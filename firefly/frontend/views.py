# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import dumps

from django.apps import apps
from django.db.models import F
from django.http import HttpResponse
from mezzanine.core.models import Displayable
from mezzanine.generic.forms import ThreadedCommentForm
from mezzanine.generic.views import initial_validation
from mezzanine.utils.cache import add_cache_bypass
from mezzanine.utils.importing import import_dotted_path

from .models import BookCategory, Book, UserProfile, Chapter, Author, TrackPosition
from mezzanine.blog.models import BlogPost, BlogCategory
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from mezzanine.generic.models import Keyword
from calendar import month_name
from django.http import Http404
from django.contrib.auth import get_user_model
from mezzanine.utils.views import paginate, is_spam, set_cookie
from mezzanine.conf import settings
from django.utils.translation import ugettext_lazy as _

User = get_user_model()


def book_detail(request, slug, chapter=0, position=None,
                template="frontend/book_detail.html",
                extra_context=None):
    """. Custom templates are checked for using the name
    ``blog/blog_post_detail_XXX.html`` where ``XXX`` is the blog
    posts's slug.
    """
    last_chapter = None
    blog_posts = Book.objects.published(
        for_user=request.user).select_related()
    blog_post = get_object_or_404(blog_posts, slug=slug)
    related_posts = blog_post.related_posts.published(for_user=request.user)
    try:
        chapter_list = Chapter.objects.filter(book_id=blog_post.id).order_by('no')
        chapter_list = paginate(chapter_list, request.GET.get("page", 1),
                                10,
                                settings.MAX_PAGING_LINKS)
        chapter_content = chapter_list[0].content
    except:
        chapter_content = ''
    for chapter in chapter_list:
        if not request.user.is_anonymous():
            try:
                position_list = TrackPosition.objects.annotate(book=F('chapter__book')).filter(user=request.user,
                                                                                               book=blog_post).order_by(
                    '-time')
                position = position_list[0]
                last_chapter = position_list[0].chapter
            except:
                position = None

    context = {"blog_post": blog_post, "editable_obj": blog_post,
               "related_posts": related_posts, 'chapter_list': chapter_list, 'last_chapter': last_chapter,
               'chapter_content': chapter_content,
               'position': position, }
    context.update(extra_context or {})
    templates = [u"frontend/book_detail_%s.html" % str(slug), template]
    return TemplateResponse(request, templates, context)


def chapter_list(request, slug, chapter=0, position=None,
                 template="frontend/chapter_list.html",
                 extra_context=None):
    """. Custom templates are checked for using the name
    ``blog/blog_post_detail_XXX.html`` where ``XXX`` is the blog
    posts's slug.
    """
    blog_posts = Book.objects.published(
        for_user=request.user).select_related()
    blog_post = get_object_or_404(blog_posts, slug=slug)
    related_posts = blog_post.related_posts.published(for_user=request.user)
    try:
        chapter_list = Chapter.objects.filter(book_id=blog_post.id).order_by('no')
        chapter_list = paginate(chapter_list, request.GET.get("page", 1),
                                10,
                                settings.MAX_PAGING_LINKS)
        chapter_content = chapter_list[0].content
    except:
        chapter_content = ''
    for chapter in chapter_list:
        print(chapter.title)
    if not request.user.is_anonymous():
        try:
            position_list = TrackPosition.objects.annotate(book=F('chapter__book')).filter(user=request.user,
                                                                                           book=blog_post).order_by(
                '-time')
            position = position_list[0]
            last_chapter = position_list[0].chapter
        except:
            position = None
            last_chapter = None

    context = {"blog_post": blog_post, "editable_obj": blog_post,
               "related_posts": related_posts, 'chapter_list': chapter_list, 'last_chapter': last_chapter,
               'chapter_content': chapter_content,
               'position': position, }
    context.update(extra_context or {})
    templates = [u"frontend/chapter_list_%s.html" % str(slug), template]
    print(templates)
    return TemplateResponse(request, templates, context)


def book_list(request, tag=None, year=None, month=None, username=None,
              category=None, template="frontend/book_list.html",
              extra_context=None):
    """
    Display a list of blog posts that are filtered by tag, year, month,
    author or category. Custom templates are checked for using the name
    ``blog/blog_post_list_XXX.html`` where ``XXX`` is either the
    category slug or author's username if given.
    """
    print(request)
    templates = []
    # blog_posts = BlogPost.objects.published(for_user=request.user)
    blog_posts = Book.objects.published(for_user=request.user)
    if tag is not None:
        tag = get_object_or_404(Keyword, slug=tag)
        blog_posts = blog_posts.filter(keywords__keyword=tag)
    if year is not None:
        blog_posts = blog_posts.filter(publish_date__year=year)
        if month is not None:
            blog_posts = blog_posts.filter(publish_date__month=month)
            try:
                month = _(month_name[int(month)])
            except IndexError:
                raise Http404()
    if category is not None:
        category = get_object_or_404(BlogCategory, slug=category)
        blog_posts = blog_posts.filter(categories=category)
        templates.append(u"frontend/book_list_%s.html" %
                         str(category.slug))
    author = None
    if username is not None:
        author = get_object_or_404(User, username=username)
        blog_posts = blog_posts.filter(user=author)
        templates.append(u"frontend/book_list_%s.html" % username)

    prefetch = ("categories", "keywords__keyword")
    blog_posts = blog_posts.select_related("user").prefetch_related(*prefetch)
    blog_posts = paginate(blog_posts, request.GET.get("page", 1),
                          settings.BLOG_POST_PER_PAGE,
                          settings.MAX_PAGING_LINKS)
    context = {"blog_posts": blog_posts, "year": year, "month": month,
               "tag": tag, "category": category, "author": author}
    context.update(extra_context or {})
    templates.append(template)
    return TemplateResponse(request, templates, context)


def book_list_category(request, tag=None, year=None, month=None, username=None,
                       category=None, template="frontend/book_list.html",
                       extra_context=None):
    """
    Display a list of blog posts that are filtered by tag, year, month,
    author or category. Custom templates are checked for using the name
    ``blog/blog_post_list_XXX.html`` where ``XXX`` is either the
    category slug or author's username if given.
    """
    templates = []
    # blog_posts = BlogPost.objects.published(for_user=request.user)
    blog_posts = Book.objects.published(for_user=request.user)
    if tag is not None:
        tag = get_object_or_404(Keyword, slug=tag)
        blog_posts = blog_posts.filter(keywords__keyword=tag)
    if year is not None:
        blog_posts = blog_posts.filter(publish_date__year=year)
        if month is not None:
            blog_posts = blog_posts.filter(publish_date__month=month)
            try:
                month = _(month_name[int(month)])
            except IndexError:
                raise Http404()
    if category is not None:
        category = get_object_or_404(BlogCategory, slug=category)
        blog_posts = blog_posts.filter(categories=category)
        templates.append(u"frontend/book_list_%s.html" %
                         str(category.slug))
    author = None
    if username is not None:
        author = get_object_or_404(User, username=username)
        blog_posts = blog_posts.filter(user=author)
        templates.append(u"frontend/book_list_%s.html" % username)

    prefetch = ("categories", "keywords__keyword")
    blog_posts = blog_posts.select_related("user").prefetch_related(*prefetch)
    blog_posts = paginate(blog_posts, request.GET.get("page", 1),
                          settings.BLOG_POST_PER_PAGE,
                          settings.MAX_PAGING_LINKS)
    context = {"blog_posts": blog_posts, "year": year, "month": month,
               "tag": tag, "category": category, "author": author}
    context.update(extra_context or {})
    templates.append(template)
    return TemplateResponse(request, templates, context)


def index(request, tag=None, year=None, month=None, username=None,
          category=None, template="frontend/index.html",
          extra_context=None):
    """
    Display a list of blog posts that are filtered by tag, year, month,
    author or category. Custom templates are checked for using the name
    ``blog/blog_post_list_XXX.html`` where ``XXX`` is either the
    category slug or author's username if given.
    """
    templates = []
    # blog_posts = BlogPost.objects.published(for_user=request.user)
    blog_posts = Book.objects.published(for_user=request.user).order_by('?')[:12]
    if tag is not None:
        tag = get_object_or_404(Keyword, slug=tag)
        blog_posts = blog_posts.filter(keywords__keyword=tag)
    if year is not None:
        blog_posts = blog_posts.filter(publish_date__year=year)
        if month is not None:
            blog_posts = blog_posts.filter(publish_date__month=month)
            try:
                month = _(month_name[int(month)])
            except IndexError:
                raise Http404()
    if category is not None:
        category = get_object_or_404(BookCategory, slug=category)
        blog_posts = blog_posts.filter(categories=category)
        templates.append(u"frontend/book_list_%s.html" %
                         str(category.slug))
    author = None
    if username is not None:
        author = get_object_or_404(User, username=username)
        blog_posts = blog_posts.filter(user=author)
        templates.append(u"frontend/book_list_%s.html" % username)

    prefetch = ("categories", "keywords__keyword")
    blog_posts = blog_posts.select_related("user").prefetch_related(*prefetch)
    blog_posts = paginate(blog_posts, request.GET.get("page", 1),
                          settings.BLOG_POST_PER_PAGE,
                          settings.MAX_PAGING_LINKS)
    context = {"blog_posts": blog_posts, "year": year, "month": month,
               "tag": tag, "category": category, "author": author}
    context.update(extra_context or {})
    templates.append(template)
    return TemplateResponse(request, templates, context)


def myprofile(request, username=None, template="accounts/account_profile.html",
              extra_context=None):
    """
    Display a profile.
    """
    if not username:
        username = request.user
    try:
        user = User.objects.get(username=username)
    except:
        return redirect('/')

    lookup = {"username__iexact": username, "is_active": True}
    # track_list = TrackPosition.objects.filter(user=user).annotate(book=F('chapter__book')).values('book', 'chapter',
    #                                                                                               'time').annotate(
    #     dcount=Count('book')).order_by('time')
    track_list = TrackPosition.objects.filter(user=user)
    context = {"profile_user": get_object_or_404(User, **lookup), 'track_list': track_list}
    context.update(extra_context or {})
    print(template)
    return TemplateResponse(request, template, context)


def search(request, template="search_results.html", extra_context=None):
    """
    Display search results. Takes an optional "contenttype" GET parameter
    in the form "app-name.ModelName" to limit search results to a single model.
    """
    query = request.GET.get("q", "")
    page = request.GET.get("page", 1)
    per_page = settings.SEARCH_PER_PAGE
    max_paging_links = settings.MAX_PAGING_LINKS
    try:
        parts = request.GET.get("type", "").split(".", 1)
        search_model = apps.get_model(*parts)
        search_model.objects.search  # Attribute check
    except (ValueError, TypeError, LookupError, AttributeError):
        search_model = Displayable
        search_type = _("Everything")
    else:
        search_type = search_model._meta.verbose_name_plural.capitalize()
    results = search_model.objects.search(query, for_user=request.user)
    paginated = paginate(results, page, per_page, max_paging_links)
    context = {"query": query, "results": paginated,
               "search_type": search_type}
    context.update(extra_context or {})
    return TemplateResponse(request, template, context)


def comment(request, template="includes/comments.html", extra_context=None):
    """
    Handle a ``ThreadedCommentForm`` submission and redirect back to its
    related object.
    """
    response = initial_validation(request, "comment")
    if isinstance(response, HttpResponse):
        return response
    obj, post_data = response
    form_class = import_dotted_path(settings.COMMENT_FORM_CLASS)
    form = form_class(request, obj, post_data)
    if form.is_valid():
        url = obj.get_absolute_url()
        if is_spam(request, form, url):
            return redirect(url)
        comment = form.save(request)
        response = redirect(add_cache_bypass(comment.get_absolute_url()))
        # Store commenter's details in a cookie for 90 days.
        for field in ThreadedCommentForm.cookie_fields:
            cookie_name = ThreadedCommentForm.cookie_prefix + field
            cookie_value = post_data.get(field, "")
            set_cookie(response, cookie_name, cookie_value)
        return response
    elif request.is_ajax() and form.errors:
        return HttpResponse(dumps({"errors": form.errors}))
    # Show errors with stand-alone comment form.
    context = {"obj": obj, "posted_comment_form": form}
    context.update(extra_context or {})
    return TemplateResponse(request, template, context)
