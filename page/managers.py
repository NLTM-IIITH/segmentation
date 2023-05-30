from django.contrib.auth import get_user_model
from tqdm import tqdm

from core.managers import BaseQuerySet

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