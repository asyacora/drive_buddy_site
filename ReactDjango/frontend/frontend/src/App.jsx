import { Canvas } from '@react-three/fiber';
import Blob from "./index.jsx";
import React, { useState } from 'react';


export default function App() {
  const [conversationState, setConversationState] = useState('IDLING');

  const updateState = (state) => {
    console.log(`State changing to: ${state}`);
    setConversationState(state);
  };

  return (
    <div className="container">
      <Canvas camera={{ position: [0.0, 0.0, 8.0] }}>
        <Blob conversationState={conversationState} />
      </Canvas>
      
      <div style={{ marginTop: '20px' }}>
        <button onClick={() => updateState('LISTENING')}>Set Listening</button>
        <button onClick={() => updateState('RESPONDING')}>Set Responding</button>
        <button onClick={() => updateState('STOPPED')}>Set Stopped</button>
        <button onClick={() => updateState('IDLING')}>Set Idling</button>
      </div>
    </div>
  );
}
