import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import Camera from '../Camera';
import EmotionDisplay from './EmotionDisplay';

// Mock react-webcam
jest.mock('react-webcam', () => {
  const React = require('react');
  const MockWebcam = ({ onUserMedia }) => {
    React.useEffect(() => {
      onUserMedia();
    }, [onUserMedia]);
    return <div data-testid="mock-webcam" />;
  };
  MockWebcam.prototype.getScreenshot = jest.fn(() => 'data:image/jpeg;base64,dummydata');
  return MockWebcam;
});

// Mock window.location.href
const mockLocation = { href: '' };
Object.defineProperty(window, 'location', {
  value: mockLocation,
  writable: true,
});

// Mock EmotionDisplay to match the real component (optional, can use real one)
jest.mock('./EmotionDisplay', () => {
  const React = require('react');
  return function EmotionDisplay({ emotion }) {
    return (
      <div>
        {emotion && <h2>Detected Emotion: {emotion}</h2>}
      </div>
    );
  };
});

describe('Camera Component', () => {
  let mockAxios;

  beforeEach(() => {
    mockAxios = new MockAdapter(axios);
    jest.useFakeTimers(); // For useEffect interval
  });

  afterEach(() => {
    mockAxios.reset();
    jest.useRealTimers();
    mockLocation.href = ''; // Reset mock location
  });

  // Test 1: Component renders correctly
  it('renders webcam, canvas, and button', () => {
    render(<Camera />);
    expect(screen.getByTestId('mock-webcam')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /redirect to spotify/i })).toBeInTheDocument();
    // eslint-disable-next-line testing-library/prefer-presence-queries
    expect(screen.getByRole('heading', { level: 2, name: /detected emotion/i }, { hidden: true })).not.toBeInTheDocument(); // Initially no emotion
  });

  // Test 2: Draws bounding boxes on canvas
  it('draws bounding boxes and emotion text on canvas', () => {
    render(<Camera />);
    const canvas = screen.getByRole('canvas');
    const ctx = canvas.getContext('2d');

    mockAxios.onPost('http://127.0.0.1:8080/detect_emotion').reply(200, {
      emotions: ['happy'],
      face_coordinates: [{ x: 263, y: 187, w: 131, h: 131 }],
      emotion_indices: [3],
    });

    jest.advanceTimersByTime(1000);

    expect(ctx.strokeRect).toHaveBeenCalledWith(263, 187, 131, 131);
    expect(ctx.fillText).toHaveBeenCalledWith('happy', 268, 177); // x + 5, y - 10
  });

  // Test 3: Detects emotions and updates state
  it('detects emotions and sets primary emotion', async () => {
    render(<Camera />);
    
    mockAxios.onPost('http://127.0.0.1:8080/detect_emotion').reply(200, {
      emotions: ['happy'],
      face_coordinates: [{ x: 263, y: 187, w: 131, h: 131 }],
      emotion_indices: [3],
    });

    jest.advanceTimersByTime(1000);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Detected Emotion: happy/i })).toBeInTheDocument();
    });
  });

  // Test 4: Redirects to Spotify on button click
  it('redirects to Spotify with valid emotion', async () => {
    render(<Camera />);
    
    mockAxios.onPost('http://127.0.0.1:8080/detect_emotion').reply(200, {
      emotions: ['happy'],
      face_coordinates: [{ x: 263, y: 187, w: 131, h: 131 }],
      emotion_indices: [3],
    });
    mockAxios.onPost('http://localhost:8080/store_image').reply(200, { filename: 'test.enc' });
    mockAxios.onGet('http://localhost:8080/spotify-login').reply(200, {
      auth_url: 'https://accounts.spotify.com/authorize?client_id=abc',
    });

    jest.advanceTimersByTime(1000);

    fireEvent.click(screen.getByRole('button', { name: /redirect to spotify/i }));

    await waitFor(() => {
      expect(mockLocation.href).toBe('https://accounts.spotify.com/authorize?client_id=abc');
    });
  });

  // Test 5: Handles error when no emotion is detected
  it('shows error when redirecting without detected emotion', async () => {
    render(<Camera />);
    
    fireEvent.click(screen.getByRole('button', { name: /redirect to spotify/i }));

    await waitFor(() => {
      expect(screen.getByText('No emotion detected to redirect.')).toBeInTheDocument();
    });
  });

  // Test 6: Handles API error during emotion detection
  it('shows error on emotion detection failure', async () => {
    render(<Camera />);
    
    mockAxios.onPost('http://127.0.0.1:8080/detect_emotion').reply(500, { error: 'Server error' });

    jest.advanceTimersByTime(1000);

    await waitFor(() => {
      expect(screen.getByText('Error capturing image or processing with API.')).toBeInTheDocument();
    });
  });
});