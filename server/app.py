from flask import Flask, request, jsonify, session, redirect, url_for, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from tensorflow.keras.models import load_model
import bcrypt
import cv2
import numpy as np
import base64
import logging
import webbrowser
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
import os
from datetime import datetime
from cryptography.fernet import Fernet
import json

app = Flask(__name__)

CORS(app, resources={r"/*": {
    "origins": "http://localhost:3000",
    "methods": ["GET", "POST"],
    "allow_headers": ["Content-Type", "Authorization"]
}}, supports_credentials=True)
app.secret_key = os.urandom(64)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Generate a key for encryption (store this securely)
key = Fernet.generate_key()
cipher_suite = Fernet(key)

class CapturedImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    emotion_id = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    image_filename = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<CapturedImage {self.image_filename}>'


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




# @app.route('/detect_emotion', methods=['POST'])
# def detect_emotion():
#     try:
#         # Get frame data (Base64 encoded image)
#         data = request.json
#         image_data = base64.b64decode(data['image'])
#         frame = np.frombuffer(image_data, dtype=np.uint8)
#         frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

#         if frame is None:
#             logging.error("Failed to decode image.")
#             return jsonify({'error': 'Failed to decode image.'}), 400

#         # Convert to grayscale for Haar Cascade
#         gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         faces = face_classifier.detectMultiScale(gray_frame, scaleFactor=1.3, minNeighbors=5)

#         emotions = []
#         emotion_indices = [] 
#         face_coordinates = [] 
#         for (x, y, w, h) in faces:
#             # Extract the face ROI
#             roi_gray = gray_frame[y:y+h, x:x+w]
#             roi_gray = cv2.resize(roi_gray, (48, 48))
#             roi_gray = roi_gray.astype('float') / 255.0
#             roi_gray = np.expand_dims(roi_gray, axis=0)
#             roi_gray = np.expand_dims(roi_gray, axis=-1)
            
#             face_coordinates.append({
#                 'x': int(x),
#                 'y': int(y),
#                 'w': int(w),
#                 'h': int(h)
#             })

#             # Predict emotion
#             prediction = model.predict(roi_gray)
#             emotion_index = int(np.argmax(prediction)) 
#             emotion_indices.append(emotion_index) 
#             emotions.append(emotion_map[emotion_index]) 
#         if not emotions:
#             logging.warning("No faces detected.")
#             return jsonify({'emotions': [], 'warning': 'No faces detected.'})

#         return jsonify({
#         'emotions': emotions,
#         'emotion_indices': emotion_indices,  
#         'face_coordinates': face_coordinates,
#         'recommendations': [
#     music_dist[index]  # Return Spotify URI directly
#     for index in emotion_indices
# ]
        
#     })
    
#     except Exception as e:
#         logging.error(f"Error in detect_emotion: {str(e)}")
#         return jsonify({'error': str(e)}), 500
    
    
@app.route('/detect_emotion', methods=['POST'])
def detect_emotion():
    try:
        # Get frame data (Base64 encoded image)
        data = request.json
        try:
            image_data = base64.b64decode(data['image'])
        except (base64.binascii.Error, KeyError):
            logging.error("Invalid base64 image data.")
            return jsonify({'error': 'Invalid image data.'}), 400

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
            emotion_index = int(np.argmax(prediction))
            emotion_indices.append(emotion_index)
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
    
@app.route('/spotify-login', methods=['GET'])
def spotify_login():
    emotion_id = request.args.get('emotion', type=int)
    if emotion_id not in music_dist:
        return jsonify({"error": "Invalid emotion ID"}), 400
    
    # Only generate auth URL when requested by the button click
    auth_url = sp_oauth.get_authorize_url(state=str(emotion_id))
    return jsonify({'auth_url': auth_url})  # Send URL to frontend

    
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


@app.route("/user_profile")
def user_profile():
    try:
        if not sp_oauth.validate_token(cache_handler.get_cached_token()):
            auth_url = sp_oauth.get_authorize_url()
            return redirect(auth_url)

        user_info = sp.current_user()
        return jsonify(user_info)

    except Exception as e:
        logging.error(f"Error fetching user profile: {str(e)}")
        return jsonify({"error": "Failed to fetch user profile"}), 500




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

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Create database tables
with app.app_context():
    db.create_all()

# Helper function to hash passwords
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Helper function to check passwords
def check_password(hashed_password, user_password):
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)

# Signup route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    hashed_password = hash_password(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password(user.password, password):
        return jsonify({"error": "Invalid username or password"}), 401

    return jsonify({"message": "Login successful"}), 200


@app.route('/get_metadata', methods=['GET'])
def get_metadata():
    try:
        image_filename = request.args.get('filename')
        if not image_filename:
            return jsonify({"error": "Filename is required"}), 400

        # Construct the full path to the metadata file
        metadata_filename = f'captured_images/{image_filename}.json'

        # Check if the file exists
        if not os.path.exists(metadata_filename):
            return jsonify({"error": "Metadata file not found"}), 404

        # Read the metadata file
        with open(metadata_filename, 'r') as f:
            metadata = json.load(f)

        return jsonify(metadata), 200

    except FileNotFoundError:
        logging.error(f"Metadata file not found: {metadata_filename}")
        return jsonify({"error": "Metadata not found"}), 404
    except Exception as e:
        logging.error(f"Error retrieving metadata: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/store_image', methods=['POST'])
def store_image():
    try:
        data = request.json

        # Check for required keys in the payload
        required_keys = ['image', 'emotion_id', 'face_coordinates']
        for key in required_keys:
            if key not in data:
                return jsonify({"error": f"Missing key in request payload: {key}"}), 400

        image_data = data['image']
        emotion_id = data['emotion_id']
        face_coordinates = data['face_coordinates']

        # Decode the base64 image data
        image_bytes = base64.b64decode(image_data)

        # Encrypt the image data
        encrypted_image = cipher_suite.encrypt(image_bytes)

        # Create a directory to store images if it doesn't exist
        if not os.path.exists('captured_images'):
            os.makedirs('captured_images')

        # Save the encrypted image with a timestamp and emotion ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_filename = f'{timestamp}_emotion_{emotion_id}.enc'
        with open(f'captured_images/{image_filename}', 'wb') as f:
            f.write(encrypted_image)

        # Save metadata (bounding box and emotion)
        metadata = {
            "filename": image_filename,
            "emotion": emotion_map[emotion_id],
            "face_coordinates": face_coordinates,
        }
        metadata_filename = f'captured_images/{image_filename}.json'
        with open(metadata_filename, 'w') as f:
            json.dump(metadata, f)

        # Return the filename to the frontend
        return jsonify({
            "message": "Image stored successfully",
            "filename": image_filename
        }), 200

    except Exception as e:
        logging.error(f"Error storing image: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    
@app.route('/get_image', methods=['GET'])
def get_image():
    try:
        image_filename = request.args.get('filename')
        if not image_filename:
            return jsonify({"error": "Filename is required"}), 400

        # Read the encrypted image file
        with open(f'captured_images/{image_filename}', 'rb') as f:
            encrypted_image = f.read()

        # Decrypt the image data
        decrypted_image = cipher_suite.decrypt(encrypted_image)

        # Return the decrypted image as a response
        return Response(decrypted_image, mimetype='image/jpeg')

    except FileNotFoundError:
        logging.error(f"Image file not found: {image_filename}")
        return jsonify({"error": "Image not found"}), 404
    except Exception as e:
        logging.error(f"Error retrieving image: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/list_images', methods=['GET'])
def list_images():
    try:
        # List all files in the captured_images directory
        image_files = os.listdir('captured_images')
        return jsonify({"images": image_files}), 200
    except Exception as e:
        logging.error(f"Error listing images: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
