import os
import glob
import re
from io import BytesIO

from pydub import AudioSegment

from dotenv import load_dotenv
from openai import OpenAI

EXCLUDE_GENERATED_FILES = True
VOICE = "nova"
TTS_MODEL = "tts-1"
MAX_CHARS = 4000  # Slightly less than 4096 to avoid edge cases.
CHUNK_FUNC = "nltk"  # "regex" or "nltk"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Set this in .env or as an environment variable. Also, you can use the OpenAI API key directly.

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chunk_text_with_regex(text, max_chunk_size=MAX_CHARS):
    """
    Splits `text` into a list of chunks, each not exceeding `max_chunk_size`.
    We try to split on sentence boundaries to make chunks more coherent.
    """
    # Split text into sentences by '.', '!', or '?', preserving delimiter.
    # This regex looks for a period, exclamation, or question mark followed by space.
    sentences = re.split(r'([.?!])', text)
    
    # Rebuild list of sentences including punctuation
    # e.g. ["Hello world", ".", " This is a test", ".", " And more", "!"]
    # We will pair up the punctuation with its sentence part.
    rebuilt_sentences = []
    for i in range(0, len(sentences) - 1, 2):
        sentence_part = sentences[i].strip()
        punctuation = sentences[i+1].strip()
        # Combine them back into one sentence string
        rebuilt_sentences.append((sentence_part + punctuation).strip())
    # If there's a trailing piece without punctuation, add it.
    if len(sentences) % 2 != 0:
        leftover = sentences[-1].strip()
        if leftover:
            rebuilt_sentences.append(leftover)

    chunks = []
    current_chunk = ""

    for sentence in rebuilt_sentences:
        # If adding this sentence would exceed the max chunk size, 
        # push the current chunk to chunks and start a new one.
        if len(current_chunk) + len(sentence) + 1 > max_chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            if current_chunk == "":
                current_chunk = sentence
            else:
                current_chunk += " " + sentence

    # Add the last chunk if it's not empty
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def chunk_text_with_nltk(text, max_chunk_size=MAX_CHARS):
    import nltk
    from nltk.tokenize import sent_tokenize
    nltk.download('punkt_tab', quiet=True)
    
    sentences = sent_tokenize(text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(sentence) > max_chunk_size:
            raise ValueError(f"Sentence too long to chunk: {sentence}")
        
        # Bulid the candidate chunk if we add this sentence
        if current_chunk:
            candidate_chunk = f"{current_chunk} {sentence}"
        else:
            candidate_chunk = sentence
            
        # If adding this sentence would exceed the max chunk size,
        # push the current chunk to chunks and start a new one.
        if len(candidate_chunk) > max_chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk = candidate_chunk
            
    # Add the last chunk if it's not empty
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        
    return chunks

def main():
    # Find all .txt files in the `audio` directory
    txt_files = glob.glob(os.path.join(os.getcwd(), "audio/*.txt"))
    print(f"Found {len(txt_files)} .txt files")

    for txt_file in txt_files:
        output_mp3 = f"{txt_file}.mp3"
        
        # If we are excluding already-generated files, skip if the .mp3 exists
        if EXCLUDE_GENERATED_FILES and os.path.exists(output_mp3):
            print(f"Skipping {txt_file} as audio already exists.")
            continue
        
        # Read the text
        with open(txt_file, "r", encoding="utf-8") as file:
            text = file.read()
            text = text.replace("\r\n", "\n").strip()

        print(f"Generating chunks for {txt_file}...")

        # Chunk the text into smaller pieces
        if CHUNK_FUNC == "regex":
            text_chunks = chunk_text_with_regex(text)
        elif CHUNK_FUNC == "nltk":
            text_chunks = chunk_text_with_nltk(text)
        else:
            raise ValueError(f"Invalid chunking function: {CHUNK_FUNC}")
        
        print(f"Split text into {len(text_chunks)} chunks")

        print(f"Generating audio for {txt_file}...")
        combined_audio = AudioSegment.silent(duration=0)

        for i, chunk in enumerate(text_chunks):
            # Generate audio for chunk
            try:
                response = client.audio.speech.create(
                    model=TTS_MODEL,
                    voice=VOICE,
                    input=chunk,
                )
            except Exception as e:
                print(f"Failed to generate audio for chunk {i} in {txt_file}: {e}")
                with open(f"{txt_file}.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"Chunk {i} error: {e}\n")
                continue
            
            # Convert response content (which is MP3 data) into an AudioSegment
            try:
                chunk_audio = AudioSegment.from_file(BytesIO(response.content), format="mp3")
            except Exception as e:
                print(f"Failed to convert audio for chunk {i} in {txt_file}: {e}")
                with open(f"{txt_file}.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"Chunk {i} conversion error: {e}\n")
                continue

            # Append this chunk to the combined audio
            combined_audio += chunk_audio

            print(f"Processed chunk {i+1}/{len(text_chunks)}")

        # Finally, export the combined audio to a single MP3
        combined_audio.export(output_mp3, format="mp3")
        print(f"Generated audio for {txt_file}: {output_mp3}")

    print("All audio files generated successfully.")

if __name__ == "__main__":
    main()
    