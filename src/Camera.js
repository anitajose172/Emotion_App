// import React, { useRef, useState, useEffect } from "react";
// import Webcam from "react-webcam";
// import axios from "axios";

// const Camera = ({ onEmotionDetected }) => {
//   const videoRef = useRef(null);
//   const [isCapturing, setIsCapturing] = useState(false);
//   const [captureError, setCaptureError] = useState(null);

//   const handleCapture = async () => {
//     setIsCapturing(true);
//     setCaptureError(null);

//     try {
//       const imageSrc = videoRef.current.getScreenshot();
//       const response = await axios.post('/detect_emotion', { image: imageSrc });

//       if (response.data) {
//         const { emotion, recommendations } = response.data;
//         onEmotionDetected({ emotion, recommendations }); // Pass data to parent
//       } else {
//         setCaptureError("No emotion detected or unexpected response from API");
//       }
//     } catch (error) {
//       setCaptureError("Error capturing image or processing with API");
//       console.error("Camera capture error:", error);
//     } finally {
//       setIsCapturing(false);
//     }
//   };

//   return (
//     <div className="camera-container">
//       <Webcam
//         audio={false}
//         height={480}
//         ref={videoRef}
//         screenshotFormat="image/jpeg"
//       />
//       <button disabled={isCapturing} onClick={handleCapture}>
//         {isCapturing ? "Capturing..." : "Capture Emotion"}
//       </button>
//       {captureError && <p className="error-message">{captureError}</p>}
//     </div>
//   );
// };

// export default Camera;

import React, { useRef, useState } from "react";
import Webcam from "react-webcam";
import axios from "axios";

const Camera = ({ onEmotionDetected }) => {
  const videoRef = useRef(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [captureError, setCaptureError] = useState(null);

  const handleCapture = async () => {
    setIsCapturing(true);
    setCaptureError(null);

    try {
      // Capture the image as a base64 string
      const imageSrc = videoRef.current.getScreenshot();

      // Send the image to the Flask backend
      const response = await axios.post("http://127.0.0.1:5000/detect_emotion", {
        image: imageSrc,
      });

      if (response.data) {
        const { emotion, recommendations } = response.data;
        onEmotionDetected({ emotion, recommendations });
      } else {
        setCaptureError("No emotion detected or unexpected response from API");
      }
    } catch (error) {
      setCaptureError("Error capturing image or processing with API");
      console.error("Camera capture error:", error);
    } finally {
      setIsCapturing(false);
    }
  };

  return (
    <div className="camera-container">
      <Webcam
        audio={false}
        height={480}
        ref={videoRef}
        screenshotFormat="image/jpeg"
      />
      <button disabled={isCapturing} onClick={handleCapture}>
        {isCapturing ? "Capturing..." : "Capture Emotion"}
      </button>
      {captureError && <p className="error-message">{captureError}</p>}
    </div>
  );
};

export default Camera;
