from dotenv import load_dotenv
from openai import OpenAI
import os
import glob

EXCLUDE_GENERATED_FILES = True
VOICE = "nova"
TTS_MODEL = "tts-1"

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Find all .txt files in the current directory
txt_files = glob.glob(os.path.join(os.getcwd(), "audio/*.txt"))
print(f"Found {len(txt_files)} .txt files")

# Read the contents of each .txt file and generate audio
for txt_file in txt_files:
    if EXCLUDE_GENERATED_FILES and os.path.exists(f"{txt_file}.mp3"):
        print(f"Skipping {txt_file} as audio already exists")
        continue
    
    with open(txt_file, "r") as file:
        text = file.read()
        text.replace("\r\n", "\n")
        
        print(f"Generating audio for {txt_file}...")

        try:
            response = client.audio.speech.create(
                model=TTS_MODEL,
                voice=VOICE,
                input=text,
            )
        except Exception as e:
            print(f"Failed to generate audio for {txt_file}")
            with open(f"{txt_file}.log", "w") as log_file:
                log_file.write(str(e))
            continue

        with open(f"{txt_file}.mp3", "wb") as file:
            file.write(response.content)
            print(f"Generated audio for {txt_file}")
            
print("All audio files generated successfully")