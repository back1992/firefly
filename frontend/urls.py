from __future__ import unicode_literals
from django.conf.urls import url
from . import views
from mezzanine.conf import settings

_slash = "/" if settings.APPEND_SLASH else ""

app_name = 'frontend'
urlpatterns = [
    url(r'^book_list/$', views.book_list, name='book_list'),
    url(r'^category/(?P<category>.*)%s$' % _slash, views.book_list_category, name="book_list_category"),
    url(r'^bookdetail/(?P<slug>.*)/(?P<chapter>.*)/(?P<position>.*)%s$' % _slash, views.book_detail,
        name='book_detail_position'),
    url(r'^bookdetail/(?P<slug>.*)%s$' % _slash, views.book_detail, name='book_detail'),
    url(r'^chapterlist/(?P<slug>.*)%s$' % _slash, views.chapter_list, name='chapter_list'),
    url(r'^myprofile/(?P<username>.*)%s$' % _slash, views.myprofile, name='myprofile'),
    url(r'^myprofile%s$' % _slash, views.myprofile, name='userprofile'),
    url("^search%s$" % _slash, views.search, name="search"),
]
