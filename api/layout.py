import os

import requests


class LayoutAPI:

	@staticmethod
	def fire(folder_path, model='craft') -> list:
		"""
		calls the layout parser api and returns the json response
		"""
		url = 'https://ilocr.iiit.ac.in/layout/'
		files = os.listdir(folder_path)
		files = [os.path.join(folder_path, i) for i in files if i.endswith('jpg')]
		files = [(
			'images', (
				os.path.basename(image_path),
				open(image_path, 'rb'),
				'image/jpeg',
			)
		) for image_path in files]
		response = requests.post(
			url,
			headers={},
			data={
				'model': model
			},
			files=files,
		)
		if response.ok:
			return response.json()
		return []
