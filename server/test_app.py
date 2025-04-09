import pytest
from flask import Flask
from app import app as flask_app, db, User, hash_password, check_password, cipher_suite, music_dist
import base64
import numpy as np
import os
import json
from unittest.mock import patch, mock_open

# Fixtures
@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with flask_app.app_context():
        db.drop_all()  # Clear existing tables
        db.create_all()  # Recreate tables for the test
    yield flask_app
    with flask_app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    """Provide a test client for the Flask app."""
    return app.test_client()

# Tests for /detect_emotion
def test_detect_emotion_success(client, mocker):
    """Test successful emotion detection with a face in the image."""
    # Mock cv2.imdecode to return a dummy frame (avoiding decode failure)
    mocker.patch('cv2.imdecode', return_value=np.zeros((480, 640, 3), dtype=np.uint8))  # Dummy RGB image
    # Mock cv2.cvtColor to return a grayscale frame
    mocker.patch('cv2.cvtColor', return_value=np.zeros((480, 640), dtype=np.uint8))  # Dummy grayscale
    # Mock OpenCV face detection with the sample coordinates
    mocker.patch('cv2.CascadeClassifier.detectMultiScale', return_value=[(263, 187, 131, 131)])
    # Mock TensorFlow model prediction for 'happy' (index 3)
    mocker.patch('tensorflow.keras.models.Model.predict', return_value=np.array([[0, 0, 0, 1, 0, 0, 0]]))

    # Same input as before
    image_data = base64.b64encode(b'some image data').decode('utf-8')
    payload = {'image': image_data}

    # Send request to the endpoint
    response = client.post('/detect_emotion', json=payload)

    # Assertions (expecting success, so status should be 200, not 400)
    assert response.status_code == 200  # Success case should return 200, not 400
    data = response.get_json()
    assert 'emotions' in data
    assert data['emotions'] == ['happy']
    assert 'emotion_indices' in data
    assert data['emotion_indices'] == [3]
    assert 'face_coordinates' in data
    assert data['face_coordinates'] == [{'x': 263, 'y': 187, 'w': 131, 'h': 131}]
    assert 'recommendations' in data
    assert data['recommendations'] == [music_dist[3]]
    
    

def test_detect_emotion_missing_image(client):
    """Test emotion detection with missing image key."""
    payload = {}
    response = client.post('/detect_emotion', json=payload)
    assert response.status_code == 500  # Current behavior due to KeyError; could be improved to 400
    data = response.get_json()
    assert 'error' in data

# Tests for /store_image
def test_store_image_success(client, mocker):
    """Test successful image storage."""
    mocker.patch('cryptography.fernet.Fernet.encrypt', return_value=b'encrypted_data')
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('os.makedirs')
    mocker.patch('builtins.open', mock_open())
    
    image_data = base64.b64encode(b'some image data').decode('utf-8')
    payload = {
        'image': image_data,
        'emotion_id': 3,
        'face_coordinates': {'x': 100, 'y': 100, 'w': 50, 'h': 50}
    }
    
    response = client.post('/store_image', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert 'filename' in data

def test_store_image_missing_keys(client):
    """Test image storage with missing keys."""
    payload = {'image': 'some_data'}
    response = client.post('/store_image', json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Missing key' in data['error']

# Tests for /get_image
def test_get_image_success(client, mocker):
    """Test retrieving an existing image."""
    mocker.patch('cryptography.fernet.Fernet.decrypt', return_value=b'decrypted_image_data')
    mocker.patch('builtins.open', mock_open(read_data=b'encrypted_data'))
    
    response = client.get('/get_image?filename=test.enc')
    assert response.status_code == 200
    assert response.data == b'decrypted_image_data'
    assert response.mimetype == 'image/jpeg'

def test_get_image_not_found(client, mocker):
    """Test retrieving a non-existent image."""
    mocker.patch('builtins.open', side_effect=FileNotFoundError)
    response = client.get('/get_image?filename=nonexistent.enc')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'Image not found'

def test_get_image_missing_filename(client):
    """Test retrieving an image without providing a filename."""
    response = client.get('/get_image')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'Filename is required'

# Tests for /list_images
def test_list_images(client, mocker):
    """Test listing images in the captured_images directory."""
    mocker.patch('os.listdir', return_value=['image1.enc', 'image2.enc', 'not_enc.txt'])
    response = client.get('/list_images')
    assert response.status_code == 200
    data = response.get_json()
    assert 'images' in data
    assert data['images'] == ['image1.enc', 'image2.enc']

# Tests for /spotify-login
def test_spotify_login_success(client, mocker):
    """Test Spotify login with a valid emotion ID."""
    mocker.patch('spotipy.oauth2.SpotifyOAuth.get_authorize_url', return_value='https://accounts.spotify.com/authorize?...')
    response = client.get('/spotify-login?emotion=3')
    assert response.status_code == 200
    data = response.get_json()
    assert 'auth_url' in data
    assert data['auth_url'].startswith('https://accounts.spotify.com/authorize')

def test_spotify_login_invalid_emotion(client):
    """Test Spotify login with an invalid emotion ID."""
    response = client.get('/spotify-login?emotion=10')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'Invalid emotion ID'

# Tests for /callback
def test_callback_success(client, mocker):
    """Test Spotify callback with valid code and state."""
    mocker.patch('spotipy.oauth2.SpotifyOAuth.get_access_token', return_value={'access_token': 'test_token'})
    
    response = client.get('/callback?code=test_code&state=3', follow_redirects=False)
    assert response.status_code == 302
    assert response.location == 'https://open.spotify.com/playlist/37i9dQZF1DXdPec7aLTmlC'

def test_callback_invalid_state(client, mocker):
    """Test Spotify callback with an invalid state."""
    # Mock get_access_token to return a valid token, bypassing Spotify API failure
    mocker.patch('spotipy.oauth2.SpotifyOAuth.get_access_token', return_value={'access_token': 'mock_token'})

    # Send request with an invalid state (10 is not in music_dist)
    response = client.get('/callback?code=test_code&state=10')

    # Assert the expected 400 status code and message
    assert response.status_code == 400
    assert response.data.decode('utf-8') == "Invalid emotion ID"

# Tests for /signup
def test_signup_success(client):
    """Test successful user signup."""
    payload = {'username': 'testuser', 'password': 'testpass'}
    response = client.post('/signup', json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert 'message' in data
    assert data['message'] == 'User created successfully'
    
    with flask_app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert check_password(user.password, 'testpass')

def test_signup_existing_user(client):
    """Test signup with an existing username."""
    with flask_app.app_context():
        hashed_password = hash_password('testpass')
        db.session.add(User(username='testuser', password=hashed_password))
        db.session.commit()
    
    payload = {'username': 'testuser', 'password': 'newpass'}
    response = client.post('/signup', json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'Username already exists'

def test_signup_missing_fields(client):
    """Test signup with missing fields."""
    payload = {'username': 'testuser'}
    response = client.post('/signup', json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'Username and password are required'

# Tests for /login
def test_login_success(client):
    """Test successful user login."""
    with flask_app.app_context():
        hashed_password = hash_password('testpass')
        db.session.add(User(username='testuser', password=hashed_password))
        db.session.commit()
    
    payload = {'username': 'testuser', 'password': 'testpass'}
    response = client.post('/login', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert data['message'] == 'Login successful'

def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    with flask_app.app_context():
        hashed_password = hash_password('testpass')
        db.session.add(User(username='testuser', password=hashed_password))
        db.session.commit()
    
    payload = {'username': 'testuser', 'password': 'wrongpass'}
    response = client.post('/login', json=payload)
    assert response.status_code == 401
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'Invalid username or password'

def test_login_missing_fields(client):
    """Test login with missing fields."""
    payload = {'username': 'testuser'}
    response = client.post('/login', json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'Username and password are required'