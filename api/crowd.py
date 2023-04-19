import requests


class CrowdAPI:

	@staticmethod
	def get_vocab(parent) -> str:
		url = f'http://bhasha.iiit.ac.in/crowd/job/api/gt/?job_id={parent}'
		# print(f'Fetching data from Crowdsource using API at: {url}')
		response = requests.get(url)
		if response.ok:
			ret = response.json()
			# return ret['gt'].strip().replace('\n', ' ').strip().split(' ')
			return ret['gt'].strip()