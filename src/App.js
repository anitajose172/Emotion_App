import "./App.css";
import React, { useState, useEffect } from "react";
import Camera from "./Camera";
import EmotionDisplay from './EmotionDisplay';
import SongRecommendations from './SongRecommendations';
import axios from "axios";

function App() {
  const [emotion] = useState(null);
  const [recommendations] = useState([]);


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
  const primaryEmotionIndex = data.emotion_indices[0];
  
  try {
    // First check if we have recommendations
    if (data.recommendations?.length) {
      const playlistUri = data.recommendations[0];
      const playlistId = playlistUri.split(':')[2];
      
      // Directly try to open Spotify
      window.open(`https://open.spotify.com/playlist/${playlistId}`, '_blank');
      
      // Check if authentication is needed
      setTimeout(() => {
        if (document.hidden) return; // If tab switched, assume success
        authenticateSpotify(primaryEmotionIndex);
      }, 1000);
    }
  } catch (error) {
    console.error('Playlist open error:', error);
    authenticateSpotify(primaryEmotionIndex);
  }
};

useEffect(() => {
  const handleSpotifyCallback = async () => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const error = params.get('error');

    if (code) {
      try {
        // Get the emotion ID from the state parameter
        const emotionId = params.get('state');
        
        // Exchange code for playlist URL
        const response = await axios.get('http://localhost:8080/get_playlists', {
          params: { emotion: emotionId }
        });

        if (response.data.playlist_url) {
          window.open(response.data.playlist_url, '_blank');
        }
      } catch (error) {
        console.error('Callback handling error:', error);
      }
    }
  };

  handleSpotifyCallback();
}, []);

  return (
    <div>
      <Camera onEmotionDetected={handleEmotionDetected} />
      <EmotionDisplay emotion={emotion} />
      <SongRecommendations recommendations={recommendations} /> 
    </div>
  );
}



export default App;
