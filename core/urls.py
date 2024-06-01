from django.urls import path

from . import api_views, views

app_name = 'core'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('gt/', views.SegmentGTView.as_view(), name='segment-gt'),
    path('save/', views.SegmentSaveView.as_view(), name='segment-save'),
    path('skip/', views.SegmentSkipView.as_view(), name='segment-skip'),
    path('assign/', views.AssignView.as_view(), name='assign'),
    path('upload/', views.UploadView.as_view(), name='upload'),
    path('segment/', views.SegmentView.as_view(), name='segment'),
    path('download/', views.DownloadView.as_view(), name='download'),

    path('qc/', views.QCView.as_view(), name='qc'),

    path('send_to_verification/', views.SendToVerificationView.as_view(), name='send-to-verification'),

    path('api/upload/', api_views.UploadView.as_view(), name='api-upload'),
    path('api/fetch/', api_views.FetchView.as_view(), name='api-fetch'),
]
