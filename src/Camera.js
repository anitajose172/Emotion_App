import React, { useRef, useState, useEffect } from "react";
import Webcam from "react-webcam";
import axios from "axios";
import EmotionDisplay from "./EmotionDisplay";

const Camera = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const [captureError, setCaptureError] = useState(null);
  const [primary_emotion, setPrimaryEmotion] = useState(null);
  const [emotions, setEmotions] = useState([]);
  const [isWebcamReady, setIsWebcamReady] = useState(false);
  const [lastDetectedEmotionId, setLastDetectedEmotionId] = useState(null);

  const drawBoundingBoxes = (faces, emotions) => {
    const canvas = canvasRef.current;
    const video = videoRef.current?.video;
    if (!canvas || !video) return;

    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    faces.forEach((face, index) => {
      const { x, y, w, h } = face;
      ctx.strokeStyle = "#FF0000";
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, w, h);

      const emotionText = emotions[index] || "No emotion detected";
      ctx.fillStyle = "#FF0000";
      ctx.font = "16px Arial";
      ctx.fillText(emotionText, x + 5, y - 10); // Place text slightly above the bounding box
    });
  };

  const detectEmotion = async () => {
    if (!isWebcamReady) return;

    try {
      const imageSrc = videoRef.current?.getScreenshot();

      if (!imageSrc) {
        setCaptureError("Unable to capture image.");
        return;
      }

      const base64Image = imageSrc.split(",")[1];
      const response = await axios.post("http://127.0.0.1:8080/detect_emotion", {
        image: base64Image,
      });

      if (response.data && response.data.emotions) {
        const { emotions, face_coordinates, emotion_indices } = response.data;
        setEmotions(emotions);
        drawBoundingBoxes(face_coordinates, emotions);
        setLastDetectedEmotionId(emotion_indices[0]); // Save the first detected emotion's ID
        handleEmotionDetected(response.data);
      } else {
        setCaptureError("No emotions detected.");
      }
    } catch (error) {
      setCaptureError("Error capturing image or processing with API.");
      // console.error("Emotion detection error:", error);
    }
  };

  const redirectToSpotify = async () => {
    if (!lastDetectedEmotionId) {
      setCaptureError("No emotion detected to redirect.");
      return;
    }
  
    try {
      // Set a 10-second delay before redirecting
      // setCaptureError("Redirecting in 10 seconds...");
  
      // setTimeout(async () => {
        try {
          const response = await axios.get("http://localhost:8080/spotify-login", {
            params: { emotion: lastDetectedEmotionId },
          });
  
          if (response.data.auth_url) {
            window.location.href = response.data.auth_url; // Redirect to Spotify
          }
        } catch (error) {
          console.error("Spotify auth error:", error);
        }
      // }, 0); // 10 seconds delay (10,000 milliseconds)
  
    } catch (error) {
      console.error("Error in redirect:", error);
    }
  };

    const authenticateSpotify = async (emotionId) => {
      try {
        const response = await axios.get('http://localhost:8080/spotify-login', {
          params: { emotion: emotionId },
        });
        
        if (response.data.auth_url) {
          // window.location.href = response.data.auth_url; // Redirect to Spotify auth
        }
      } catch (error) {
        console.error('Spotify auth error:', error);
      }
    };

    /**
   * Act on emotion detection
   * 
   * NOTE: Since you are getting a array of emotions, create a new array of these arrays.
   * Basically a 2 dimensional array, 
   * e.g. emotion_matrix = [
   *    [...emotions_at_first_attempt],
   *    [...emotions_at_second_attempt],
   *    [...emotions_at_third_attempt],
   *    [...emotions_at_fourth_attempt],
   *    ...
   * ]
   * 
   * Now from this matrix derive the most prominent/primary emotion (could be based on frequency or come up with a better calculation)
   * @param {string[]} data 
   * @returns 
   */
    const handleEmotionDetected = async (data) => {
      if (!data?.emotions?.length) return;
  
      const primaryEmotionIndex = data.emotion_indices[0];
  
      // Save the detected emotion for display
      setPrimaryEmotion(data.emotions[0]);
  
      try {
        // Redirect to Spotify for authorization
        authenticateSpotify(primaryEmotionIndex);
      } catch (error) {
        console.error('Error during Spotify flow:', error);
      }
    };
  
  

  useEffect(() => {
    // Continuously detect emotions every 1 second
    const interval = setInterval(() => {
      if (isWebcamReady) detectEmotion();
    }, 1000);

    return () => clearInterval(interval);
  }, [isWebcamReady]);

  return (
    <React.Fragment>
          <div className="camera-container">
      <div style={{ position: "relative" }}>
        <Webcam
          audio={false}
          height={480}
          ref={videoRef}
          screenshotFormat="image/jpeg"
          className="webcam-view"
          onUserMedia={() => setIsWebcamReady(true)}
        />
        <canvas
          ref={canvasRef}
          style={{ position: "absolute", top: 0, left: 0, pointerEvents: "none" }}
        />
      </div>
      <div className="controls">
        <button onClick={redirectToSpotify}>Redirect to Spotify</button>
      </div>
      {captureError && <p className="error-message">{captureError}</p>}
      
    </div>
         {/* Emotion Display (global) */}
        <EmotionDisplay emotion={primary_emotion} />
    </React.Fragment>

  );
};

export default Camera;
