import "./App.css";
import React, { useState } from "react";
import Camera from "./Camera";
import EmotionDisplay from './EmotionDisplay';
import SongRecommendations from './SongRecommendations';
import axios from "axios";

function App() {
  const [emotion,setEmotion] = useState(null);
  const [recommendations,setRecommendations] = useState([]);

  const emotion_map = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise'];

// Add Spotify authentication flow
const authenticateSpotify = async () => {
  try {
    // Point to Flask backend endpoint
    const response = await axios.get('http://localhost:5000/spotify-login');
    window.location.href = response.data.auth_url;
  } catch (error) {
    console.error('Spotify auth error:', error);
  }
};


const handleEmotionDetected = async (data) => {
  if (!data?.emotions?.length) {
    console.error('Invalid emotion data');
    setEmotion(null);
    setRecommendations([]);
    return;
  }

  const primaryEmotionIndex = data.emotion_indices[0]; // Use index from backend
  setEmotion(data.emotions[0]);
  setRecommendations(data.recommendations);

  try {
    const authCheck = await axios.get('http://localhost:5000/spotify-login');

    if (authCheck.data.auth_url) {
      window.location.href = authCheck.data.auth_url;
      return;
    }

    // Get the Spotify URI (e.g., "spotify:playlist:...")
    const spotifyUri = data.recommendations[0];

    // Open Spotify app using the URI
    window.location.href = spotifyUri;  // Direct deep link

    // Fallback to web player if app isn't installed
    setTimeout(() => {
      const playlistId = spotifyUri.split(':')[2];
      window.open(`https://open.spotify.com/playlist/${playlistId}`, '_blank');
    }, 500);

  } catch (error) {
    console.error('Spotify error:', error);
  }
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
