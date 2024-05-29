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
from django.views.generic import ListView

from api.crowd import CrowdAPI
from core.tasks import perform_segment_bulk
from page.models import Page
from word.models import Word

User = get_user_model()


class BasePageView(LoginRequiredMixin):
    model = Page


class PageListView(BasePageView, ListView):
    pass