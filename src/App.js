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
    const response = await axios.get('/spotify-login');
    if (response.data.auth_url) {
      window.location.href = response.data.auth_url;
    }
  } catch (error) {
    console.error('Spotify auth error:', error);
  }
};

// const handleEmotionDetected = async (data) => {
//   // Add null checks for data and its properties
//   if (!data || !data.emotions || !Array.isArray(data.emotions)) {
//     console.error('Invalid emotion data structure:', data);
//     setEmotion(null);
//     setRecommendations([]);
//     return;
//   }

//   // Safely access first emotion with optional chaining
//   const primaryEmotion = data.emotions?.[0]?.name || 'neutral';
//   setEmotion(primaryEmotion);

  
//   // Handle recommendations safely
//   setRecommendations(data.recommendations || []);

//   // Handle Spotify authentication flow
//   try {
//     const spotifyStatus = await axios.get('/spotify-login');
    
//     if (!spotifyStatus?.data) {
//       throw new Error('Invalid Spotify status response');
//     }

//     if (spotifyStatus.data.status !== 'already_authenticated') {
//       await authenticateSpotify();
//     } else {
//       // Only fetch playlists when already authenticated
//       const emotionIndex = emotion_map.indexOf(primaryEmotion);
//       if (emotionIndex !== -1) {
//         const playlists = await axios.get(`/get_playlists?emotion=${emotionIndex}`);
//         window.open(playlists.data.playlist_url, '_blank');
//       }
//     }
//   } catch (error) {
//     console.error('Spotify check error:', error);
//   }
// };

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
    const spotifyStatus = await axios.get('/spotify-login');

    if (spotifyStatus.data.auth_url) {
      window.location.href = spotifyStatus.data.auth_url;
      return; // Important: Stop execution after redirect
    }

    const playlists = await axios.get(`/get_playlists?emotion=${primaryEmotionIndex}`);
    window.open(playlists.data.playlist_url, '_blank'); // Open playlist
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
