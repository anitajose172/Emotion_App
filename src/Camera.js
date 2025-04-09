import React, { useRef, useState, useEffect } from "react";
import Webcam from "react-webcam";
import axios from "axios";
import EmotionDisplay from "./EmotionDisplay";

const Camera = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [captureError, setCaptureError] = useState(null);
  const [primaryEmotion, setPrimaryEmotion] = useState(null);
  const [emotions, setEmotions] = useState([]);
  const [isWebcamReady, setIsWebcamReady] = useState(false);
  const [lastDetectedEmotionId, setLastDetectedEmotionId] = useState(null);
  const [faceCoordinates, setFaceCoordinates] = useState([]);

  // #### Draw Bounding Boxes
  const drawBoundingBoxes = (faces, emotions) => {
    const canvas = canvasRef.current;
    const video = videoRef.current?.video;
    if (!canvas || !video) return;

    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    // ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    faces.forEach((face, index) => {
      const { x, y, w, h } = face;
      ctx.strokeStyle = "#FF0000";
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, w, h);

      const emotionText = emotions[index] || "No emotion detected";
      ctx.fillStyle = "#FF0000";
      ctx.font = "16px Arial";
      ctx.fillText(emotionText, x + 5, y - 10);
    });
  };

  // #### Detect Emotions in Real-Time
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
      }, { withCredentials: true });

      if (response.data && response.data.emotions) {
        const { emotions, face_coordinates, emotion_indices } = response.data;
        setEmotions(emotions);
        setFaceCoordinates(face_coordinates);
        setLastDetectedEmotionId(emotion_indices[0]);
        setPrimaryEmotion(emotions[0]);
        drawBoundingBoxes(face_coordinates, emotions);
      } else {
        setCaptureError("No emotions detected.");
      }
    } catch (error) {
      setCaptureError("Error capturing image or processing with API.");
      console.error("Emotion detection error:", error);
    }
  };

  // #### Set Up Continuous Detection
  useEffect(() => {
    const interval = setInterval(() => {
      if (isWebcamReady) detectEmotion();
    }, 1000); // Detect every second
    return () => clearInterval(interval); // Cleanup on unmount
  }, [isWebcamReady]);

  // #### Capture and Redirect on Button Click
  const redirectToSpotify = async () => {
    if (!lastDetectedEmotionId) {
      setCaptureError("No emotion detected to redirect.");
      return;
    }

    try {
      const canvas = canvasRef.current;
      const annotatedImage = canvas.toDataURL("image/jpeg").split(",")[1];

      const storeResponse = await axios.post("http://localhost:8080/store_image", {
        image: annotatedImage,
        emotion_id: lastDetectedEmotionId,
        face_coordinates: faceCoordinates,
      }, {
        headers: { "Content-Type": "application/json" },
        withCredentials: true,
      });

      if (storeResponse.data.filename) {
        console.log("Image stored:", storeResponse.data.filename);
      }

      const response = await axios.get("http://localhost:8080/spotify-login", {
        params: { emotion: lastDetectedEmotionId },
      }, { withCredentials: true });

      if (response.data.auth_url) {
        window.location.href = response.data.auth_url;
      }
    } catch (error) {
      console.error("Error in redirect:", error);
      setCaptureError("Error storing image or redirecting to Spotify.");
    }
  };



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
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              pointerEvents: "none",
            }}
          />
        </div>
        <div className="controls">
          <button onClick={redirectToSpotify}>Redirect to Spotify</button>
        </div>
        {captureError && <p className="error-message">{captureError}</p>}
      </div>
      <EmotionDisplay emotion={primaryEmotion} />
    </React.Fragment>
  );
};

export default Camera;