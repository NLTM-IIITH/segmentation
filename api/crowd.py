import requests


class CrowdAPI:

	@staticmethod
	def get_vocab(parent) -> str:
		url = f'http://bhasha.iiit.ac.in/crowd/job/api/gt/?job_id={parent}'
		response = requests.get(url)
		if response.ok:
			ret = response.json()
			return ret['gt'].strip()
		else:
			return ''

	@staticmethod
	def get_ilocr_vocab(parent) -> str:
		url = f'https://ilocr.iiit.ac.in/crowd/job/api/gt/?job_id={parent}'
		response = requests.get(url)
		if response.ok:
			ret = response.json()
			return ret['gt'].strip()