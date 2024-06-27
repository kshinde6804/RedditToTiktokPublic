import boto3
import json

# Initialize a session using Amazon Polly
polly_client = boto3.Session(
    aws_access_key_id='YOUR_KEY_ID',
    aws_secret_access_key='YOUR_ACCESS_KEY',
    region_name='YOUR_REGION'
).client('polly')
voice = 'Matthew'

def get_speech_audio(content, output_audio_file):
    # Request audio stream
    response_audio = polly_client.synthesize_speech(
        Text=f"<speak>{content}</speak>",
        TextType='ssml',
        VoiceId=voice,
        OutputFormat='mp3',
    )

    # Write the audio stream to a file
    audio_stream = response_audio.get('AudioStream')
    with open(output_audio_file, 'wb') as file:
        file.write(audio_stream.read())

def synthesize_speech(text, output_audio_file, output_marks_file):
    
    get_speech_audio(text, output_audio_file)
    
    # Request speech marks
    response_marks = polly_client.synthesize_speech(
        VoiceId=voice,
        OutputFormat='json',
        Text=text,
        SpeechMarkTypes=['word']
    )
    
    # Write the speech marks to a file
    marks_stream = response_marks.get('AudioStream')
    with open(output_marks_file, 'w', encoding='utf-8') as file:  # Ensure correct encoding
        file.write(marks_stream.read().decode('utf-8'))
    
    # Parse the speech marks from the file
    with open(output_marks_file, 'r', encoding='utf-8') as file:  # Ensure correct encoding
        speech_marks = [json.loads(line) for line in file]
    
    return speech_marks

if __name__ == "__main__":
    main()

