import React, { useEffect, useRef, useState } from "react";
import { useFrame } from "@react-three/fiber";
import vertexShader from "./vertexShader";
import fragmentShader from "./fragmentShader";

const Blob = ({ conversationState }) => {
  const mesh = useRef(null);
  const [intensity, setIntensity] = useState(0.1); // Default value
  const [speed, setSpeed] = useState(0.5); // Default value

  // Update intensity and speed based on conversationState
  useEffect(() => {
    switch (conversationState) {
      case 'RESPONDING':
        setIntensity(0.75);
        setSpeed(2);
        break;
      case 'LISTENING':
        setIntensity(0.35);
        setSpeed(1.25);
        break;
      case 'STOPPED':
        setIntensity(0.1);
        setSpeed(0.8);
        break;
      case 'IDLING':
        setIntensity(0.05);
        setSpeed(0.5);
        break;
      default:
        setIntensity(0.1);
        setSpeed(0.5);
    }
  }, [conversationState]);

  // Update shader uniforms based on intensity and speed
  useFrame((state) => {
    const { clock } = state;
    if (mesh.current) {
      mesh.current.material.uniforms.u_time.value = speed * clock.getElapsedTime();
      mesh.current.material.uniforms.u_intensity.value = intensity;
    }
  });

  return (
    <mesh ref={mesh}>
      <icosahedronGeometry args={[2, 20]} />
      <shaderMaterial
        attach="material"
        args={[{
          vertexShader,
          fragmentShader,
          uniforms: {
            u_intensity: { value: intensity },
            u_time: { value: 0.0 },
          }
        }]}
      />
    </mesh>
  );
};

export default Blob;
