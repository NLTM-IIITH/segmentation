import json
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View

from api.crowd import CrowdAPI
from core.tasks import perform_segment_bulk
from page.models import Page
from word.models import Word

from .helper import download_pages, handle_upload_zipfile
from .tasks import send_to_verification

User = get_user_model()


class BaseCoreView(LoginRequiredMixin):
	pass

@method_decorator(csrf_exempt, name='dispatch')
class UploadView(View):

	def post(self, *args, **kwargs):
		data = json.loads(self.request.body)
		if len(data) == 0:
			return HttpResponse('No Data found')
