import "./App.css";
import React, { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import Signup from "./Signup";
import Login from "./Login";
import Camera from "./Camera";
import axios from "axios";

function App() {
  const fetchUserProfile = async () => {
    try {
      const response = await axios.get("http://localhost:8080/user_profile");
      console.log(response.data); // Log user data or handle it as needed
    } catch (error) {
      console.error("Error fetching user profile:", error);
    }
  };

  useEffect(() => {
    const handleSpotifyCallback = async () => {
      const params = new URLSearchParams(window.location.search);
      const code = params.get("code");
      const emotionId = params.get("state");

      if (code && emotionId) {
        try {
          // Fetch playlist URL after authorization
          fetchUserProfile();

          const response = await axios.get(
            "http://localhost:8080/get_playlists",
            {
              params: { emotion: emotionId },
            }
          );

          if (response.data.playlist_url) {
            // Open the playlist in a new tab
            window.open(response.data.playlist_url, "_blank");
          }
        } catch (error) {
          console.error("Error fetching playlist:", error);
        }
      }
    };

    handleSpotifyCallback();
  }, []);

  return (
    <div>
      {/* Title */}
      <h1 className="title">
        Music Recommendation System via Emotion Detection
      </h1>

      <Router>
        <Routes>
          {/* Redirect root to signup */}
          <Route path="/" element={<Navigate to="/signup" />} />

          {/* Signup page */}
          <Route path="/signup" element={<Signup />} />

          {/* Login page */}
          <Route path="/login" element={<Login />} />

          {/* Camera page */}
          <Route path="/camera" element={<Camera />} />
        </Routes>
      </Router>
    </div>
  );
}

export default App;
