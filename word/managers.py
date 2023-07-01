import json
import os
import time
from os.path import basename, join
from tempfile import TemporaryDirectory
from typing import Any

from django.contrib.auth import get_user_model
from django.core.files import File
from PIL import Image

from api.crowd import CrowdAPI
from api.ocr import OCRAPI
from core.managers import BaseQuerySet

from .helper import send_to_editing, send_to_verification

User = get_user_model()


class WordQuerySet(BaseQuerySet):

	def cropped(self, **kwargs):
		return self.filter(
			status='cropped',
			**kwargs
		)

	def from_layout_response(
		self,
		layout_response: dict[str, Any],
		page,
		padding: int = 0,
		save: bool = True,
	) -> tuple[list, list]:
		Word = self.model
		Point = Word.points.field.model
		words = []
		points = []
		for region in layout_response['regions']:
			if 'bounding_box' in region:
				word = Word(
					page=page,
					line=region['line'],
					x=region['bounding_box']['x'] - padding,
					y=region['bounding_box']['y'] - padding,
					w=region['bounding_box']['w'] + padding,
					h=region['bounding_box']['h'] + padding,
				)
				words.append(word)
				points += word.update_points(save=False)
			else:
				point_list = []
				word = Word(
					page=page,
					line=region['line']
				)
				for i in region['points']:
					point_list.append(
						Point(
							word=word,
							x=i['x'],
							y=i['y'],
						)
					)
				x = [i.x for i in point_list]
				y = [i.y for i in point_list]
				word.x = min(x)
				word.y = min(y)
				word.w = max(x) - min(x)
				word.h = max(y) - min(y)
				words.append(word)
				points += point_list
		if save:
			Word.objects.bulk_create(words)
			Point.objects.bulk_create(points)
		return (words, points)

	def update_points(self):
		points = []
		for word in self.all():
			points += word.update_points(save=False)
		print('Performing DB Operation for creating points')
		if points:
			points[0]._meta.model.objects.bulk_create(points)


	def update_cropped_images(self) -> None:
		"""
		This is a pure function that updates all the words in the
		self queryset with the newly cropped image using the bbox.

		This function is called AFTER the annotater completes the bbox
		annotation for the paragraph, and all the words in the DB are
		updated with new x,y,w,h. So we call this function to delete
		the old word level cropped image and create a word crop
		using new bbox data
		"""
		if not self.exists():
			return None
		tmp = TemporaryDirectory(prefix='words')
		image = Image.open(self.all().first().page.image.path) # type: ignore
		image = image.convert('RGB')
		t = time.time()
		words = list(self.all())
		for word in words:
			location = join(tmp.name, f'{str(word.id)}.jpg')
			image.crop(word.get_crop_coords()).save(location)
		print(f'completed the cropping of images in {time.time()-t} sec')
		t = time.time()
		for word in words:
			location = join(tmp.name, f'{str(word.id)}.jpg')
			word.image.delete(False)
			word.image.save(
				basename(location),
				File(open(location, 'rb')),
				save=False
			)
		self.model.objects.bulk_update(words, ['image'])
		print(f'completed the saving of images in {time.time()-t} sec')

	def save_images(self, folder_path: str, as_id: bool = False) -> None:
		folder_path = folder_path.rstrip('/ ')
		for word in self.all():
			try:
				if as_id:
					os.system(f'cp {word.image.path} {folder_path}/{word.id}.jpg')
				else:
					os.system(f'cp {word.image.path} {folder_path}')
			except Exception:
				pass

	def perform_ocr(
			self,
			version: str = 'v2',
			modality: str = 'printed'
		) -> list[tuple[Any, str]]:
		"""Performs the OCR on all the words using ILOCR API.
		This function doesn't change any fields of the model, it simply
		performs the OCR and returns all the words and their OCR outputs

		Args:
			version (str, optional): OCR model version to call. Defaults to 'v2'.
			modality (str, optional): Modality of the model to call. Defaults to 'printed'.

		Returns:
			list[tuple[Any, str]]: This function returns the list of tuple
			containing 2 elements, one is the word (Word) object and other
			is the string ocr output received from the OCRAPI.
		"""
		if not self.exists():
			# Return empty is there are no words to process
			return []
		tmp = TemporaryDirectory(prefix='ocr')
		folder = tmp.name
		self.save_images(folder, as_id=True)
		a = OCRAPI.fire(
			folder,
			self.all()[0].page.language,
			modality=modality,
			version=version
		)

		words = list(self.all().order_by('id'))
		assert len(words) == len(a)
		ver: list[tuple] = []

		for word, bb in zip(words,a):
			ver.append((
				word,
				bb['text']
			))
		return ver

	def send_to_verification(self, ocr_version: str = 'v2', ocr_modality: str = 'printed') -> list:
		ver = self.all().perform_ocr(ocr_version, ocr_modality)
		send_to_verification(ver)
		return [i[0] for i in ver]


	def send_to_editing_verification(self) -> tuple[list, list]:
		"""
		This is a function to call the OCR of the words and send the
		words to editing or verification portal according to the
		OCR output of the words.
		"""
		if not self.exists():
			return ([], [])
		print(f'processing for {self.count()} words')
		tmp = TemporaryDirectory(prefix='ocr')
		folder = tmp.name
		parent = self.all()[0].page.parent
		self.save_images(folder, as_id=True)
		print('saved all the word images to the folder')
		vocab = CrowdAPI.get_vocab(parent)
		vocab = vocab.strip().replace('\n', ' ').strip().split(' ')
		print(f'Got the vocab from the crowdsource: {vocab}')
		a = OCRAPI.fire(folder, self.all()[0].page.language, incldue_prob=True)
		print('completed the OCR API')
		b = OCRAPI.fire_postprocess(a, self.all()[0].page.language, vocab)
		del a
		print('completed the postprocessing API')

		words = list(self.all().order_by('id'))
		assert len(words) == len(b), 'Some words were lost in postprocessing API'
		ver: list[tuple] = []
		edit: list[tuple] = []

		for word, bb in zip(words,b):
			if len(bb['text']) == 1:
				ver.append((
					word,
					bb['text'][0]
				))
			else:
				edit.append((
					word,
					tuple(bb['text'])
				))

		os.system(f'rm -rf {folder}/*')
		if ver:
			print(f'sending {len(ver)} words to verification')
			send_to_verification(ver)
			ver = [i[0] for i in ver]
		if edit:
			print(f'sending {len(edit)} words to editing')
			send_to_editing(edit)
			edit = [i[0] for i in edit]
		return (edit, ver)