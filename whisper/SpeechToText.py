import wget
from IPython.display import Audio, display
from transformers import pipeline

# load whisper library
whisper = pipeline('automatic-speech-recognition', model = 'openai/whisper-medium')

#download audio file for conversion
audio_url = "https://www2.cs.uic.edu/~i101/SoundFiles/taunt.wav"
audio_path = wget.download(audio_url, "audio.wav")

# display(Audio(audio_path, autoplay=True))
# convert audio to text
text = whisper(audio_path)

# final text
text