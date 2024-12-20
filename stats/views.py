from datetime import date
from typing import Any, Optional

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, F, Q, Sum
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

    def get_date(self) -> date:
        requested_date = self.request.GET.get('date', '') # type: ignore
        if requested_date:
            requested_date = requested_date.strip('/ ').split('/')[::-1]
            requested_date = list(map(int, requested_date))
            requested_date = date(*requested_date)
        else:
            requested_date = date.today()
        return requested_date


class QCStatsView(BaseStatsView, TemplateView):
    template_name = 'stats/qc.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        category = self.request.GET.get('category', '')
        ret = Page.objects.all()
        if category:
            ret = ret.filter(category=category)
        ret = ret.values('language').annotate(
            name=F('language'),
            total_count=Count('id'),
            pending_count=Count('id', filter=Q(qc_status='')),
            approved_count=Count('id', filter=Q(qc_status='approved')),
            rejected_count=Count('id', filter=Q(qc_status='rejected')),
            # **self.create_count_annotations([
            # 	i[0] for i in Page.STATUS_CHOICES
            # ])
        )
        kwargs.update({
            'language_list': ret,
            'category': category,
            'category_list': Page.get_all_categories(),
        })
        print(kwargs)
        return super().get_context_data(**kwargs)


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
        if category == 'all':
            pass
        elif category == '':
            ret = ret.none()
        else:
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
        return super().get_context_data(**kwargs)


class MonthUserStatsView(BaseStatsView, TemplateView):
    template_name = 'stats/month_user.html'

    def get_context_data(self, **kwargs):
        requested_date = self.get_date()
        temp = Page.objects \
            .exclude(user=None) \
            .filter(corrected_timestamp__date__month=requested_date.month) \
            .filter(corrected_timestamp__date__year=requested_date.year) \
            .values('user') \
            .annotate(
                name=F('user__username'),
                id=F('user__id'),
                total_count=Count('id'),
                **self.create_count_annotations([
                    'segmented',
                    'corrected',
                    'skipped',
                    'sent',
                ])
            ).order_by('id')
        final_count = temp.aggregate(
            segmented_total=Sum('segmented_count'),
            corrected_total=Sum('corrected_count'),
            skipped_total=Sum('skipped_count'),
            sent_total=Sum('sent_count'),
            grand_total=Sum('total_count'),
        )
        ret = []
        for i in temp:
            x = dict(i)
            user = User.objects.get(pk=x['user'])
            x['last_activity'] = user.last_activity
            x['language'] = user.pages.order_by('corrected_timestamp').last().language # type: ignore
            x['category'] = user.pages.order_by('corrected_timestamp').last().category # type: ignore
            x['pk'] = user.pk
            ret.append(x)
        kwargs.update({
            'user_list': sorted(ret, key=lambda x:x['name'].lower()),
            'final_count': final_count
        })
        return super().get_context_data(**kwargs)

class MonthLanguageStatsView(BaseStatsView, TemplateView):
    template_name = 'stats/month_language.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        requested_date = self.get_date()
        category = self.request.GET.get('category', '')
        ret = Page.objects.all()
        if category:
            ret = ret.filter(category=category)
        ret = ret.filter(
            corrected_timestamp__date__month=requested_date.month,
            corrected_timestamp__date__year=requested_date.year,
        )
        ret = ret.values('language').annotate(
            name=F('language'),
            total_count=Count('id'),
            **self.create_count_annotations([
                'segmented',
                'corrected',
                'skipped',
                'sent',
            ])
        )
        kwargs.update({
            'language_list': ret,
            'category': category,
            'category_list': Page.get_all_categories(),
            'requested_date': '{}%2F{}%2F{}'.format(
                requested_date.day,
                requested_date.month,
                requested_date.year
            )
        })
        return super().get_context_data(**kwargs)

class DayStatsView(BaseStatsView, TemplateView):
    template_name = 'stats/day.html'

    def get_context_data(self, **kwargs):
        requested_date = self.get_date()
        temp = Page.objects \
            .exclude(user=None) \
            .filter(corrected_timestamp__date=requested_date) \
            .values('user') \
            .annotate(
                name=F('user__username'),
                id=F('user__id'),
                total_count=Count('id'),
                **self.create_count_annotations([
                    'corrected',
                    'skipped'
                ])
            ).order_by('id')
        final_count = temp.aggregate(
            corrected_total=Sum('corrected_count'),
            skipped_total=Sum('skipped_count'),
            grand_total=Sum('total_count'),
        )
        ret = []
        for i in temp:
            x = dict(i)
            user = User.objects.get(pk=x['user'])
            x['last_activity'] = user.last_activity
            x['language'] = user.pages.order_by('corrected_timestamp').last().language # type: ignore
            x['category'] = user.pages.order_by('corrected_timestamp').last().category # type: ignore
            x['pk'] = user.pk
            ret.append(x)
        kwargs.update({
            'user_list': sorted(ret, key=lambda x:x['name'].lower()),
            'final_count': final_count
        })
        return super().get_context_data(**kwargs)
