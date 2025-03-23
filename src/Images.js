import React, { useState, useEffect } from "react";
import axios from "axios";

const Images = () => {
  const [imageList, setImageList] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [metadata, setMetadata] = useState(null);

  const fetchImageList = async () => {
    try {
      const response = await axios.get("http://localhost:8080/list_images", { withCredentials: true });
      setImageList(response.data.images);
    } catch (error) {
      console.error("Error listing images:", error);
    }
  };

  const fetchImage = async (filename) => {
    try {
      const response = await axios.get("http://localhost:8080/get_image", {
        params: { filename },
        withCredentials: true,
        responseType: 'arraybuffer'
      });
      const base64Image = btoa(
        new Uint8Array(response.data).reduce((data, byte) => data + String.fromCharCode(byte), '')
      );
      setSelectedImage(`data:image/jpeg;base64,${base64Image}`);

      const metadataResponse = await axios.get("http://localhost:8080/get_metadata", {
        params: { filename: filename.replace('.enc', '') },
        withCredentials: true,
      });
      setMetadata(metadataResponse.data);
    } catch (error) {
      console.error("Error fetching image or metadata:", error);
    }
  };

  useEffect(() => {
    fetchImageList();
  }, []);

  return (
    <div>
      <h1>Captured Images</h1>
      <ul>
        {imageList.map((filename) => (
          <li key={filename}>
            <button onClick={() => fetchImage(filename)}>{filename}</button>
          </li>
        ))}
      </ul>
      {selectedImage && (
        <div>
          <h3>Selected Image</h3>
          <img src={selectedImage} alt="Captured" style={{ width: "300px" }} />
          {metadata && (
            <div>
              <p>Emotion: {metadata.emotion}</p>
              <p>Coordinates: {JSON.stringify(metadata.face_coordinates)}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Images;