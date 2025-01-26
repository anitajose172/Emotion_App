# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from tensorflow.keras.models import load_model
# from tensorflow.keras.models import Sequential
# from tensorflow.keras.layers import Dense

# app = Flask(__name__)
# CORS(app)


# model = Sequential()
# model.load_weights(".weights.h5") 

# @app.route('/detect_emotion', methods=['POST'])
# def detect_emotion():
#   try:
#     image_data = request.json['image']
#     image_array = np.array(image_data)  # Convert list back to NumPy array

#     # Preprocess image if needed (assuming preprocessed in OpenCV code)
#     # ...

#     prediction = model.predict(image_array)
#     predicted_emotion = np.argmax(prediction[0])  # Get index of maximum value

#     # Map emotion labels based on your model's output (modify as needed)
#     emotion_map = {
#         0: 'Angry',
#         1: 'Disgust',
#         2: 'Fear',
#         3: 'Happy',
#         4: 'Neutral',
#         5: 'Sad',
#         6: 'Surprise'
#     }
#     predicted_emotion = emotion_map[predicted_emotion]

#     return jsonify({'emotion': predicted_emotion})

#   except Exception as e:
#     return jsonify({'error': str(e)}), 500

# if __name__ == '__main__':
#   app.run(debug=True)

from flask import Flask, request, jsonify
import numpy as np
import cv2
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)

# Load the pre-trained emotion model
emotion_model = load_model(".weights.h5")

# Define emotion labels
emotion_dict = {0: "Angry", 1: "Disgusted", 2: "Fearful", 3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprised"}

# API Endpoint for Emotion Detection
@app.route('/detect_emotion', methods=['POST'])
def detect_emotion():
    try:
        # Get the base64 image from the request
        data = request.get_json()
        img_str = data['image']
        img_data = base64.b64decode(img_str.split(",")[1])  # Remove the base64 header
        img = Image.open(BytesIO(img_data)).convert("L")    # Convert to grayscale

        # Preprocess the image
        img = img.resize((48, 48))
        img_array = img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0

        # Predict the emotion
        predictions = emotion_model.predict(img_array)
        max_index = int(np.argmax(predictions))
        emotion = emotion_dict[max_index]

        # Return the emotion and additional details (if needed)
        return jsonify({"emotion": emotion, "recommendations": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
