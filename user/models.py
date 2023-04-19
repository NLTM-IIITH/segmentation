from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

	mobile = models.CharField(
		default='',
		max_length=10,
	)

	@property
	def assigned_count(self) -> int:
		"""
		Returns the number of Pages currently assigned to this user.
		"""
		return self.pages.filter(status='assigned').count() # type: ignore

	@property
	def last_activity(self):
		"""
		Returns the datetime of the last page segmented by user.
		"""
		return self.pages.order_by('-corrected_timestamp')[0].corrected_timestamp # type: ignore

	def unassign(self):
		"""
		Unassigns all the pages that are currently assigned to the user.

		Effected Fields:
		 - Page.status
		 - Page.user
		"""
		self.pages.assigned().unassign() # type: ignore