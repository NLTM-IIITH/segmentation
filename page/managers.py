import os
from os.path import join
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

	def export(self, path: str, include_gt: bool = True, include_visual: bool = False, use_parent: bool = False):
		image_folder = gt_folder = visual_folder = ''
		image_folder = join(path, 'images')
		if not os.path.exists(image_folder):
			os.makedirs(image_folder)
		if include_gt:
			gt_folder = join(path, 'gt')
			if not os.path.exists(gt_folder):
				os.makedirs(gt_folder)
		if include_visual:
			visual_folder = join(path, 'visualization')
			if not os.path.exists(visual_folder):
				os.makedirs(visual_folder)
		for i in tqdm(self.all()):
			i.export(image_folder, gt_folder, visual_folder, use_parent)

	def export_all_language(self, path: str, include_gt: bool = True, include_visual: bool = False, use_parent: bool = False):
		language_list = self.all().values_list('language', flat=True).distinct()
		print(f'Found {len(language_list)} languages in the Queryset')
		for language in language_list:
			if not os.path.exists(join(path, language)):
				os.makedirs(join(path, language))
			self.filter(language=language).export(
				join(path, language),
				include_gt,
				include_visual,
				use_parent
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

	def save_images(self, path: str) -> list[int]:
		ret = []
		for page in tqdm(self.all(), desc='Saving Images'):
			if not page.save_image(path):
				ret.append(page.id)
		return ret

	def segment_single_batch(self):
		pages = self.all().refresh()
		if not pages.exists():
			return None
		Word.objects.filter(page__in=pages).delete()
		tmp = TemporaryDirectory(prefix='segment')
		error_pages = self.save_images(tmp.name)
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
		pages.exclude(id__in=error_pages).update(status='segmented')

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
	
	def send_to_verification(self, ocr_version: str = '', ocr_modality: str = 'printed'):
		"""
		This is function to send all the words to verification portal.
		"""
		for i in tqdm(self.all(), desc='Sending to Verification Portal'):
			i.send_to_verification(ocr_version, ocr_modality)