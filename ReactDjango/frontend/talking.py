import os
import pyaudio
import wave
import numpy as np
import threading
from dotenv import load_dotenv
from openai import OpenAI
import openai
from pinecone import Pinecone, ServerlessSpec
import json

# Load environment variables from .env file
load_dotenv()
client = OpenAI()

# Retrieve API key from environment variable
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("No OpenAI API key found in environment variables.")

# Debug print to verify the API key
print(f"Using OpenAI API Key: {openai_api_key[:5]}...{openai_api_key[-5:]}")

# Initialize Pinecone client
pinecone_api_key = os.getenv("PINECONE_API_KEY")
if not pinecone_api_key:
    raise ValueError("No Pinecone API key found in environment variables.")

pc = Pinecone(api_key=pinecone_api_key)

# Connect to Pinecone index
if 'user1' not in pc.list_indexes().names():
    pc.create_index(
        name='user1', 
        dimension=1536, 
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )
index = pc.Index('user1')

class SpeechRecorder:
    def __init__(self):
        self.chunk = 1024
        self.sample_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.silence_threshold = 500
        self.silence_duration = 1.75
        self.audio = pyaudio.PyAudio()
        self.conversation_history = []
        self.noise_levels = []
        self.state = 'idling'

    def get_state(self):
        return self.state

    def update_status(self, status):
        """Updates the internal state and prints a message."""
        self.state = status
        print(f"Status updated to: {self.state}")

    def is_silent(self, data):
        """Returns 'True' if below the silence threshold"""
        max_value = np.frombuffer(data, dtype=np.int16).max()
        if not self.noise_levels:
            self.noise_levels.append(max_value)
        return max_value < self.silence_threshold

    def adjust_silence_threshold(self):
        if self.noise_levels:
            self.silence_threshold = np.mean(self.noise_levels) + 100

    def record(self):
        def run_recording():
            self.state = 'listening'
            stream = self.audio.open(format=self.sample_format,
                                     channels=self.channels,
                                     rate=self.rate,
                                     frames_per_buffer=self.chunk,
                                     input=True)
            print("Adjusting for ambient noise...")
            print("Ready to record. Start speaking...")
            file_counter = 0
            calibrating = True
            self.update_status('idling')

            while True:
                frames = []
                silent_chunks = 0
                is_recording = False
                self.update_status('listening')

                while True:
                    try:
                        data = stream.read(self.chunk, exception_on_overflow=False)
                    except IOError as e:
                        print(f"Error: {e}")
                        continue

                    frames.append(data)

                    if calibrating:
                        self.noise_levels.append(np.frombuffer(data, dtype=np.int16).max())
                        if len(self.noise_levels) > 50:
                            calibrating = False
                            self.adjust_silence_threshold()
                            print(f"Calibrated silence threshold: {self.silence_threshold}")

                    if self.is_silent(data) and not calibrating:
                        silent_chunks += 1
                    else:
                        silent_chunks = 0
                        is_recording = True

                    if is_recording and silent_chunks > (self.silence_duration * self.rate / self.chunk):
                        print(f"Speech chunk {file_counter + 1} finished.")
                        self.state = 'idling'
                        break

                if is_recording:
                    file_name = self.save_audio(frames, file_counter)
                    user_text = self.process_audio(file_name)
                    print(f"User asked: {user_text}")
                    self.conversation_history.append({"role": "user", "content": user_text})
                    response_text = self.gpt_response()
                    print(f"Response: {response_text}")
                    self.conversation_history.append({"role": "assistant", "content": response_text})
                    file_counter += 1
                    self.state = 'stopped'
                    self.upsert_to_pinecone(file_counter, user_text)
                    
                self.update_status('idling')

        thread = threading.Thread(target=run_recording)
        thread.start()

    def save_audio(self, frames, counter):
        file_name = f"output_{counter}.wav"
        wf = wave.open(file_name, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.sample_format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"Audio saved as {file_name}")
        return file_name

    def process_audio(self, audio_file_path):
        with open(audio_file_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        return response.text

    def gpt_response(self):
        self.update_status('responding')
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
            ] + self.conversation_history
        )
        self.update_status('stopped')
        return response.choices[0].message.content

    def upsert_to_pinecone(self, vector_id, text):
        embedding_response = client.embeddings.create(model="text-embedding-ada-002",
        input=[text])
        embedding = embedding_response.data[0].embedding

        index.upsert(vectors=[{
            "id": str(vector_id),
            "values": embedding
        }])
        print(f"Upserted vector ID {vector_id} to Pinecone")

    def close(self):
        self.audio.terminate()
