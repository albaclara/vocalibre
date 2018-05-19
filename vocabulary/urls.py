from django.urls import include, path
from django.conf.urls import url
from . import views


urlpatterns = [
    url('^/?$', views.ChooseLanguage, name="choose_language"),
    url('^(?P<langApr>\w+)/choosetrans/?$', views.ChooseTranslation, name="choose_translation"),
    url('^(?P<langApr>\w+)/(?P<langUt>\w+)/subject/?$', views.ChooseSubject, name="choose_subject"),
    url('^(?P<langApr>\w+)/(?P<langUt>\w+)/(?P<subject>\w+)/?$', views.DisplayWords, name="display_words"),
]
