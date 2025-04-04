import json
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import Lower
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from api.crowd import CrowdAPI
from core.tasks import perform_segment_bulk
from page.models import Page
from word.models import Word

from .helper import download_pages, handle_upload_zipfile
from .tasks import send_to_verification

User = get_user_model()


class BaseCoreView(LoginRequiredMixin):
    pass


class SegmentGTView(BaseCoreView, TemplateView):
    template_name = 'core/segment_gt.html'
    navigation = 'segment'

    def get_context_data(self, **kwargs):
        page_id = int(self.request.GET.get('page_id', 0))
        page = Page.objects.get(id=page_id)
        gt = 'No GT Available'
        try:
            if page.category == 'crowd_hw':
                gt = CrowdAPI.get_vocab(int(page.parent)) # type: ignore
            elif page.category == 'ilocr_crowd_hw':
                gt = CrowdAPI.get_ilocr_vocab(int(page.parent)) # type: ignore
        except:
            pass
        kwargs.update({
            'page': page,
            'gt': gt
        })
        return super().get_context_data(**kwargs)


class QCView(BaseCoreView, TemplateView):
    template_name = 'core/qc.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs.update({
            'page': Page.objects.filter(
                status='corrected',
                qc_status='',
            ).order_by('language').first()
        })
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        print(request.POST)
        page = Page.objects.get(id=request.POST.get('id'))
        if 'approve' in request.POST:
            page.approve(request.user)
        elif 'reject' in request.POST:
            page.reject(request.user)
        return redirect('core:qc')


class IndexView(BaseCoreView, TemplateView):
    template_name = 'core/index.html'
    navigation = 'segment'

    def post(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        page_id = int(self.request.GET.get('page_id', 0))
        if page_id and self.request.user.is_superuser: # type: ignore
            page = Page.objects.get(id=page_id)
        else:
            page = Page.objects.filter(
                status='assigned',
                user=self.request.user
            ).first()
        gt = 'No GT Available'
        try:
            if page.category == 'crowd_hw':
                gt = CrowdAPI.get_vocab(int(page.parent)) # type: ignore
            elif page.category == 'ilocr_crowd_hw':
                gt = CrowdAPI.get_ilocr_vocab(int(page.parent)) # type: ignore
        except:
            pass
        kwargs.update({
            'page': page,
            'gt': gt
        })
        return super().get_context_data(**kwargs)

@method_decorator(csrf_exempt, name='dispatch')
class SegmentSaveView(BaseCoreView, TemplateView):
    def post(self, request, *args, **kwargs):
        print('Got the data')
        data = json.loads(request.body.decode('utf-8'))
        page: Page = Page.objects.get(id=int(data['page_id']))
        print(int(data['page_id']))
        data = data['data']
        ndelete, _ = page.words.all().delete() # type: ignore
        print(f'Deleted {ndelete} words after annotation')

        Word.bulk_update_from_lsf(data, page)
        print('updated/created the remaining words')

        page.words.all().clean() # type: ignore
        page.words.all().update_cropped_images() # type: ignore	
        print('saved all word level cropped images')
        page.status = 'corrected'
        page.user = request.user
        page.corrected_timestamp = timezone.localtime()
        page.save()
        return redirect('core:index')


class SegmentSkipView(BaseCoreView, TemplateView):
    def get(self, request, *args, **kwargs):
        page_id = int(request.GET.get('page_id', 0))
        page = Page.objects.get(id=page_id)
        page.skip(request.user)
        return redirect('core:index')


@method_decorator(csrf_exempt, name='dispatch')
class UploadView(TemplateView):
    template_name = 'core/upload.html'
    navigation = 'upload'

    def post(self, *args, **kwargs):
        language = self.request.POST.get('language', 'hindi')
        category = self.request.POST['category']
        print(language, category)
        total, failed = handle_upload_zipfile(
            self.request.FILES['file'],
            language,
            category,
        )
        messages.success(
            self.request,
            f'Uploaded {total-failed} Page images. {failed} Failed.'
        )
        return redirect('core:upload')

    def get_context_data(self, **kwargs):
        language_list: list[list[str | int]] = [list(i) for i in Page.LANGUAGE_CHOICES]
        for i in language_list:
            i.append(Page.objects.filter(
                status='segmented',
                language=i[0]
            ).count())
        kwargs.update({
            'language_list': language_list,
            'category_list': Page.get_all_categories(),
        })
        return super().get_context_data(**kwargs)

class AssignView(BaseCoreView, TemplateView):
    template_name = 'core/assign.html'
    navigation = 'assign'

    def post(self, *args, **kwargs):
        user = User.objects.get(id=self.request.POST.get('user'))
        language = self.request.POST.get('language', '')
        category = self.request.POST.get('category')
        count = int(self.request.POST.get('count', 0))
        type = self.request.POST.get('type', 'rectangle')
        print(user, language, category, count, type)
        pages = Page.objects.filter(
            status='segmented',
            category=category,
        )
        if language:
            pages = pages.filter(language=language)
        if count:
            pages = pages[:count]
        assign_count = pages.count()
        pages.assign(user, type == 'polygon')
        messages.success(
            self.request,
            f'Assigned {assign_count} pages to {user}'
        )
        return redirect('core:assign')

    def get_context_data(self, **kwargs):
        language_list: list[list[str | int]] = [list(i) for i in Page.LANGUAGE_CHOICES]
        for i in language_list:
            i.append(Page.objects.filter(
                status='segmented',
                language=i[0]
            ).count())
        kwargs.update({
            'language_list': language_list,
            'user_list': User.objects.filter(
                groups__name='Annotater'
            ).order_by(Lower('username')),
            'category_list': Page.get_all_categories(),
        })
        return super().get_context_data(**kwargs)

class SegmentView(BaseCoreView, TemplateView):
    template_name = 'core/segment.html'
    navigation = 'segment'

    def post(self, *args, **kwargs):
        language = self.request.POST.get('language', '')
        category = self.request.POST.get('category')
        count = int(self.request.POST.get('count', 0))
        print(language, category, count)
        pages = Page.objects.filter(category=category, status='new')
        if language:
            pages = pages.filter(language=language)
        if count:
            pages = pages[:count]
        pages = list(pages.values_list('id', flat=True))
        perform_segment_bulk.delay(pages)
        messages.success(
            self.request,
            f'Performing Segmentation on {len(pages)} pages.'
        )
        return redirect('core:segment')

    def get_context_data(self, **kwargs):
        language_list: list[list[str | int]] = [list(i) for i in Page.LANGUAGE_CHOICES]
        for i in language_list:
            i.append(0)
        kwargs.update({
            'language_list': language_list,
            'category_list': Page.get_all_categories(status='new'),
        })
        return super().get_context_data(**kwargs)


class SendToVerificationView(BaseCoreView, TemplateView):
    template_name = 'core/send_to_verification.html'
    navigation = 'send_to_verification'

    def post(self, *args, **kwargs):
        language = self.request.POST.get('language', '')
        category = self.request.POST.get('category')
        status = self.request.POST.get('status')
        version = self.request.POST.get('version', 'v2')
        modality = self.request.POST.get('modality', 'printed')
        page_ids = list(Page.objects.filter(
            language=language,
            category=category,
            status=status
        ).values_list('id', flat=True))
        send_to_verification.delay(page_ids, version, modality)
        # count = Page.objects.filter(
        # 	language=language,
        # 	status=status,
        # 	category=category,
        # ).send_to_verification(version, modality) # type: ignore
        messages.success(
            self.request,
            f'Sent pages to the Verification portal'
        )
        return redirect('core:send-to-verification')

    def get_context_data(self, **kwargs):
        kwargs.update({
            'language_list': Page.LANGUAGE_CHOICES,
            'category_list': Page.get_all_categories(),
            'status_list': Page.STATUS_CHOICES,
        })
        return super().get_context_data(**kwargs)
    

class DownloadView(BaseCoreView, TemplateView):
    template_name = 'core/download.html'
    navigation = 'download'

    def post(self, *args, **kwargs):
        language = self.request.POST.get('language', '')
        category = self.request.POST.get('category')
        status = self.request.POST.get('status', 'segmented')
        include_gt = self.request.POST.get('include_gt') == 'on'
        include_visual = self.request.POST.get('include_visual') == 'on'
        use_parent = self.request.POST.get('use_parent') == 'on'
        print(status, language, category)
        if status == 'qc_approved':
            pages = Page.objects.filter(qc_status='approved')
        elif status == 'qc_rejected':
            pages = Page.objects.filter(qc_status='rejected')
        else:
            pages = Page.objects.filter(status=status)
        pages = pages.filter(category=category)
        if language:
            pages = pages.filter(language=language)
        messages.success(
            self.request,
            f'Downloaded {pages.count()} pages.'
        )
        return download_pages(
            pages,
            f'{category}-{status}',
            include_gt,
            include_visual,
            use_parent,
        )

    def get_context_data(self, **kwargs):
        kwargs.update({
            'language_list': [tuple(i) for i in Page.LANGUAGE_CHOICES],
            'status_list': [tuple(i) for i in Page.STATUS_CHOICES],
            'category_list': Page.get_all_categories(False),
        })
        return super().get_context_data(**kwargs)


class ConvertView(BaseCoreView, TemplateView):
    template_name = 'core/convert.html'
    navigation = 'convert'

    def post(self, *args, **kwargs):
        category = self.request.POST.get('category')
        language = self.request.POST.get('language', '')
        status = self.request.POST.get('status', 'segmented')
        convert_status = self.request.POST.get('convert_status', '')
        print(status, language, category, convert_status)
        pages = Page.objects.filter(category=category)
        if language:
            pages = pages.filter(language=language)
        if status:
            pages = pages.filter(status=status)
        page_count = pages.count()
        if convert_status and convert_status == 'delete':
            pages.delete()
            messages.success(
                self.request,
                f'Deleted {page_count} pages.'
            )
        elif convert_status:
            pages.update(status=convert_status)
            messages.success(
                self.request,
                f'converted {page_count} pages to {convert_status}.'
            )
        else:
            messages.success(
                self.request,
                f'Aborted. Please specify the convert status.'
            )
        return redirect('core:convert')

    def get_context_data(self, **kwargs):
        kwargs.update({
            'language_list': [tuple(i) for i in Page.LANGUAGE_CHOICES],
            'status_list': [tuple(i) for i in Page.STATUS_CHOICES],
            'category_list': Page.get_all_categories(False),
        })
        return super().get_context_data(**kwargs)