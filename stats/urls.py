from django.urls import path

from . import views

app_name = 'stats'
urlpatterns = [
	path('user/', views.UserStatsView.as_view(), name='user'),
	path('language/', views.LanguageStatsView.as_view(), name='language'),
	path('qc/', views.QCStatsView.as_view(), name='qc'),
]
