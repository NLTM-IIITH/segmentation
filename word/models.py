from os.path import join

from django.contrib.auth import get_user_model
from django.db import models
from PIL import Image

from core.models import BaseModel

from .managers import WordQuerySet

User = get_user_model()

def get_image_path(instance, filename):
	return join(
		'Words',
		str(instance.page.category),
		str(instance.page.language),
		filename
	)


class Word(BaseModel):

	STATUS_CHOICES = (
		('new', 'New'),
		('cropped', 'Cropped'),
		('sent_editing', 'Sent to Editing'),
		('sent_verification', 'Sent to Verification'),
	)

	objects = WordQuerySet.as_manager()

	page = models.ForeignKey(
		'page.Page',
		on_delete=models.CASCADE,
	)

	image = models.ImageField(
		verbose_name='Word Image',
		help_text='original word level cropped image',
		null=True,
		blank=True,
		upload_to=get_image_path,
	)
	x = models.IntegerField(default=0)
	y = models.IntegerField(default=0)
	w = models.IntegerField(default=0)
	h = models.IntegerField(default=0)
	line = models.IntegerField(default=0)

	status = models.CharField(
		max_length=50,
		choices=STATUS_CHOICES,
		default='new',
	)

	class Meta:
		default_related_name = 'words'

	def __repr__(self) -> str:
		return f'<Word: {self.status}>'

	def convert_bbox_to_percentage(self):
		"""
		Converts the absolute x,y,w,h pixelvalues to percent of total 
		width and height of the original image.
		"""
		image = Image.open(self.page.image.path)
		width, height = image.width, image.height
		x = round(self.x / width * 100, 2)
		y = round(self.y / height * 100, 2)
		w = round(self.w / width * 100, 2)
		h = round(self.h / height * 100, 2)
		return (x,y,w,h)


	def get_value(self):
		"""
		function that is used by Page.get_annotations to get the proper
		value of each of the word.
		returns the json object as expected by the labelstudio frontend
		"""
		x,y,w,h = self.convert_bbox_to_percentage()
		return {
			'id': str(self.id), # type: ignore
			'source': '$image',
			'from_name': 'tag',
			'to_name': 'img',
			'type': 'rectanglelabels',
			'value': {
				'x': x,
				'y': y,
				'width': w,
				'height': h,
				'rectanglelabels': ['BBOX'],
			}
		}

	def get_crop_coords(self) -> tuple[int, int, int, int]:
		x1 = self.x
		x2 = self.x + self.w
		y1 = self.y
		y2 = self.y + self.h
		return (x1, y1, x2, y2)

	def update_from_lsf(self, data, save=True):
		"""
		this function takes as input the data object returned by the LSF
		for this particular word model instance.
		"""
		width, height = data['original_width'], data['original_height']
		self.x = (data['value']['x'] * width) // 100
		self.y = (data['value']['y'] * height) // 100
		self.w = (data['value']['width'] * width) // 100
		self.h = (data['value']['height'] * height) // 100
		if save:
			self.save()

	@staticmethod
	def bulk_update_from_lsf(data, page) -> None:
		data_dict = {i['id']:i for i in data}
		ids = [i['id'] for i in data]
		words = []
		for i in range(len(ids)):
			words.append(
				Word(
					page=page,
				)
			)
		Word.objects.bulk_create(words)
		print(f'Created {len(words)} word model placeholders')
		words = list(Word.objects.filter(page=page))
		for i in range(len(ids)):
			words[i].update_from_lsf(data_dict[ids[i]], save=False)
		Word.objects.bulk_update(words, ['x', 'y', 'w', 'h'])
		print('completed creating and updating new words')