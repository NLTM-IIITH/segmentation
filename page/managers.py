import os
from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib.auth import get_user_model
from tqdm import tqdm

from api.layout import LayoutAPI
from core.managers import BaseQuerySet
from word.models import Word

User = get_user_model()


class PageQuerySet(BaseQuerySet):

	def assigned(self, **kwargs):
		return self.filter(
			status='assigned',
			**kwargs
		)

	def assign(self, user: 'User', polygon: bool) -> None: # type: ignore
		"""
		Assigns all the pages in QuerySet to the given user
		and updates the assigned_timstamp of all the pages.

		Effected Fields:
		 - Page.status
		 - Page.polygon
		 - Page.user
		 - Page.assigned_timestamp
		"""
		pages = list(self.all())
		print(f'Assigning {user} to {self.count()} pages')
		for page in pages:
			page.assign(user, polygon, save=False)
		self.model.objects.bulk_update(
			pages,
			('user', 'polygon', 'assigned_timestamp', 'status')
		)

	def unassign(self) -> None:
		"""
		Removes the assigned status for all the pages.

		Effected Fields:
		 - Page.status
		 - Page.user
		"""
		self.all().assigned().update(
			status='segmented',
			user=None
		)

	def save_images(self, path: str) -> str:
		for page in tqdm(self.all(), desc='Saving Images'):
			page.save_image(path)
		return path

	def segment_single_batch(self):
		pages = self.all().refresh()
		Word.objects.filter(page__in=pages).delete()
		tmp = TemporaryDirectory(prefix='segment')
		self.save_images(tmp.name)
		model = settings.PAGE_CATEGORY_SEGMENTATION_MODEL.get(pages[0].category, 'v2_doctr')
		words = LayoutAPI().fire(tmp.name, model)
		word_list = []
		point_list = []
		for word in tqdm(words, desc='Parsing Layout output'):
			wl, pl = Word.objects.from_layout_response( # type: ignore
				word,
				pages.get(id=int(word['image_name'].split('.')[0].strip())),
				# self,
				padding=0,
				save=False
			)
			word_list += wl
			point_list += pl
		Word.objects.bulk_create(word_list)
		Word.points.field.model.objects.bulk_create(point_list) # type: ignore
		pages.update(status='segmented')

	def segment_bulk(self, batch_size: int = 50):
		pages = self.all()
		batch_pages = [pages[i:i+batch_size] for i in range(0, pages.count(), batch_size)]
		for batch in tqdm(batch_pages, desc=f'Performing Segment {batch_size} at a time'):
			batch.segment_single_batch()


	def segment(self) -> int:
		"""
		Performs the layout parser on the bunch of pages and segment
		the pages as well.
		returns the number of successfull segmented pages

		Effected Fields:
		 - Page.status
		"""
		count = 0
		for page in tqdm(self.all()):
			try:
				page.segment()
				count += 1
			except:
				print(f'Encounter error while segmenting {repr(page)}')
		return count
	
	def send_to_verification(self):
		"""
		This is function to send all the words to verification portal.
		"""
		for i in tqdm(self.all()):
			i.send_to_verification()