import hashlib
from pathlib import Path
import cmd
import contextlib

from google.cloud import texttospeech

with contextlib.redirect_stdout(None):
    import pygame
    pygame.init()


client = texttospeech.TextToSpeechClient()
voice = texttospeech.types.VoiceSelectionParams(
    language_code='en-US',
    ssml_gender=texttospeech.enums.SsmlVoiceGender.NEUTRAL)
audio_config = texttospeech.types.AudioConfig(audio_encoding=texttospeech.enums.AudioEncoding.MP3)

def synthesize(text, target):
    input = texttospeech.types.SynthesisInput(text=text)
    response = client.synthesize_speech(input, voice, audio_config)
    with open(target, 'wb') as out:
        out.write(response.audio_content)

def speak(text):
    cache = '/tmp/speech-%s.mp3' % hashlib.sha1(text.encode('ascii')).hexdigest()
    if not Path(cache).exists():
        synthesize(text, cache)
    pygame.mixer.music.load(cache)
    pygame.mixer.music.play()
 
class InteractiveSpeech(cmd.Cmd):
    prompt = 'speech > '

    def do_say(self, arg):
        speak(arg)

    def do_quit(self, arg):
        return True

if __name__ == '__main__':
    InteractiveSpeech().cmdloop()

