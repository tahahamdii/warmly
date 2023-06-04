import openai
import winsound
import time
import pyaudio
import keyboard
import wave
import json
from utils.translate import *
from utils.TTS import *
from utils.promptMaker import *
from utils.notification import *

openai.api_key = "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"

conversation = []
history = {"history": conversation}

total_characters = 0
chat = ""
chat_now = ""
chat_prev = ""
is_Speaking = False
owner_name = "Patient"
trigger = "I will call a doctor"

# Function to get the user's input audio
def record_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    WAVE_OUTPUT_FILENAME = "input.wav"
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    frames = []
    print("Recording...")
    while keyboard.is_pressed('RIGHT_SHIFT'):
        data = stream.read(CHUNK)
        frames.append(data)
    print("Stopped recording.")
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    transcribe_audio("input.wav")

# Function to transcribe the user's audio
def transcribe_audio(file):
    global chat_now
    try:
        audio_file = open(file, "rb")
        transcript = openai.Audio.translate("whisper-1", audio_file)
        chat_now = transcript.text
        print("Question: " + chat_now)
    except Exception as e:
        print("Error transcribing audio: {0}".format(e))
        return

    result = owner_name + " said " + chat_now
    conversation.append({'role': 'user', 'content': result})
    openai_answer()

# Function to get an answer from OpenAI
def openai_answer():
    global total_characters, conversation, trigger

    total_characters = sum(len(d['content']) for d in conversation)

    while total_characters > 4000:
        try:
            conversation.pop(2)
            total_characters = sum(len(d['content']) for d in conversation)
        except Exception as e:
            print("Error removing old messages: {0}".format(e))

    with open("conversation.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

    prompt = getPrompt()

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt,
        max_tokens=128,
        temperature=1,
        top_p=0.9
    )
    message = response['choices'][0]['message']['content']
    conversation.append({'role': 'assistant', 'content': message})

    if trigger in message:
        prompt = getSummary()
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt,
            max_tokens=128,
            temperature=1,
            top_p=0.9
        )
        summary = response['choices'][0]['message']['content']
        send_message(summary)

    translate_text(message)

# Translating is optional
def translate_text(text):
    global is_Speaking
    detect = detect_google(text)
    tts_en = translate_google(text, f"{detect}", "EN")
    try:
        print("EN Answer: " + tts_en)
    except Exception as e:
        print("Error printing text: {0}".format(e))
        return

    silero_tts(tts_en, "en", "v3_en", "en_21")

    time.sleep(1)

    # is_Speaking is used to prevent the assistant from speaking more than one audio at a time
    is_Speaking = True
    winsound.PlaySound("test.wav", winsound.SND_FILENAME)
    is_Speaking = False

    # Clear the text files after the assistant has finished speaking
    time.sleep(1)
    with open("output.txt", "w") as f:
        f.truncate(0)
    with open("chat.txt", "w") as f:
        f.truncate(0)

# Function to get to know the user by asking 10 questions
def get_to_know_user():
    global owner_name, conversation

    print("Let's get to know you better!")
    owner_name = input("What's your name? ")

    for i in range(10):
        question = input("Question {0}: ".format(i + 1))
        answer = input("Your answer: ")
        result = owner_name + " answered " + answer
        conversation.append({'role': 'user', 'content': result})

    # Save the conversation history to a file
    with open("conversation.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

# Main program
if __name__ == '__main__':
    print("Press and hold Right Shift to record audio")

    # Check if the conversation data file exists
    try:
        with open("conversation.json", "r", encoding="utf-8") as f:
            history = json.load(f)
            conversation = history["history"]
    except FileNotFoundError:
        # If the file doesn't exist, get to know the user
        get_to_know_user()

    # Start the question-answering loop
    while True:
        if keyboard.is_pressed('RIGHT_SHIFT'):
            record_audio()
