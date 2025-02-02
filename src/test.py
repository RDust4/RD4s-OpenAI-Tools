from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.audio.speech.create(
    model="tts-1",
    voice="alloy",
    input="Hello, my name is Alloy. I am a text-to-speech model created by OpenAI. I am here to help you with your text-to-speech needs.",
)



# The method "stream_to_file" in class "HttpxBinaryResponseContent" is deprecated
# Due to a bug, this method doesn't actually stream the response content, `.with_streaming_response.method()` should be used insteadPylance
# response.stream_to_file("output.mp3")

with open("output.mp3", "wb") as f:
    f.write(response.content)
