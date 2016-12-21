# -*- coding: utf-8 -*-
import os

import django
from audiofield.fields import AudioField
from django.conf import settings
from django.db import models
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.six import python_2_unicode_compatible
from mezzanine.blog.models import BlogCategory, BlogPost
from mezzanine.core.managers import SearchableManager
from django.utils.translation import ugettext_lazy as _
from mezzanine.core.fields import RichTextField, OrderField
from django.contrib.contenttypes.fields import GenericRelation
from hitcount.models import HitCount, HitCountMixin
from ordered_model.models import OrderedModel
# from durationfield.db.models.fields.duration import DurationField
from django.db.models.fields import DurationField


@python_2_unicode_compatible  # only if you need to support Python 2
class Publisher(models.Model):
    name = models.CharField(max_length=30, verbose_name=u"名称")
    website = models.URLField(verbose_name=u"网址")

    def __str__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = u'出版社'
        verbose_name_plural = u'出版社'


@python_2_unicode_compatible  # only if you need to support Python 2
class UserProfile(models.Model):
    user = models.OneToOneField("auth.User", related_name='profile')
    avatar = models.ImageField(upload_to='avatar', blank=True)
    bio = models.TextField()
    # address = models.OneToOneField("Address", null=True)

    SHIRT_SIZES = (
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
    )

    shirt_size = models.CharField(max_length=1, choices=SHIRT_SIZES, default='S')

    def __str__(self):
        return str(self.user)

    class Meta:
        verbose_name = u'会员管理'
        verbose_name_plural = u'会员管理'


@python_2_unicode_compatible  # only if you need to support Python 2
class Author(models.Model):
    english_name = models.CharField(max_length=30, null=True, verbose_name=u"英文姓名", unique=True)
    chinese_name = models.CharField(max_length=40, null=True, verbose_name=u"中文姓名")
    country = models.CharField(max_length=40, null=True, verbose_name=u"国家")
    description = models.TextField(verbose_name=u"作者简介")
    objects = SearchableManager()
    search_fields = ("english_name", "chinese_name")

    def __str__(self):
        return self.english_name + '---' + self.chinese_name

    class Meta:
        verbose_name = u'作者'
        verbose_name_plural = u'作者'


@python_2_unicode_compatible  # only if you need to support Python 2
class BookCategory(OrderedModel, BlogCategory):
    cover = models.ImageField(upload_to="categories", verbose_name=u"图片", null=True)
    npid = models.CharField(max_length=30, null=True, default='npid')
    # order = models.PositiveIntegerField(default=0, blank=False, null=False)

    def image_tag(self):
        return mark_safe('<img src="/static/media/%s" width="80" height="80" />' % (self.cover))

    image_tag.short_description = 'Cover'

    # order_with_respect_to = 'my_order'
    # order_field_name = 'my_order'

    class Meta(OrderedModel.Meta):
        # ordering = ['category_order']
        verbose_name = u'书籍分类'
        verbose_name_plural = u'书籍分类'
        # ordering = ('my_order',)

    models.Model._admin_url_name = lambda self, type: 'admin:%s_%s_%s' % (
        # self._meta.app_label, self._meta.module_name, type)
        self._meta.app_label, self._meta.object_name.lower(), type)

    def get_admin_change_url(self):
        return reverse(self._admin_url_name('change'), args=(self.pk,))

    models.Model.get_admin_change_url = get_admin_change_url

    def get_admin_delete_url(self):
        return reverse(self._admin_url_name('delete'), args=(self.pk,))

    models.Model.get_admin_delete_url = get_admin_delete_url

    def get_admin_history_url(self):
        return reverse(self._admin_url_name('history'), args=(self.pk,))

    models.Model.get_admin_history_url = get_admin_history_url

    def get_admin_changelist_url(self):
        return reverse(self._admin_url_name('changelist'))

    models.Model.get_admin_changelist_url = get_admin_changelist_url

    def get_admin_add_url(self):
        return reverse(self._admin_url_name('add'))

    models.Model.get_admin_add_url = get_admin_add_url

    models.Model.get_verbose_name = lambda self: self._meta.verbose_name
    models.Model.get_verbose_name_plural = lambda self: self._meta.verbose_name_plural

    def __str__(self):
        return str(self.title)


BookCategory._meta.get_field('title').verbose_name = u'分类名称'


@python_2_unicode_compatible  # only if you need to support Python 2
class Book(BlogPost, HitCountMixin):
    titlezh = models.CharField(max_length=100, null=True, verbose_name=u"中文书名")
    isbn = models.CharField(max_length=100, null=True, verbose_name="ISBN")
    author = models.ForeignKey("Author", verbose_name=u"作者")
    # cover = models.ImageField(upload_to="books", verbose_name=u"图片")
    publisher = models.ForeignKey(Publisher, null=True, verbose_name=u"出版社")
    npid = models.CharField(max_length=30, null=True, default='npid')
    publication_date = models.DateField(null=True, verbose_name=u"出版日期")
    hit_count_generic = GenericRelation(
        HitCount, object_id_field='object_pk',
        related_query_name='hit_count_generic_relation')

    # is_published = models.BooleanField(default=False, verbose_name=u"上架")

    class Meta:
        verbose_name = u'图书'
        verbose_name_plural = u'图书'

    def get_absolute_url(self):
        """
        URLs for blog posts can either be just their slug, or prefixed
        with a portion of the post's publish date, controlled by the
        setting ``BLOG_URLS_DATE_FORMAT``, which can contain the value
        ``year``, ``month``, or ``day``. Each of these maps to the name
        of the corresponding urlpattern, and if defined, we loop through
        each of these and build up the kwargs for the correct urlpattern.
        The order which we loop through them is important, since the
        order goes from least granular (just year) to most granular
        (year/month/day).
        """
        url_name = "book_detail"
        # print(self.get_slug())
        # attrs = vars(self)
        # from django.urls import reverse
        # return reverse(url_name, args=[str(self.slug)])
        self.slug = self.get_slug()
        return "/frontend/bookdetail/%s/" % self.slug


Book._meta.get_field('categories').verbose_name = u'分类名称'
Book._meta.get_field('title').verbose_name = u'英文书名'
Book._meta.get_field('description').verbose_name = u'摘要'
Book._meta.get_field('categories').verbose_name = u'目录'
Book._meta.get_field('content').verbose_name = u'内容简介'
Book._meta.get_field('categories').verbose_name = u'目录'
Book._meta.get_field('status').verbose_name = u'上架'
Book._meta.get_field('user').verbose_name = u'责任编辑'
Book._meta.get_field('keywords').verbose_name = u'标签'
Book._meta.get_field('_meta_title').verbose_name = u'中文书名'
Book._meta.get_field('featured_image').verbose_name = u'封面'
Book._meta.get_field('related_posts').verbose_name = u'相关书籍和章节'


@python_2_unicode_compatible  # only if you need to support Python 2
class Chapter(models.Model):
    no = models.IntegerField(db_index=True)
    title = models.CharField(max_length=100, null=True, verbose_name=u"章节标题")
    npid = models.CharField(max_length=30, null=True, default='npid')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name=u"所属书籍")
    content = RichTextField(_("Content"))
    audio_file = AudioField(upload_to="audiofiles", blank=True,
                            ext_whitelist=(".mp3", ".wav", ".ogg"),
                            help_text=("Allowed type - .mp3, .wav, .ogg"), verbose_name=u"音频文件")

    # Add this method to your model
    def audio_file_player(self):
        """audio player tag for admin"""
        if self.audio_file:
            file_url = settings.MEDIA_URL + str(self.audio_file)
            player_string = '<ul class="playlist"><li style="width:250px;">\
            <a href="%s">%s</a></li></ul>' % (file_url, os.path.basename(self.audio_file.name))
            return player_string

    audio_file_player.allow_tags = True
    audio_file_player.short_description = (u'音频文件')

    # def custom_action(self):
    #     return format_html(
    #         ' <a href="/admin/backend/chapter/{}/change/" class ="viewsitelink" target="_blank" >edit</a>',
    #         self.id
    #     )

    # custom_action.short_description = u"操作"

    def __str__(self):
        # return self.book.title + str(self.no)
        return "%s: 第%s章节" % (self.book.title, self.no)

    class Meta:
        verbose_name = u'章节管理'
        verbose_name_plural = u'章节管理'


#
#
# Chapter._meta.get_field('title').verbose_name = u'章节标题'
# Chapter._meta.get_field('content').verbose_name = u'内容'
# Chapter._meta.get_field('user').verbose_name = u'责任编辑'


#
#
# SEARCH_MODEL_CHOICES = ('backend.Book', 'backend.Author')
#
# ACCOUNTS_PROFILE_FORM_EXCLUDE_FIELDS = (
#     "first_name",
#     "last_name",
#     "signup_date",
# )



@python_2_unicode_compatible  # only if you need to support Python 2
class TrackPosition(models.Model):
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name='+',
        verbose_name=u"用户",
    )
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        verbose_name=u"章节"
    )
    # position = models.IntegerField(verbose_name=u"播放位置")
    position = DurationField(verbose_name=u"播放位置")
    # date = models.DateTimeField(auto_now_add=True, blank=True)
    time = models.DateTimeField(default=django.utils.timezone.now, blank=True, verbose_name=u"时间")

    def __str__(self):
        return u'%s' % self.position

    class Meta:
        verbose_name = u'文件位置'
        verbose_name_plural = u'文件位置'

    def get_absolute_url(self):
        """
        URLs for blog posts can either be just their slug, or prefixed
        with a portion of the post's publish date, controlled by the
        setting ``BLOG_URLS_DATE_FORMAT``, which can contain the value
        ``year``, ``month``, or ``day``. Each of these maps to the name
        of the corresponding urlpattern, and if defined, we loop through
        each of these and build up the kwargs for the correct urlpattern.
        The order which we loop through them is important, since the
        order goes from least granular (just year) to most granular
        (year/month/day).
        """

        self.slug = self.chapter.book.slug
        self.no = str(self.chapter.no)
        self.pos = str(self.position)
        # return "/frontend/bookdetail/%s/%s/$s" % (self.chapter.book.slug, self.no, self.pos)
        return "/frontend/bookdetail/" + self.slug + "/" + self.no + "/" + self.pos
