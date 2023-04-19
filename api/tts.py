import json
from os.path import join
from tempfile import TemporaryDirectory

import requests
from google.cloud import texttospeech
from tqdm import tqdm


class TTSAPI:

	def get_access_token():
		key = 'RTFMNGluUVRlc25WbHczMlp6SzB4em9LVVhzYTpXdGZubjhFV29nVlNlTXpHTllzMFBYYkI4dnNh'
		url = 'https://sts.choreo.dev/oauth2/token'
		headers = {
			'Authorization': f'Basic {key}'
		}
		data = {
			'grant_type': 'client_credentials'
		}
		r = requests.post(url, headers=headers, data=data, verify=False)
		print(r.text)
		return r.json()['access_token']

	def fire_dev(text, lang, audio_path):
		print(text)
		text = text.strip().split('\n')
		print(len(text))
		tmp = TemporaryDirectory(prefix='tts_parts')
		folder = tmp.name
		folder = '/home/ocr_testing/test'
		token = TTSAPI.get_access_token()
		print(f'Performing TTS for {lang}')
		url = "https://11fc0468-644c-4cc6-be7d-46b5bffcd914-prod.e1-us-east-azure.choreoapis.dev/aqqz/iltts/1.0.0/IITM_TTS/API/tts.php"
		headers = {
			'Authorization': f'Bearer {token}',
			'Content-Type': 'application/json',
		}
		ret = []
		# for i in tqdm(text):
		for idx, i in enumerate(text):
			payload = json.dumps({
				'text': i,
				'gender': 'male',
				'lang': 'Hindi',
			})
			try:
				r = requests.post(url, headers=headers, data=payload)
				ret.append(r.json()['outspeech_filepath'][0])
				print(ret[-1])
				with open(join(folder, f'{idx}.wav'), 'wb') as f:
					f.write(requests.get(ret[-1]).content)
			except Exception as e:
				print(e)
				print(r.text)
		ret = [i.strip() for i in ret]
		print(ret)
		return '\n'.join(ret)

	@staticmethod
	def fire(text, language_code, outfile):
		client = texttospeech.TextToSpeechClient()
		synthesis_input = texttospeech.SynthesisInput(text=text)

		# Build the voice request, select the language code ("en-US") and the ssml
		# voice gender ("neutral")
		voice = texttospeech.VoiceSelectionParams(
			language_code=f'{language_code}-IN',
			ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
		)

		# Select the type of audio file you want returned
		audio_config = texttospeech.AudioConfig(
			audio_encoding=texttospeech.AudioEncoding.MP3
		)

		# Perform the text-to-speech request on the text input with the selected
		# voice parameters and audio file type
		response = client.synthesize_speech(
			input=synthesis_input, voice=voice, audio_config=audio_config
		)

		with open(outfile, 'wb') as out:
			out.write(response.audio_content)
