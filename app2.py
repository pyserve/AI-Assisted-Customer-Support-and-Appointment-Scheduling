import os
from flask import Flask, request, jsonify, render_template
from groq import Groq
import pygame
from deepgram import DeepgramClient, SpeakOptions
from datetime import datetime
import time  # Import time module for latency calculation

# Initialize Flask app
app = Flask(__name__)

# Initialize Groq client
client = Groq(api_key="GROK")

# Initialize pygame mixer
pygame.mixer.init()

# Define Deepgram API key and options
DEEPGRAM_API_KEY = "DEEPGRAM"  # Replace with your actual Deepgram API key
output_dir = r"C:\Users\Weaver 15\Documents\Capstone Project\output_files"  # Directory where output files will be saved

# Initial system message setting the context
conversation_history = [
    {
        "role": "system",
        "content": "You are a receptionist at a Heating and Ventilation and Air Conditioning Company. Be resourceful and efficient. Your Company sells Heat Pumps and Air Conditioners. The available sales agents are Raju and Sanat. Only answer in two sentences."
    }
]

def save_to_file(deepgram, filename, speak_options, options):
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Save the audio content to the file
    response = deepgram.speak.v("1").save(filename, speak_options, options)

def play_audio(filename):
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

    # Wait for the audio to finish playing
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global conversation_history

    start_time = time.time()  # Capture start time

    user_input = request.json["user_input"]

    # Add user input to conversation history
    conversation_history.append({
        "role": "user",
        "content": user_input
    })

    # Generate response from the model
    chat_completion = client.chat.completions.create(
        messages=conversation_history,
        model="llama3-8b-8192"
    )

    ai_response = chat_completion.choices[0].message.content

    # Add AI response to conversation history
    conversation_history.append({
        "role": "assistant",
        "content": ai_response
    })

    # Use AI response as text for Deepgram
    try:
        # Create a Deepgram client
        deepgram = DeepgramClient(api_key=DEEPGRAM_API_KEY)

        # Generate a unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"output_{timestamp}.mp3")

        # Configure Deepgram options
        options = SpeakOptions(
            model="aura-asteria-en"
        )

        # Speak options based on AI response
        SPEAK_OPTIONS = {"text": ai_response}

        # Call Deepgram API to save speech to file
        save_to_file(deepgram, filename, SPEAK_OPTIONS, options)
        print(f"File '{filename}' saved successfully.")

        # Play the generated MP3 file using pygame
        play_audio(filename)

    except Exception as e:
        print(f"Exception: {e}")

    end_time = time.time()  # Capture end time
    latency = end_time - start_time  # Calculate latency in seconds
    print(latency)

    return jsonify({
        "response": ai_response,
        "latency_seconds": latency  # Include latency in the response
    })

# Start Flask server
if __name__ == "__main__":
    app.run()
