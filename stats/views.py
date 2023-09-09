from typing import Any, Optional

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, F, Q
from django.views.generic import TemplateView

from page.models import Page
from user.models import User


class BaseStatsView(LoginRequiredMixin, UserPassesTestMixin):
	navigation = 'stats'

	def test_func(self) -> Optional[bool]:
		return self.request.user.is_staff # type: ignore

	def create_count_annotations(self, fields: list[str]) -> dict[str, Any]:
		ret = {}
		for i in fields:
			ret[f'{i}_count'] = Count(
				'id',
				filter=Q(status=i)
			)
		return ret


class UserStatsView(BaseStatsView, TemplateView):
	template_name = 'stats/user.html'

	def get_context_data(self, **kwargs):
		temp = Page.objects \
			.exclude(user=None) \
			.values('user') \
			.annotate(
				name=F('user__username'),
				total_count=Count('id'),
				**self.create_count_annotations([
					'assigned',
					'corrected',
					'skipped'
				])
			)
		ret = []
		for i in temp:
			x = dict(i)
			user = User.objects.get(pk=x['user'])
			x['last_activity'] = user.last_activity
			x['language'] = user.pages.first().language # type: ignore
			x['pk'] = user.pk
			ret.append(x)
		kwargs.update({
			'user_list': sorted(ret, key=lambda x:x['name'].lower())
		})
		return super().get_context_data(**kwargs)


class LanguageStatsView(BaseStatsView, TemplateView):
	template_name = 'stats/language.html'

	def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
		category = self.request.GET.get('category', '')
		ret = Page.objects.all()
		if category:
			ret = ret.filter(category=category)
		ret = ret.values('language').annotate(
			name=F('language'),
			total_count=Count('id'),
			**self.create_count_annotations([
				i[0] for i in Page.STATUS_CHOICES
			])
		)
		kwargs.update({
			'language_list': ret,
			'category': category,
			'category_list': Page.get_all_categories(),
		})
		print(kwargs)
		return super().get_context_data(**kwargs)