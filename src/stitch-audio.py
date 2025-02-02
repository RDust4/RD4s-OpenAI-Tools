"""
This file is an interactie script that allows the user to stitch together multiple audio files into a single audio file.
"""

import os

from pydub import AudioSegment

def main():
    # Get the list of audio files to stitch together
    print("Enter the paths of the audio files to stitch together, separated by newlines (empty line to end input):")
    
    audio_files = []
    while True:
        path = input().strip().strip('"').strip("'")
        if not path:
            break
        if not os.path.exists(path):
            print(f"File not found: {path}")
            continue
        audio_files.append(path)
    
    # Get the output file path
    output_path = input("Enter the path of the output file: ").strip().strip('"').strip("'")
    print()
    
    # Create a list of AudioSegment objects from the audio files
    print("Stitching audio files together...")
    audio_segments = [AudioSegment.from_file(file) for file in audio_files]
    
    # Combine the audio segments into a single AudioSegment
    combined = sum(audio_segments)
    
    # Export the combined audio to the output file
    combined.export(output_path, format="mp3")
    print(f"Audio files stitched together and saved to {output_path}")
    
if __name__ == "__main__":
    main()
    