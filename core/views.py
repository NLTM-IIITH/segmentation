import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from api.crowd import CrowdAPI
from page.models import Page
from word.models import Word

from .helper import handle_upload_zipfile

User = get_user_model()


class BaseCoreView(LoginRequiredMixin):
	pass


class SegmentGTView(BaseCoreView, TemplateView):
	template_name = 'core/segment_gt.html'
	navigation = 'segment'

	def get_context_data(self, **kwargs):
		page_id = int(self.request.GET.get('page_id', 0))
		page = Page.objects.get(id=page_id)
		try:
			gt = CrowdAPI.get_vocab(int(page.parent))
		except:
			gt = 'No GT Available'
		kwargs.update({
			'page': page,
			'gt': gt
		})
		return super().get_context_data(**kwargs)


class SegmentView(BaseCoreView, TemplateView):
	template_name = 'core/segment.html'
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
		try:
			gt = CrowdAPI.get_vocab(int(page.parent)) # type: ignore
		except:
			gt = 'No GT Available'
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
		data = data['data']
		ndelete, _ = page.words.all().delete() # type: ignore
		print(f'Deleted {ndelete} words after annotation')

		Word.bulk_update_from_lsf(data, page)
		print('updated/created the remaining words')

		page.words.all().update_cropped_images() # type: ignore	
		print('saved all word level cropped images')
		page.status = 'corrected'
		page.user = request.user
		page.corrected_timestamp = timezone.localtime()
		page.save()
		return redirect('core:segment')


class SegmentSkipView(BaseCoreView, TemplateView):
	def get(self, request, *args, **kwargs):
		page_id = int(request.GET.get('page_id', 0))
		page = Page.objects.get(id=page_id)
		page.skip(request.user)
		return redirect('core:segment')


class UploadView(BaseCoreView, TemplateView):
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
			separator='\t'
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
		Page.objects.filter(
			language=language,
			status='segmented',
			category=category,
		)[:count].assign(user, type == 'polygon') # type: ignore
		messages.success(
			self.request,
			f'Assigned {count} pages to {user}'
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
			'user_list': User.objects.filter(groups__name='Annotater'),
			'category_list': Page.get_all_categories(),
		})
		return super().get_context_data(**kwargs)


class SendToVerificationView(BaseCoreView, TemplateView):
	template_name = 'core/send_to_verification.html'
	navigation = 'send_to_verification'

	def post(self, *args, **kwargs):
		language = self.request.POST.get('language', '')
		category = self.request.POST.get('category')
		status = self.request.POST.get('status')
		count = Page.objects.filter(
			language=language,
			status=status,
			category=category,
		).send_to_verification() # type: ignore
		messages.success(
			self.request,
			f'Sent {count} pages to the Verification portal'
		)
		return redirect('core:send-to-verification')

	def get_context_data(self, **kwargs):
		kwargs.update({
			'language_list': Page.LANGUAGE_CHOICES,
			'category_list': Page.get_all_categories(),
			'status_list': Page.STATUS_CHOICES,
		})
		return super().get_context_data(**kwargs)
	