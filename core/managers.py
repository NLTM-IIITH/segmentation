from django.db.models import Count, QuerySet


class BaseQuerySet(QuerySet):

	def group(self, field: str, filter=None):
		return self.values(field).annotate(c=Count('id'))

	def refresh(self):
		ids = [i.id for i in self.all()]
		return self.model.objects.filter(id__in=ids)