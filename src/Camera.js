import React, { useRef, useState, useEffect } from "react";
import Webcam from "react-webcam";
import axios from "axios";

const Camera = ({ onEmotionDetected }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const [emotions, setEmotions] = useState([]);
  const [setFaceCoordinates] = useState([]);
  const [isCapturing, setIsCapturing] = useState(false);
  const [isDetected, setIsDetected] = useState(false);

  // Function to draw bounding boxes
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

      // Draw emotion label
      ctx.fillStyle = "#FF0000";
      ctx.font = "16px Arial";
      ctx.fillText(emotions[index] || "Unknown", x + 5, y - 5);
    });
  };

  // Function to detect emotions in real time
  const detectEmotionLive = async () => {
    if (!videoRef.current) return;

    const imageSrc = videoRef.current.getScreenshot();
    if (!imageSrc) return;

    try {
      const base64Image = imageSrc.split(",")[1];

      const response = await axios.post("http://127.0.0.1:8080/detect_emotion", {
        image: base64Image,
      });

      if (response.data && response.data.emotions) {
        setEmotions(response.data.emotions);
        setFaceCoordinates(response.data.face_coordinates);
        drawBoundingBoxes(response.data.face_coordinates, response.data.emotions);
      }
    } catch (error) {
      console.error("Error detecting emotion:", error);
    }
  };

  // Function to capture emotion and redirect to Spotify after 30s
  const handleCapture = async () => {
    setIsCapturing(true);
    setIsDetected(false);

    const imageSrc = videoRef.current.getScreenshot();
    if (!imageSrc) {
      setIsCapturing(false);
      return;
    }

    try {
      const base64Image = imageSrc.split(",")[1];

      const response = await axios.post("http://127.0.0.1:8080/detect_emotion", {
        image: base64Image,
      });

      if (response.data && response.data.emotions) {
        setEmotions(response.data.emotions);
        setFaceCoordinates(response.data.face_coordinates);
        drawBoundingBoxes(response.data.face_coordinates, response.data.emotions);
        setIsDetected(true);

        // Wait 30 seconds before redirecting to Spotify
        setTimeout(() => {
          window.location.href = "https://open.spotify.com/";
        }, 5000);
      }
    } catch (error) {
      console.error("Error detecting emotion:", error);
    } finally {
      setIsCapturing(false);
    }
  };

  // Run real-time emotion detection every 3 seconds
  useEffect(() => {
    const interval = setInterval(detectEmotionLive, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="camera-container">
      <div style={{ position: "relative" }}>
        <Webcam
          audio={false}
          height={480}
          ref={videoRef}
          screenshotFormat="image/jpeg"
          className="webcam-view"
        />
        <canvas
          ref={canvasRef}
          style={{ position: "absolute", top: 0, left: 0, pointerEvents: "none" }}
        />
      </div>
      <div className="controls">
        <button disabled={isCapturing} onClick={handleCapture}>
          {isCapturing ? "Capturing..." : "Capture Emotion"}
        </button>
      </div>
      {isDetected && <p>Emotion detected! Redirecting in 5 seconds...</p>}
      <div className="emotions-list">
        {emotions.length > 0 && <h3>Detected Emotions:</h3>}
        <ul>
          {emotions.map((emotion, index) => (
            <li key={index}>
              Emotion {index + 1}: {emotion}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default Camera;
