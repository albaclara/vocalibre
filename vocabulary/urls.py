from django.urls import include, path
from django.conf.urls import url
from . import views


urlpatterns = [
    url('^/?$', views.ChooseLanguage, name="choose_language"),
    url('^(?P<lang>\w+)/subject/?$', views.ChooseSubject, name="choose_theme"),
    url('^(?P<lang>\w+)/(?P<subject>\w+)/?$', views.DisplayWords, name="display_words"),
]
