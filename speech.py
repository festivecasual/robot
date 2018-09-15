import sys

from google.cloud import texttospeech


client = texttospeech.TextToSpeechClient()
input = texttospeech.types.SynthesisInput(text=sys.argv[1])
voice = texttospeech.types.VoiceSelectionParams(
    language_code='en-US',
    ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)
audio_config = texttospeech.types.AudioConfig(audio_encoding=texttospeech.enums.AudioEncoding.MP3)
response = client.synthesize_speech(input, voice, audio_config)

with open('output.mp3', 'wb') as out:
    out.write(response.audio_content)

