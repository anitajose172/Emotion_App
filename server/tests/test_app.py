import pytest
import base64
import json
import os
from datetime import datetime
from flask import Flask, jsonify, session
import numpy as np
import cv2
from unittest.mock import patch
import sys


# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import the app module
from app import app, db, User, CapturedImage, hash_password, check_password, cipher_suite

# Set up the Flask test client
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.session.remove()
            db.drop_all()

# Helper function to create a test user
def create_test_user(username="testuser", password="testpass"):
    hashed_password = hash_password(password)
    user = User(username=username, password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return user

# Helper function to encode an image as base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Test cases
def test_signup(client):
    # Test successful signup
    response = client.post('/signup', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 201
    assert json.loads(response.data) == {"message": "User created successfully"}

    # Test missing username or password
    response = client.post('/signup', json={'username': 'testuser'})
    assert response.status_code == 400
    assert json.loads(response.data) == {"error": "Username and password are required"}

    # Test duplicate username
    response = client.post('/signup', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 400
    assert json.loads(response.data) == {"error": "Username already exists"}

def test_login(client):
    with app.app_context():  # Add application context
        create_test_user()

    # Test successful login
    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 200
    assert json.loads(response.data) == {"message": "Login successful"}

    # Test invalid credentials
    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'wrongpass'
    })
    assert response.status_code == 401
    assert json.loads(response.data) == {"error": "Invalid username or password"}

def test_detect_emotion(client):
    # Mock an image for testing
    image_path = "tests/test_image.jpg"  # Replace with a real image path
    encoded_image = encode_image_to_base64(image_path)

    # Test successful emotion detection
    response = client.post('/detect_emotion', json={'image': encoded_image})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'emotions' in data
    assert 'face_coordinates' in data
    assert 'recommendations' in data

    # Test invalid image data
    response = client.post('/detect_emotion', json={'image': 'invalid'})
    assert response.status_code == 400  # Expect 400 for invalid image data
    assert json.loads(response.data) == {"error": "Invalid image data."}

def test_spotify_login(client):
    # Test Spotify login URL generation
    response = client.get('/spotify-login?emotion=0')
    assert response.status_code == 200
    assert 'auth_url' in json.loads(response.data)

    # Test invalid emotion ID
    response = client.get('/spotify-login?emotion=999')
    assert response.status_code == 400
    assert json.loads(response.data) == {"error": "Invalid emotion ID"}

def test_callback(client):
    # Mock Spotify OAuth flow
    with patch('app.sp_oauth.get_access_token') as mock_get_token:
        mock_get_token.return_value = {'access_token': 'test_token'}
        response = client.get('/callback?code=testcode&state=0')
        assert response.status_code == 302  # Redirect to Spotify playlist

    # Test invalid emotion ID
    with patch('app.sp_oauth.get_access_token') as mock_get_token:
        mock_get_token.return_value = {'access_token': 'test_token'}
        response = client.get('/callback?code=testcode&state=999')
        assert response.status_code == 400

def test_get_playlists(client):
    # Mock Spotify token validation
    with patch('app.sp_oauth.validate_token') as mock_validate:
        mock_validate.return_value = True
        response = client.get('/get_playlists?emotion=0')
        assert response.status_code == 302  # Redirect to Spotify playlist

    # Test invalid emotion ID
    with patch('app.sp_oauth.validate_token') as mock_validate:
        mock_validate.return_value = True
        response = client.get('/get_playlists?emotion=999')
        assert response.status_code == 400

def test_user_profile(client):
    # Mock Spotify token validation and user info
    with patch('app.sp_oauth.validate_token') as mock_validate, \
         patch('app.sp.current_user') as mock_user:
        mock_validate.return_value = True
        mock_user.return_value = {'id': 'testuser'}
        response = client.get('/user_profile')
        assert response.status_code == 200
        assert json.loads(response.data) == {'id': 'testuser'}

def test_store_image(client):
    # Mock image data
    image_path = "tests/test_image.jpg"  # Replace with a real image path
    encoded_image = encode_image_to_base64(image_path)

    # Test successful image storage
    response = client.post('/store_image', json={
        'image': encoded_image,
        'emotion_id': 0,
        'face_coordinates': {'x': 0, 'y': 0, 'w': 100, 'h': 100}
    })
    assert response.status_code == 200
    assert 'filename' in json.loads(response.data)

    # Test missing required keys
    response = client.post('/store_image', json={'image': encoded_image})
    assert response.status_code == 400
    assert json.loads(response.data) == {"error": "Missing key in request payload: emotion_id"}

def test_get_image(client):
    # Store an image first
    image_path = "tests/test_image.jpg"  # Replace with a real image path
    encoded_image = encode_image_to_base64(image_path)
    response = client.post('/store_image', json={
        'image': encoded_image,
        'emotion_id': 0,
        'face_coordinates': {'x': 0, 'y': 0, 'w': 100, 'h': 100}
    })
    filename = json.loads(response.data)['filename']

    # Test retrieving the image
    response = client.get(f'/get_image?filename={filename}')
    assert response.status_code == 200
    assert response.mimetype == 'image/jpeg'

    # Test invalid filename
    response = client.get('/get_image?filename=invalid')
    assert response.status_code == 404
    assert json.loads(response.data) == {"error": "Image not found"}

def test_list_images(client):
    # Test listing images
    response = client.get('/list_images')
    assert response.status_code == 200
    assert 'images' in json.loads(response.data)

def test_home(client):
    # Test home route
    response = client.get('/')
    assert response.status_code == 302  # Redirect to Spotify auth

def test_logout(client):
    # Test logout
    response = client.get('/logout')
    assert response.status_code == 302  # Redirect to home
    
    
def test_get_metadata(client):
    # Store an image first
    image_path = "tests/test_image.jpg"  # Replace with a real image path
    encoded_image = encode_image_to_base64(image_path)
    response = client.post('/store_image', json={
        'image': encoded_image,
        'emotion_id': 0,
        'face_coordinates': {'x': 0, 'y': 0, 'w': 100, 'h': 100}
    })
    filename = json.loads(response.data)['filename']

    # Test retrieving metadata
    response = client.get(f'/get_metadata?filename={filename}')
    assert response.status_code == 200
    metadata = json.loads(response.data)
    assert 'filename' in metadata
    assert 'emotion' in metadata
    assert 'face_coordinates' in metadata

    # Test missing filename
    response = client.get('/get_metadata')
    assert response.status_code == 400
    assert json.loads(response.data) == {"error": "Filename is required"}

    # Test invalid filename
    response = client.get('/get_metadata?filename=invalid')
    assert response.status_code == 404
    assert json.loads(response.data) == {"error": "Metadata file not found"}
    
def test_get_playlists(client):
    # Mock Spotify token validation
    with patch('app.sp_oauth.validate_token') as mock_validate:
        mock_validate.return_value = True
        response = client.get('/get_playlists?emotion=0')
        assert response.status_code == 302  # Redirect to Spotify playlist

    # Test invalid emotion ID
    with patch('app.sp_oauth.validate_token') as mock_validate:
        mock_validate.return_value = True
        response = client.get('/get_playlists?emotion=999')
        assert response.status_code == 400

    # Simulate an error in Spotify token validation
    with patch('app.sp_oauth.validate_token') as mock_validate:
        mock_validate.side_effect = Exception("Test error")
        response = client.get('/get_playlists?emotion=0')
        assert response.status_code == 500
        assert response.data == b"Failed to fetch playlist. Please try again."
        
def test_detect_emotion_error(client):
    # Simulate an error in image processing
    with patch('app.base64.b64decode') as mock_b64decode:
        mock_b64decode.side_effect = Exception("Test error")
        response = client.post('/detect_emotion', json={'image': 'invalid'})
        assert response.status_code == 500
        assert 'error' in json.loads(response.data)