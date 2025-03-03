//// filepath: frontend/src/App.js
import React, { useState } from 'react';
import InputForm from './components/InputForm';
import RunButton from './components/RunButton';
import OutputDisplay from './components/OutputDisplay';
import './App.css';

function App() {
  const [userPrompt, setUserPrompt] = useState('');
  const [images, setImages] = useState([]);
  const [output, setOutput] = useState('');

  const runApi = async () => {
    const payload = {
      user_prompt: userPrompt,
      images: images // Adjust image processing as needed
    };

    try {
      const response = await fetch('http://127.0.0.1:5000/run-api', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (data.result) {
        setOutput(data.result);
      } else {
        setOutput(data.error);
      }
    } catch (error) {
      setOutput(error.message);
    }
  };

  return (
    <div className="container">
      <h1>AI Model Interface</h1>
      <InputForm 
        userPrompt={userPrompt}
        setUserPrompt={setUserPrompt}
        images={images}
        setImages={setImages}
      />
      <RunButton onClick={runApi} />
      <OutputDisplay output={output} />
    </div>
  );
}

export default App;