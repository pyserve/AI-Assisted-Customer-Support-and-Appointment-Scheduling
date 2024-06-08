import os
import requests
from dotenv import load_dotenv
import pyaudio

# Load environment variables
load_dotenv()

DG_API_KEY = os.getenv("ec020d197403ff54e9d996bfcc41e2f5b17ebd34")
MODEL_NAME = "aura-luna-en"

def play_audio(audio_data, sample_rate):
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=sample_rate,
        output=True
    )
    stream.write(audio_data)
    stream.stop_stream()
    stream.close()
    audio.terminate()

def send_tts_request(text):
    DEEPGRAM_URL = f"https://api.beta.deepgram.com/v1/speak?model={MODEL_NAME}&performance=some&encoding=linear16&sample_rate=24000"

    headers = {
        "Authorization": f"Token {DG_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "voice": MODEL_NAME
    }

    try:
        r = requests.post(DEEPGRAM_URL, stream=True, headers=headers, json=payload)
        r.raise_for_status()  # Raise an exception for HTTP errors

        audio_data = b""
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                audio_data += chunk
        
        # Assuming the sample rate is 24000 based on the Deepgram URL
        play_audio(audio_data, sample_rate=24000)
    except Exception as e:
        print(f"Error: {e}")

# Example usage with saving to file
text = """
The returns for performance are superlinear."""
send_tts_request(text)
