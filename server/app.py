from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from tensorflow.keras.models import load_model
import cv2
import numpy as np
import base64
import logging
import webbrowser
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
import os

app = Flask(__name__)

CORS(app, resources={r"/*": {
    "origins": "http://localhost:3000",
    "methods": ["GET", "POST"],
    "allow_headers": ["Content-Type", "Authorization"]
}}, supports_credentials=True)
app.secret_key = os.urandom(64)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Load Haar Cascade
face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
if face_classifier.empty():
    logging.error("Failed to load Haar Cascade classifier.")

# Load the model
model = load_model("model.h5") 
logging.info("Model loaded successfully.")

# Emotion mapping

emotion_map = ['angry', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
emotion_dict = {
    0: "angry", 
    1: "disgust", 
    2: "fear", 
    3: "happy", 
    4: "neutral", 
    5: "sad", 
    6: "surprise"
}
client_id=''
client_secret=''
redirect_uri='http://localhost:8080/callback'
scope='playlist-read-private,streaming,user-read-private,playlist-read-collaborative,playlist-modify-private'

cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope='playlist-read-private,streaming,user-read-private,playlist-read-collaborative,playlist-modify-private',
    cache_handler=cache_handler,
    show_dialog=True
)

sp=Spotify(oauth_manager=sp_oauth)

# Emotion and Playlist mapping
emotion_dict = {0: "Angry", 1: "Disgusted", 2: "Fearful", 3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprised"}


music_dist = {
    0: "spotify:playlist:37i9dQZF1DX1uHCeQukD5j",  # Angry
    1: "spotify:playlist:37i9dQZF1DX3YSRoSdA634",  # Disgusted
    2: "spotify:playlist:37i9dQZF1DX6xOPeSOGone",  # Fearful
    3: "spotify:playlist:37i9dQZF1DXdPec7aLTmlC",  # Happy
    4: "spotify:playlist:37i9dQZF1DX4sWSpwq3LiO",  # Neutral
    5: "spotify:playlist:37i9dQZF1DX7qK8ma5wgG1",  # Sad
    6: "spotify:playlist:37i9dQZF1DX8FwnYE6PRvL"   # Surprised
}




@app.route('/detect_emotion', methods=['POST'])
def detect_emotion():
    try:
        # Get frame data (Base64 encoded image)
        data = request.json
        image_data = base64.b64decode(data['image'])
        frame = np.frombuffer(image_data, dtype=np.uint8)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        if frame is None:
            logging.error("Failed to decode image.")
            return jsonify({'error': 'Failed to decode image.'}), 400

        # Convert to grayscale for Haar Cascade
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_classifier.detectMultiScale(gray_frame, scaleFactor=1.3, minNeighbors=5)

        emotions = []
        emotion_indices = [] 
        face_coordinates = [] 
        for (x, y, w, h) in faces:
            # Extract the face ROI
            roi_gray = gray_frame[y:y+h, x:x+w]
            roi_gray = cv2.resize(roi_gray, (48, 48))
            roi_gray = roi_gray.astype('float') / 255.0
            roi_gray = np.expand_dims(roi_gray, axis=0)
            roi_gray = np.expand_dims(roi_gray, axis=-1)
            
            face_coordinates.append({
                'x': int(x),
                'y': int(y),
                'w': int(w),
                'h': int(h)
            })

            # Predict emotion
            prediction = model.predict(roi_gray)
            emotion_index = int(np.argmax(prediction))  # Convert here
            emotion_indices.append(emotion_index)  # Store index
            emotions.append(emotion_map[emotion_index]) 
        if not emotions:
            logging.warning("No faces detected.")
            return jsonify({'emotions': [], 'warning': 'No faces detected.'})

        return jsonify({
        'emotions': emotions,
        'emotion_indices': emotion_indices,  
        'face_coordinates': face_coordinates,
        'recommendations': [
    music_dist[index]  # Return Spotify URI directly
    for index in emotion_indices
]
        
    })
    
    except Exception as e:
        logging.error(f"Error in detect_emotion: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/spotify-login')
def spotify_login():
    emotion_id = request.args.get('emotion', type=int)
    if emotion_id not in music_dist:
        return jsonify({"error": "Invalid emotion ID"}), 400
        
    auth_url = sp_oauth.get_authorize_url(state=str(emotion_id))
    return jsonify({'auth_url': auth_url})
    
@app.route("/callback")
def callback():
    try:
        # Exchange code for an access token
        sp_oauth.get_access_token(request.args["code"])
        
        # Get emotion ID from the 'state' parameter passed during Spotify login
        emotion_id = request.args.get("state", type=int)
        if emotion_id not in music_dist:
            return "Invalid emotion ID", 400

        # Redirect to the Spotify playlist URL
        playlist_uri = music_dist[emotion_id]
        playlist_id = playlist_uri.split(':')[-1]
        playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
        return redirect(playlist_url)

    except Exception as e:
        logging.error(f"Error in callback: {str(e)}")
        return "Authorization failed. Please try again.", 500


@app.route("/get_playlists")
def get_playlists():
    try:
        # Validate the Spotify token
        if not sp_oauth.validate_token(cache_handler.get_cached_token()):
            auth_url = sp_oauth.get_authorize_url()
            return redirect(auth_url)

        # Get emotion ID from query parameters
        emotion_id = int(request.args.get("emotion"))
        if emotion_id not in music_dist:
            return "Invalid emotion ID", 400

        # Generate the Spotify playlist URL
        playlist_uri = music_dist[emotion_id]
        playlist_id = playlist_uri.split(':')[-1]
        playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"

        # Redirect to the playlist URL
        return redirect(playlist_url)

    except Exception as e:
        logging.error(f"Error in get_playlists: {str(e)}")
        return "Failed to fetch playlist. Please try again.", 500


# @app.route("/get_playlists")
# def get_playlists():
#     if not sp_oauth.validate_token(cache_handler.get_cached_token()):
#         auth_url = sp_oauth.get_authorize_url()
#         return redirect(auth_url)

#     try:
#         emotion_id = int(request.args.get("emotion"))
#     except (TypeError, ValueError):
#         return jsonify({"error": "Missing or invalid emotion parameter"}), 400

#     if emotion_id not in music_dist:
#         return jsonify({"error": "Invalid emotion ID"}), 400

#     playlist_uri = music_dist[emotion_id]
#     playlist_id = playlist_uri.split(':')[-1]
#     return jsonify({
#         "playlist_url": f"https://open.spotify.com/playlist/{playlist_id}",
#         "playlist_uri": playlist_uri
#     })

# @app.route('/callback')
# def callback():
#     emotion_id = request.args.get('state')  # Get emotion ID from state
#     sp_oauth.get_access_token(request.args["code"])
#     return redirect(url_for('get_playlists', emotion=emotion_id))



@app.route("/")
def home():
    # Redirect to Spotify authentication if token is not valid
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for("get_playlists"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True, port=8080)
