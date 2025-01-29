import React, { useRef, useState, useEffect } from "react";
import Webcam from "react-webcam";
import axios from "axios";

const Camera = ({ onEmotionDetected }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);


  const [isCapturing, setIsCapturing] = useState(false);
  const [captureError, setCaptureError] = useState(null);
  const [emotions, setEmotions] = useState([]);
  const [isContinuous, setIsContinuous] = useState(false);

  const drawBoundingBoxes = (faces) => {
    const canvas = canvasRef.current;
    const video = videoRef.current.video;
    if (!canvas || !video) return;

    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Match canvas size to video feed
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
      ctx.fillText(emotions[index], x + 5, y - 5);
    });
  };



  const handleCapture = async () => {
    setIsCapturing(true);
    setCaptureError(null);

    try {
      const imageSrc = videoRef.current.getScreenshot();

      if (!imageSrc) {
        setCaptureError("Unable to capture image.");
        setIsCapturing(false);
        return;
      }

      // Extract only the Base64 part of the image string
      const base64Image = imageSrc.split(",")[1];

      // Send the Base64 image to the Flask backend
      const response = await axios.post("http://127.0.0.1:5000/detect_emotion", {
        image: base64Image,
      });

      if (response.data && response.data.emotions) {
        const { emotions, face_coordinates } = response.data; // Assuming backend sends an "emotions" array
        setEmotions(emotions);
        drawBoundingBoxes(face_coordinates); // Draw boxes after response
        onEmotionDetected(response.data);
      } else {
        setCaptureError("No emotions detected.");
      }
    } catch (error) {
      setCaptureError("Error capturing image or processing with API.");
      console.error("Camera capture error:", error);
    } finally {
      setIsCapturing(false);
    }
  };

  useEffect(() => {
    let interval;
    if (isContinuous && !isCapturing) {
      interval = setInterval(() => {
        handleCapture();
      }, 3000); // Capture every 3 seconds
    }
    return () => clearInterval(interval);
  }, [isContinuous, isCapturing]);

  return (
    <div className="camera-container">
      <div style={{ position: 'relative' }}>
        <Webcam
          audio={false}
          height={480}
          ref={videoRef}
          screenshotFormat="image/jpeg"
          className="webcam-view"
        />
        <canvas
          ref={canvasRef}
          style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
      />
      
      </div>
      <div className="controls">
        <button disabled={isCapturing} onClick={handleCapture}>
          {isCapturing ? "Detecting Emotion..." : "Capture Emotion"}
        </button>
        <button onClick={() => setIsContinuous(!isContinuous)}>
          {isContinuous ? "Stop Continuous Detection" : "Start Continuous Detection"}
        </button>
      </div>
      {captureError && <p className="error-message">{captureError}</p>}
      <div className="emotions-list">
        {emotions.length > 0 && <h3>Detected Emotions:</h3>}
        <ul>
          {emotions.map((emotion, index) => (
            <li key={index}>Emotion {index + 1}: {emotion}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default Camera;