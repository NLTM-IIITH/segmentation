import base64
import shutil
from os.path import basename, join
from tempfile import TemporaryDirectory

import cv2
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone
from PIL import Image

from api.layout import LayoutAPI
from core.models import BaseModel
from word.models import Word

from .managers import PageQuerySet

User = get_user_model()

def get_image_path(instance, filename):
	return join(
		'Pages',
		str(instance.category),
		str(instance.language),
		filename
	)


class Page(BaseModel):

	STATUS_CHOICES = (
		('new', 'New'),
		('segmented', 'Segmented'),
		('assigned', 'Assigned'),
		('corrected', 'Corrected'),
		('skipped', 'Skipped'),
		# this implies that the page has been processed and all the words
		# of this page are either sent to verification or editing
		('sent', 'Sent'),
	)
	QC_STATUS_CHOICES = (
		('', ''),
		('approved', 'Approved'),
		('rejected', 'Rejected'),
	)
	LANGUAGE_CHOICES = (
		('', 'Select Language'),
		('assamese', 'Assamese'),
		('bengali', 'Bengali'),
		('english', 'English'),
		('gujarati', 'Gujarati'),
		('hindi', 'Hindi'),
		('kannada', 'Kannada'),
		('malayalam', 'Malayalam'),
		('manipuri', 'Manipuri'),
		('marathi', 'Marathi'),
		('oriya', 'Oriya'),
		('punjabi', 'Punjabi'),
		('tamil', 'Tamil'),
		('telugu', 'Telugu'),
		('urdu', 'Urdu'),

		# Extra languages
		('bodo', 'Bodo'),
		('dogri', 'Dogri'),
		('konkani', 'Konkani'),
		('kashmiri', 'Kashmiri'),
		('maithili', 'Maithili'),
		('nepali', 'Nepali'),
		('sindhi', 'Sindhi'),
		('santali', 'Santali'),
		('sanskrit', 'Sanskrit'),
	)

	objects = PageQuerySet.as_manager()

	image = models.ImageField(
		verbose_name='Page Image',
		help_text='original page image',
		null=True,
		blank=True,
		upload_to=get_image_path,
	)
	category = models.CharField(
		default='',
		max_length=40,
	)

	status = models.CharField(
		max_length=10,
		choices=STATUS_CHOICES,
		default='new',
	)

	qc_status = models.CharField(
		max_length=15,
		choices=QC_STATUS_CHOICES,
		help_text=(
			'This status is stands for Quality Check Status '
			'Defines whether a page is approved or rejected upon '
			'showing to a verifier after segmentation editing.'
		),
		default='',
	)
	language = models.CharField(
		max_length=20,
		choices=LANGUAGE_CHOICES,
		default='',
	)

	user = models.ForeignKey(
		User,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		default=None,
		help_text='Indicates the user that corrects this pages segmentation'
	)

	parent = models.CharField(
		default='',
		max_length=100,
		help_text='This field stores the ID or information of the source of the page'
	)

	polygon = models.BooleanField(
		default=False,
		help_text=(
			'This indicates that when the page is showed for '
			'segmentation to the user, polygon will decide whether '
			'to show the label studio in the form of rectangle or polygons'
		)
	)

	assigned_timestamp = models.DateTimeField(
		default=None,
		null=True,
		blank=True,
	)
	corrected_timestamp = models.DateTimeField(
		default=None,
		null=True,
		blank=True,
	)
	sent_timestamp = models.DateTimeField(
		default=None,
		null=True,
		blank=True,
	)
	qc_timestamp = models.DateTimeField(
		default=None,
		null=True,
		blank=True,
	)


	class Meta:
		default_related_name = 'pages'

	def __repr__(self) -> str:
		return f'<Page: {self.status.title()}>'

	def assign(self, user: "User", polygon: bool, save: bool = True): # type: ignore
		"""
		Assigns a user to this page.

		Effected Fields
		 - Page.status
		 - Page.polygon
		 - Page.user
		 - Page.assigned_timestamp
		"""
		self.user = user
		self.polygon = polygon
		self.status = 'assigned'
		self.assigned_timestamp = timezone.localtime()
		if save:
			self.save()

	def segment(self) -> None:
		"""
		Perform the layout parser and updates the Page

		Effected Fields
		 - Page.status
		"""
		self.perform_layout_parser()
		self.status = 'segmented'
		self.save()

	def skip(self, user):
		"""
		Skips this page

		Effected Fields
		 - Page.status
		 - Page.corrected_timestamp
		 - Page.user
		"""
		self.status = 'skipped'
		self.corrected_timestamp = timezone.localtime()
		self.user = user
		self.save()

	def send_to_verification(self, ocr_version: str = '', ocr_modality: str = 'printed'):
		if not ocr_version:
			ocr_version = settings.PAGE_CATEGORY_OCR_VERIFICATION_MODEL[self.category]
		ver = self.words.all().send_to_verification( # type: ignore
			ocr_version,
			ocr_modality
		)
		ver = [i.id for i in ver]
		Word.objects.filter(id__in=ver).update(status='sent_verification')
		self.status = 'sent'
		self.save()
		return ver

	def send_to_editing_verification(self):
		"""
		This function sends all the words of this to editing or verification

		Effected Fields
		 - Page.status
		 - Page.sent_timestamp
		 - Page.words.status
		"""
		assert self.status == 'corrected', 'Only corrected pages can be processed'
		assert self.category == 'crowd_hw', 'This facility only available for crowd source for now'
		edit, ver = self.words.all().send_to_editing_verification() # type: ignore
		if edit:
			edit = [i.id for i in edit]
			Word.objects.filter(id__in=edit).update(status='sent_editing')
		if ver:
			ver = [i.id for i in ver]
			Word.objects.filter(id__in=ver).update(status='sent_verification')
		self.status = 'sent'
		self.sent_timestamp = timezone.localtime()
		self.save()

	def export(self, image_path: str, gt_path: str):
		self.save_image(image_path)
		ret = []
		for i in self.words.all():
			ret.append(f'{i.x}\t{i.y}\t{i.w}\t{i.h}')
		with open(join(gt_path, f'{self.id}.txt'), 'w', encoding='utf-8') as f:
			f.write('\n'.join(ret))

	@transaction.atomic
	def get_annotations(self):
		"""
		function to retrieve all the word annotations for the this job.
		assumes that this page has already been Segmented.
		returns a json object with all the prior annotations in the format
		that is compatible with the label studio frontend.
		"""
		ret = self.words.all() # type: ignore
		ret = [i.get_value() for i in ret]
		ret = {
			'id': '1001',
			'result': ret,
		}
		return ret

	def save_image(self, path: str) -> str:
		"""
		fetches the original page, crop out the region part 
		and save the region image in the specified path
		"""
		path = join(path, f'{self.id}.jpg') # type: ignore
		img = Image.open(self.image.path)
		img.convert('RGB').save(path)
		return path

	def perform_layout_parser(self):
		"""
		Perform the layout parser for all the regions denoted by this queryset
		"""
		self.words.all().delete() # type: ignore
		tmp = TemporaryDirectory(prefix='layout')
		self.save_image(tmp.name)
		model = settings.PAGE_CATEGORY_SEGMENTATION_MODEL.get(self.category, 'v2_doctr')
		words = LayoutAPI().fire(tmp.name, model)
		for word in words:
			Word.objects.from_layout_response( # type: ignore
				word,
				self,
				padding=0,
			)

	@staticmethod
	def get_all_categories(**kwargs) -> list[tuple[str, int]]:
		ret = Page.objects.filter(**kwargs)
		ret = ret.values_list('category', flat=True).distinct()
		ret = [[i] for i in ret]
		for i in ret:
			i.append(Page.objects.filter(
				category=i[0],
				**kwargs
			).count())
		ret = [tuple(i) for i in ret]
		return ret

	@transaction.atomic
	def approve(self):
		self.qc_status = 'approved'
		self.qc_timestamp = timezone.localtime()
		self.save()

	@transaction.atomic
	def reject(self):
		self.qc_status = 'rejected'
		self.qc_timestamp = timezone.localtime()
		self.save()

	def get_highlighted_base64_image(self) -> str:
		"""
		creates the line segment image and saves in the model from the
		data saved in model of the page object
		"""
		tmp_dir = TemporaryDirectory(prefix='highlight')
		folder = tmp_dir.name
		shutil.copy(self.image.path, folder)
		image = join(folder, basename(self.image.path))
		img = cv2.imread(image)

		alpha = 0.3
		color = (255,0,0)
		for word in self.words.all():
			overlay = img.copy()
			cv2.rectangle(
				overlay,
				(word.x, word.y),
				(word.x + word.w, word.y + word.h),
				color,
				-1
			)
			cv2.addWeighted(overlay, alpha, img, 1-alpha, 0, img)
		cv2.imwrite(image, img)
		return base64.b64encode(open(image, 'rb').read()).decode()