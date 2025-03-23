import "./App.css";
import React, { useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Signup from "./Signup";
import Login from "./Login";
import Camera from "./Camera";
import Images from "./Images"; // Import the new component
import axios from "axios";

function App() {
  const fetchUserProfile = async () => {
    try {
      const response = await axios.get("http://localhost:8080/user_profile", { withCredentials: true });
      console.log(response.data);
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
          fetchUserProfile();
          const response = await axios.get("http://localhost:8080/get_playlists", {
            params: { emotion: emotionId },
            withCredentials: true,
          });
          if (response.data.playlist_url) {
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
      <h1 className="title">Music Recommendation System via Emotion Detection</h1>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/signup" />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/login" element={<Login />} />
          <Route path="/camera" element={<Camera />} />
          <Route path="/images" element={<Images />} /> {/* New route */}
        </Routes>
      </Router>
    </div>
  );
}

export default App;