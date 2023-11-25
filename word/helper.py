import os
from dataclasses import dataclass
from os.path import join
from tempfile import TemporaryDirectory

import requests


@dataclass
class CustomDir:
	name: str


def send_to_verification(ver: list[tuple]):
	print(f'Preparing to send {len(ver)} words to verification portal')
	tmp = TemporaryDirectory(prefix='ver')
	folder = tmp.name
	folder = join(folder, 'test')
	os.system('mkdir ' + folder)
	image_folder = join(folder, 'image')
	os.system('mkdir ' + image_folder)
	# print('setup the folder structure for the zip')
	ret = []
	for word, ocr in ver:
		os.system(f'cp {word.image.path} {image_folder}') # type: ignore
		ret.append(f'image/{word.id}.jpg\t{ocr.strip()}') # type: ignore
	print(f'Saved the words at {folder}')
	with open(join(folder, 'gt.txt'), 'w', encoding='utf-8') as f:
		f.write('\n'.join(ret))
	# print('added all the images and gt file to the folders')
	zip_path = join(tmp.name, 'test.zip')
	os.system(f'cd {tmp.name} && zip -r test.zip test/ >/dev/null && cd -')
	# print(f'created the zip file to be uploaded: {zip_path}')

	# print('calling the verification upload API')
	url = "https://ilocr.iiit.ac.in/verification/upload/"
	payload={'language': ver[0][0].page.language, 'category': ver[0][0].page.category}
	files=[
		('file',('test.zip',open(zip_path,'rb'),'application/zip'))
	]
	response = requests.post(url, data=payload, files=files)
	return response.ok


def send_to_editing(ver: list[tuple]):
	tmp = TemporaryDirectory(prefix='ver')
	# tmp = CustomDir(name='/home/annotation/test')
	folder = join(tmp.name, 'test')
	os.system('mkdir ' + folder)
	image_folder = join(folder, 'image')
	os.system('mkdir ' + image_folder)
	# print('setup the folder structure for the zip')
	ret = []
	for word, ocr in ver:
		os.system(f'cp {word.image.path} {image_folder}') # type: ignore
		ocr = '\t'.join(ocr)
		ret.append(f'image/{word.id}.jpg\t{ocr.strip()}') # type: ignore
	with open(join(folder, 'gt.txt'), 'w', encoding='utf-8') as f:
		f.write('\n'.join(ret))
	# print('added all the images and gt file to the folders')
	zip_path = join(tmp.name, 'test.zip')
	os.system(f'cd {tmp.name} && zip -r test.zip test/ >/dev/null && cd -')
	# print(f'created the zip file to be uploaded: {zip_path}')

	# print('calling the verification upload API')
	url = "https://ilocr.iiit.ac.in/editing/upload/"
	payload={'language': ver[0][0].page.language, 'category': ver[0][0].page.category}
	files=[
	  ('file',('test.zip',open(zip_path,'rb'),'application/zip'))
	]
	response = requests.post(url, data=payload, files=files)
	# print(f'Got the response as: {response.status_code}')
	return response.ok