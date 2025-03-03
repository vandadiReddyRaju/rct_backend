//// filepath: frontend/src/components/InputForm.js
import React from 'react';

const InputForm = ({ userPrompt, setUserPrompt, images, setImages }) => {
  const onImageChange = (e) => {
    const files = Array.from(e.target.files);
    // For simplicity, here we just store file names (or process to base64 as needed)
    setImages(files.map(file => file.name));
  };

  return (
    <div className="input-form">
      <div className="form-group">
        <label>Your Query:</label>
        <textarea
          value={userPrompt}
          onChange={(e) => setUserPrompt(e.target.value)}
          rows={4}
          cols={50}
          placeholder="Enter your query here..."
        />
      </div>
      <div className="form-group">
        <label>Upload Images (optional):</label>
        <input type="file" multiple onChange={onImageChange} />
      </div>
    </div>
  );
};

export default InputForm;