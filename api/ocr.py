import base64
import json
import os
from os.path import join

import requests


class OCRAPI:
	LANGUAGE_CODES = {
		'hindi': 'hi',
		'english': 'en',
		'marathi': 'mr',
		'tamil': 'ta',
		'telugu': 'te',
		'kannada': 'kn',
		'gujarati': 'gu',
		'punjabi': 'pa',
		'bengali': 'bn',
		'malayalam': 'ml',
		'assamese': 'asa',
		'manipuri': 'mni',
		'oriya': 'ori',
		'urdu': 'ur',

		# Extra languages
		'bodo': 'brx',
		'dogri': 'doi',
		'kashmiri': 'ks',
		'konkani': 'kok',
		'maithili': 'mai',
		'nepali': 'ne',
		'sanskrit': 'sa',
		'santali': 'sat',
		'sindhi': 'sd',
	}

	@staticmethod
	def fire(
		folder_path,
		language,
		incldue_prob: bool = False,
		modality: str = 'handwritten',
		version: str = 'v3_post'
	) -> list[dict]:
		"""
		calls the layout parser api and returns the json response
		"""
		url = 'https://ilocr.iiit.ac.in/ocr/infer'
		images = os.listdir(folder_path)
		images = sorted(images, key=lambda x:int(x.strip().split('.')[0]))
		images = [join(folder_path, i) for i in images if i.endswith('jpg')]
		images = [base64.b64encode(open(i, 'rb').read()).decode() for i in images]
		ocr_request = {
			'imageContent': images,
			'modality': modality,
			'version': version,
			'language': OCRAPI.LANGUAGE_CODES[language],
			'meta': {
				'include_probability': incldue_prob
			}
		}
		headers = {
			'Content-Type': 'application/json'
		}
		response = requests.post(
			url,
			headers=headers,
			data=json.dumps(ocr_request),
		)
		if response.ok:
			ret = response.json()
			return ret
		else:
			return []


	@staticmethod
	def fire_postprocess(ocr_output, language, vocabulary) -> list[dict[str, list[str]]]:
		"""
		calls the layout parser api and returns the json response
		"""
		url = 'https://ilocr.iiit.ac.in/ocr/postprocess'
		ocr_request = {
			'words': ocr_output,
			'vocabulary': vocabulary,
			'language': OCRAPI.LANGUAGE_CODES[language],
		}
		headers = {
			'Content-Type': 'application/json'
		}
		# print(f'Performing OCR using API at: {url}')
		response = requests.post(
			url,
			headers=headers,
			data=json.dumps(ocr_request),
			timeout=2*60
		)
		if response.ok:
			ret = response.json()
			return ret
		else:
			print(response.text)
			raise ValueError('Error in PostProcess OCR')