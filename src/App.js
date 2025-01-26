import "./App.css";
import React, { useState } from "react";
import Camera from "./Camera";
import EmotionDisplay from './EmotionDisplay';
import SongRecommendations from './SongRecommendations';

function App() {
  const [emotion,setEmotion] = useState(null);
  const [recommendations,setRecommendations] = useState([]);

  const handleEmotionDetected = (data) => {
    setEmotion(data.emotion);
    setRecommendations(data.recommendations);
  };

  return (
    <div>
      <Camera onEmotionDetected={handleEmotionDetected} />
      <EmotionDisplay emotion={emotion} />
      <SongRecommendations recommendations={recommendations} /> 
    </div>
  );
}

export default App;
