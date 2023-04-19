from django.db.models import Count, QuerySet


class BaseQuerySet(QuerySet):

	def group(self, field: str, filter=None):
		return self.values(field).annotate(c=Count('id'))