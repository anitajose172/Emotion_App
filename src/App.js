import "./App.css";
import React, { useState, useEffect } from "react";
import Camera from "./Camera";
import EmotionDisplay from './EmotionDisplay';
import axios from "axios";

function App() {
  const [emotion] = useState(null);


const authenticateSpotify = async (emotionId) => {
  try {
    const response = await axios.get('http://localhost:8080/spotify-login', {
      params: { emotion: emotionId }
    });
    
    if (response.data.auth_url) {
      window.location.href = response.data.auth_url;
    }
  } catch (error) {
    console.error('Spotify auth error:', error);
  }
};

const handleEmotionDetected = async (data) => {
  if (!data?.emotions?.length) return;

  const emotionId = data.emotion_indices[0];
  authenticateSpotify(emotionId);
};


useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const playlistUrl = params.get('playlist_url');
  if (playlistUrl) {
    window.open(playlistUrl, '_blank');
    // Clean the URL
    window.history.replaceState({}, '', window.location.pathname);
  }
}, []);

  return (
    <div>
      <Camera onEmotionDetected={handleEmotionDetected} />
      <EmotionDisplay emotion={emotion} />
    </div>
  );
}



export default App;
