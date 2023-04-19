from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
	path('', views.SegmentView.as_view(), name='segment'),
	path('gt/', views.SegmentGTView.as_view(), name='segment-gt'),
	path('save/', views.SegmentSaveView.as_view(), name='segment-save'),
	path('skip/', views.SegmentSkipView.as_view(), name='segment-skip'),
	path('assign/', views.AssignView.as_view(), name='assign'),
	path('upload/', views.UploadView.as_view(), name='upload'),

	path('send_to_verification/', views.SendToVerificationView.as_view(), name='send-to-verification'),
]
