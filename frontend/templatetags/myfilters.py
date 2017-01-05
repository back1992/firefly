from __future__ import unicode_literals
import os

try:
    from urllib.parse import quote, unquote
except ImportError:
    from urllib import quote, unquote
from django.utils.text import capfirst
from django.template.loader import get_template
from mezzanine.conf import settings
from django.contrib import admin
from mezzanine.utils.urls import admin_url
from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib.sites.models import Site
from mezzanine.utils.sites import current_site_id
from django.core.exceptions import ObjectDoesNotExist
from mezzanine import template
from django.template import Context, TemplateSyntaxError, Variable
from mezzanine.pages.models import Page
from mezzanine.utils.urls import home_slug
from collections import defaultdict
from django.core.files.storage import default_storage
from django.core.files import File
from frontend.models import Book, UserProfile, BookCategory
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, Count
from mezzanine.generic.models import AssignedKeyword, Keyword
from mezzanine.blog.models import BlogCategory
from django.contrib.auth import get_user_model
import hashlib
from django.shortcuts import render
from django.contrib.staticfiles.templatetags.staticfiles import static

User = get_user_model()

register = template.Library()


@register.filter(name='addclass')
def addclass(value, arg):
    return value.as_widget(attrs={'class': arg})


@register.filter(name='addplaceholder')
def addplaceholder(field, placeholder):
    return field.as_widget(attrs={"placeholder": placeholder})
    # return field.field.widget.attrs.update({"placeholder": placeholder})
    # return field.widget.attrs["placeholder"]=placeholder


@register.filter(name='placeholder')
def placeholder(value, token):
    value.field.widget.attrs["placeholder"] = token
    return value


@register.filter(name='get_type')
def get_type(value):
    t = type(value)
    return t.__module__ + "." + t.__name__


def admin_app_list(request):
    """
    Adopted from ``django.contrib.admin.sites.AdminSite.index``.
    Returns a list of lists of models grouped and ordered according to
    ``mezzanine.conf.ADMIN_MENU_ORDER``. Called from the
    ``admin_dropdown_menu`` template tag as well as the ``app_list``
    dashboard widget.
    """
    app_dict = {}

    # Model or view --> (group index, group title, item index, item title).
    menu_order = {}
    for (group_index, group) in enumerate(settings.ADMIN_MENU_ORDER):
        group_title, items = group
        for (item_index, item) in enumerate(items):
            if isinstance(item, (tuple, list)):
                item_title, item = item
            else:
                item_title = None
            menu_order[item] = (group_index, group_title,
                                item_index, item_title)

    # Add all registered models, using group and title from menu order.
    for (model, model_admin) in admin.site._registry.items():
        opts = model._meta
        in_menu = not hasattr(model_admin, "in_menu") or model_admin.in_menu()
        if hasattr(model_admin, "in_menu"):
            import warnings
            warnings.warn(
                'ModelAdmin.in_menu() has been replaced with '
                'ModelAdmin.has_module_permission(request). See '
                'https://docs.djangoproject.com/en/stable/ref/contrib/admin/'
                '#django.contrib.admin.ModelAdmin.has_module_permission.',
                DeprecationWarning)
        in_menu = in_menu and model_admin.has_module_permission(request)
        if in_menu and request.user.has_module_perms(opts.app_label):
            admin_url_name = ""
            if model_admin.has_change_permission(request):
                admin_url_name = "changelist"
                change_url = admin_url(model, admin_url_name)
            else:
                change_url = None
            if model_admin.has_add_permission(request):
                admin_url_name = "add"
                add_url = admin_url(model, admin_url_name)
            else:
                add_url = None
            if admin_url_name:
                model_label = "%s.%s" % (opts.app_label, opts.object_name)
                try:
                    app_index, app_title, model_index, model_title = \
                        menu_order[model_label]
                except KeyError:
                    app_index = None
                    try:
                        app_title = opts.app_config.verbose_name.title()
                    except AttributeError:
                        # Third party admin classes doing weird things.
                        # See GH #1628
                        app_title = ""
                    model_index = None
                    model_title = None
                else:
                    del menu_order[model_label]

                if not model_title:
                    model_title = capfirst(model._meta.verbose_name_plural)

                if app_title not in app_dict:
                    app_dict[app_title] = {
                        "index": app_index,
                        "name": app_title,
                        "models": [],
                    }
                app_dict[app_title]["models"].append({
                    "index": model_index,
                    "perms": model_admin.get_model_perms(request),
                    "name": model_title,
                    "object_name": opts.object_name,
                    "admin_url": change_url,
                    "add_url": add_url
                })

    # Menu may also contain view or url pattern names given as (title, name).
    for (item_url, item) in menu_order.items():
        app_index, app_title, item_index, item_title = item
        try:
            item_url = reverse(item_url)
        except NoReverseMatch:
            continue
        if app_title not in app_dict:
            app_dict[app_title] = {
                "index": app_index,
                "name": app_title,
                "models": [],
            }
        app_dict[app_title]["models"].append({
            "index": item_index,
            "perms": {"custom": True},
            "name": item_title,
            "admin_url": item_url,
        })

    app_list = list(app_dict.values())
    sort = lambda x: (x["index"] if x["index"] is not None else 999, x["name"])
    for app in app_list:
        app["models"].sort(key=sort)
    app_list.sort(key=sort)
    return app_list


@register.inclusion_tag("includes/dropdown_menu.html",
                        takes_context=True)
def admin_dropdown_menu(context):
    """
    Renders the app list for the admin dropdown menu navigation.
    """
    template_vars = context.flatten()
    user = context["request"].user
    if user.is_staff:
        template_vars["dropdown_menu_app_list"] = admin_app_list(
            context["request"])
        if user.is_superuser:
            sites = Site.objects.all()
        else:
            try:
                sites = user.sitepermissions.sites.all()
            except ObjectDoesNotExist:
                sites = Site.objects.none()
        template_vars["dropdown_menu_sites"] = list(sites)
        template_vars["dropdown_menu_selected_site_id"] = current_site_id()
        template_vars["settings"] = context["settings"]
        template_vars["request"] = context["request"]
        return template_vars


@register.render_tag
def my_page_menu(context, token):
    """
    Return a list of child pages for the given parent, storing all
    pages in a dict in the context when first called using parents as keys
    for retrieval on subsequent recursive calls from the menu template.
    """
    # First arg could be the menu template file name, or the parent page.
    # Also allow for both to be used.
    template_name = None
    parent_page = None
    parts = token.split_contents()[1:]
    for part in parts:
        part = Variable(part).resolve(context)
        if isinstance(part, str):
            template_name = part
        elif isinstance(part, Page):
            parent_page = part
    if template_name is None:
        try:
            template_name = context["menu_template_name"]
        except KeyError:
            error = "No template found for page_menu in: %s" % parts
            raise TemplateSyntaxError(error)
    context["menu_template_name"] = template_name
    if "menu_pages" not in context:
        try:
            user = context["request"].user
            slug = context["request"].path
        except KeyError:
            user = None
            slug = ""
        num_children = lambda id: lambda: len(context["menu_pages"][id])
        has_children = lambda id: lambda: num_children(id)() > 0
        rel = [m.__name__.lower()
               for m in Page.get_content_models()
               if not m._meta.proxy]
        published = Page.objects.published(for_user=user).select_related(*rel)
        # Store the current page being viewed in the context. Used
        # for comparisons in page.set_menu_helpers.
        if "page" not in context:
            try:
                context.dicts[0]["_current_page"] = published.exclude(
                    content_model="link").get(slug=slug)
            except Page.DoesNotExist:
                context.dicts[0]["_current_page"] = None
        elif slug:
            context.dicts[0]["_current_page"] = context["page"]
        # Some homepage related context flags. on_home is just a helper
        # indicated we're on the homepage. has_home indicates an actual
        # page object exists for the homepage, which can be used to
        # determine whether or not to show a hard-coded homepage link
        # in the page menu.
        home = home_slug()
        context.dicts[0]["on_home"] = slug == home
        context.dicts[0]["has_home"] = False
        # Maintain a dict of page IDs -> parent IDs for fast
        # lookup in setting page.is_current_or_ascendant in
        # page.set_menu_helpers.
        context.dicts[0]["_parent_page_ids"] = {}
        pages = defaultdict(list)
        for page in published.order_by("_order"):
            page.set_helpers(context)
            context["_parent_page_ids"][page.id] = page.parent_id
            setattr(page, "num_children", num_children(page.id))
            setattr(page, "has_children", has_children(page.id))
            pages[page.parent_id].append(page)
            if page.slug == home:
                context.dicts[0]["has_home"] = True
        # Include menu_pages in all contexts, not only in the
        # block being rendered.
        context.dicts[0]["menu_pages"] = pages
    # ``branch_level`` must be stored against each page so that the
    # calculation of it is correctly applied. This looks weird but if we do
    # the ``branch_level`` as a separate arg to the template tag with the
    # addition performed on it, the addition occurs each time the template
    # tag is called rather than once per level.
    context["branch_level"] = 0
    parent_page_id = None
    if parent_page is not None:
        context["branch_level"] = getattr(parent_page, "branch_level", 0) + 1
        parent_page_id = parent_page.id

    # Build the ``page_branch`` template variable, which is the list of
    # pages for the current parent. Here we also assign the attributes
    # to the page object that determines whether it belongs in the
    # current menu template being rendered.
    context["page_branch"] = context["menu_pages"].get(parent_page_id, [])
    context["page_branch_in_menu"] = False
    # context["icon_in_menu"] = {"1": "disk", "2": "music-tone-alt", "3": "drawer", "4": "list", "5": "music-tone",
    #                            "6": "grid", "7": "screen-desktop", "8": "playlist"}
    context["icon_in_menu"] = ["disk", "music-tone-alt", "drawer", "list", "music-tone",
                               "grid", "screen-desktop", "playlist"]
    for page in context["page_branch"]:
        page.in_menu = page.in_menu_template(template_name)
        page.num_children_in_menu = 0
        if page.in_menu:
            context["page_branch_in_menu"] = True
        for child in context["menu_pages"].get(page.id, []):
            if child.in_menu_template(template_name):
                page.num_children_in_menu += 1
        page.has_children_in_menu = page.num_children_in_menu > 0
        page.branch_level = context["branch_level"]
        page.parent = parent_page
        context["parent_page"] = page.parent

        # Prior to pages having the ``in_menus`` field, pages had two
        # boolean fields ``in_navigation`` and ``in_footer`` for
        # controlling menu inclusion. Attributes and variables
        # simulating these are maintained here for backwards
        # compatibility in templates, but will be removed eventually.
        page.in_navigation = page.in_menu
        page.in_footer = not (not page.in_menu and "footer" in template_name)
        if page.in_navigation:
            context["page_branch_in_navigation"] = True
        if page.in_footer:
            context["page_branch_in_footer"] = True

    t = get_template(template_name)
    return t.render(Context(context))


@register.filter
def get_item(dictionary, key):
    return dictionary[key]


@register.filter
def get_meta_title(queryset):
    return queryset._meta_title


@register.inclusion_tag("includes/pagination.html", takes_context=True)
def my_pagination_for(context, current_page, page_var="page", exclude_vars=""):
    """
    Include the pagination template and data for persisting querystring
    in pagination links. Can also contain a comma separated string of
    var names in the current querystring to exclude from the pagination
    links, via the ``exclude_vars`` arg.
    """
    querystring = context["request"].GET.copy()
    exclude_vars = [v for v in exclude_vars.split(",") if v] + [page_var]
    for exclude_var in exclude_vars:
        if exclude_var in querystring:
            del querystring[exclude_var]
    querystring = querystring.urlencode()
    result = {
        "current_page": current_page,
        "querystring": querystring,
        "page_var": page_var,
    }
    return result


@register.simple_tag
def my_thumbnail(image_url, width, height, upscale=True, quality=95, left=.5,
                 top=.5, padding=False, padding_color="#fff"):
    """
    Given the URL to an image, resizes the image using the given width
    and height on the first time it is requested, and returns the URL
    to the new resized image. If width or height are zero then original
    ratio is maintained. When ``upscale`` is False, images smaller than
    the given size will not be grown to fill that size. The given width
    and height thus act as maximum dimensions.
    """

    if not image_url:
        return ""
    try:
        from PIL import Image, ImageFile, ImageOps
    except ImportError:
        return ""

    image_url = unquote(str(image_url)).split("?")[0]
    if image_url.startswith(settings.MEDIA_URL):
        image_url = image_url.replace(settings.MEDIA_URL, "", 1)
    image_dir, image_name = os.path.split(image_url)
    image_prefix, image_ext = os.path.splitext(image_name)
    filetype = {".png": "PNG", ".gif": "GIF"}.get(image_ext, "JPEG")
    thumb_name = "%s-%sx%s" % (image_prefix, width, height)
    if not upscale:
        thumb_name += "-no-upscale"
    if left != .5 or top != .5:
        left = min(1, max(0, left))
        top = min(1, max(0, top))
        thumb_name = "%s-%sx%s" % (thumb_name, left, top)
    thumb_name += "-padded-%s" % padding_color if padding else ""
    thumb_name = "%s%s" % (thumb_name, image_ext)

    # `image_name` is used here for the directory path, as each image
    # requires its own sub-directory using its own name - this is so
    # we can consistently delete all thumbnails for an individual
    # image, which is something we do in filebrowser when a new image
    # is written, allowing us to purge any previously generated
    # thumbnails that may match a new image name.
    thumb_dir = os.path.join(settings.MEDIA_ROOT, image_dir,
                             settings.THUMBNAILS_DIR_NAME, image_name)
    if not os.path.exists(thumb_dir):
        try:
            os.makedirs(thumb_dir)
        except OSError:
            pass

    thumb_path = os.path.join(thumb_dir, thumb_name)
    thumb_url = "%s/%s/%s" % (settings.THUMBNAILS_DIR_NAME,
                              quote(image_name.encode("utf-8")),
                              quote(thumb_name.encode("utf-8")))
    image_url_path = os.path.dirname(image_url)
    if image_url_path:
        thumb_url = "%s/%s" % (image_url_path, thumb_url)

    try:
        thumb_exists = os.path.exists(thumb_path)
    except UnicodeEncodeError:
        # The image that was saved to a filesystem with utf-8 support,
        # but somehow the locale has changed and the filesystem does not
        # support utf-8.
        from mezzanine.core.exceptions import FileSystemEncodingChanged
        raise FileSystemEncodingChanged()
    if thumb_exists:
        # Thumbnail exists, don't generate it.
        return thumb_url
    elif not default_storage.exists(image_url):
        # Requested image does not exist, just return its URL.
        return image_url

    f = default_storage.open(image_url)
    try:
        image = Image.open(f)
    except:
        # Invalid image format.
        return image_url

    image_info = image.info

    # Transpose to align the image to its orientation if necessary.
    # If the image is transposed, delete the exif information as
    # not all browsers support the CSS image-orientation:
    # - http://caniuse.com/#feat=css-image-orientation
    try:
        orientation = image._getexif().get(0x0112)
    except:
        orientation = None
    if orientation:
        methods = {
            2: (Image.FLIP_LEFT_RIGHT,),
            3: (Image.ROTATE_180,),
            4: (Image.FLIP_TOP_BOTTOM,),
            5: (Image.FLIP_LEFT_RIGHT, Image.ROTATE_90),
            6: (Image.ROTATE_270,),
            7: (Image.FLIP_LEFT_RIGHT, Image.ROTATE_270),
            8: (Image.ROTATE_90,)}.get(orientation, ())
        if methods:
            image_info.pop('exif', None)
            for method in methods:
                image = image.transpose(method)

    to_width = int(width)
    to_height = int(height)
    from_width = image.size[0]
    from_height = image.size[1]

    if not upscale:
        to_width = min(to_width, from_width)
        to_height = min(to_height, from_height)

    # Set dimensions.
    if to_width == 0:
        to_width = from_width * to_height // from_height
    elif to_height == 0:
        to_height = from_height * to_width // from_width
    if image.mode not in ("P", "L", "RGBA"):
        try:
            image = image.convert("RGBA")
        except:
            return image_url
    # Required for progressive jpgs.
    ImageFile.MAXBLOCK = 2 * (max(image.size) ** 2)

    # Padding.
    if padding and to_width and to_height:
        from_ratio = float(from_width) / from_height
        to_ratio = float(to_width) / to_height
        pad_size = None
        if to_ratio < from_ratio:
            pad_height = int(to_height * (float(from_width) / to_width))
            pad_size = (from_width, pad_height)
            pad_top = (pad_height - from_height) // 2
            pad_left = 0
        elif to_ratio > from_ratio:
            pad_width = int(to_width * (float(from_height) / to_height))
            pad_size = (pad_width, from_height)
            pad_top = 0
            pad_left = (pad_width - from_width) // 2
        if pad_size is not None:
            pad_container = Image.new("RGBA", pad_size, padding_color)
            pad_container.paste(image, (pad_left, pad_top))
            image = pad_container

    # Create the thumbnail.
    if to_width > to_height:
        my_to_width = my_to_height = to_height
    else:
        my_to_width = my_to_height = to_width

    to_size = (my_to_width, my_to_height)
    to_pos = (left, top)
    try:
        image = ImageOps.fit(image, to_size, Image.ANTIALIAS, 0, to_pos)
        image = image.save(thumb_path, filetype, quality=quality, **image_info)
        # Push a remote copy of the thumbnail if MEDIA_URL is
        # absolute.
        if "://" in settings.MEDIA_URL:
            with open(thumb_path, "rb") as f:
                default_storage.save(unquote(thumb_url), File(f))
    except Exception:
        # If an error occurred, a corrupted image may have been saved,
        # so remove it, otherwise the check for it existing will just
        # return the corrupted image next time it's requested.
        try:
            os.remove(thumb_path)
        except Exception:
            pass
        return image_url
    return thumb_url


@register.filter
def get_author(blog_id):
    book = Book.objects.get(blogpost_ptr_id=blog_id)
    # return book.author.english_name
    return book.author.chinese_name + '/' + book.author.english_name


@register.as_tag
def my_keywords_for(*args):
    """
    Return a list of ``Keyword`` objects for the given model instance
    or a model class. In the case of a model class, retrieve all
    keywords for all instances of the model and apply a ``weight``
    attribute that can be used to create a tag cloud.
    """

    # Handle a model instance.
    if isinstance(args[0], Model):
        obj = args[0]
        if getattr(obj, "content_model", None):
            obj = obj.get_content_model()
        keywords_name = obj.get_keywordsfield_name()
        keywords_queryset = getattr(obj, keywords_name).all()
        # Keywords may have been prefetched already. If not, we
        # need select_related for the actual keywords.
        prefetched = getattr(obj, "_prefetched_objects_cache", {})
        if keywords_name not in prefetched:
            keywords_queryset = keywords_queryset.select_related("keyword")
        return [assigned.keyword for assigned in keywords_queryset]

    # Handle a model class.
    try:
        app_label, model = args[0].split(".", 1)
    except ValueError:
        return []

    content_type = ContentType.objects.get(app_label=app_label, model=model)
    assigned = AssignedKeyword.objects.filter(content_type=content_type)
    keywords = Keyword.objects.filter(assignments__in=assigned)
    keywords = keywords.annotate(item_count=Count("assignments"))
    if not keywords:
        return []
    counts = [keyword.item_count for keyword in keywords]
    min_count, max_count = min(counts), max(counts)
    factor = (settings.TAG_CLOUD_SIZES - 1.)
    if min_count != max_count:
        factor /= (max_count - min_count)
    for kywd in keywords:
        kywd.weight = int(round((kywd.item_count - min_count) * factor)) + 1
    return keywords


@register.simple_tag(takes_context=True)
def my_fields_for(context, form, template="includes/my_form_fields.html"):
    """
    Renders fields for a form with an optional template choice.
    """
    context["form_for_fields"] = form
    return get_template(template).render(context)


@register.as_tag
def blog_recent_books(limit=5, tag=None, username=None, category=None):
    """
    Put a list of recently published blog posts into the template
    context. A tag title or slug, category title or slug or author's
    username can also be specified to filter the recent posts returned.

    Usage::

        {% blog_recent_posts 5 as recent_posts %}
        {% blog_recent_posts limit=5 tag="django" as recent_posts %}
        {% blog_recent_posts limit=5 category="python" as recent_posts %}
        {% blog_recent_posts 5 username=admin as recent_posts %}

    """
    blog_posts = Book.objects.published().select_related("user")
    title_or_slug = lambda s: Q(title=s) | Q(slug=s)
    if tag is not None:
        try:
            tag = Keyword.objects.get(title_or_slug(tag))
            blog_posts = blog_posts.filter(keywords__keyword=tag)
        except Keyword.DoesNotExist:
            return []
    if category is not None:
        try:
            category = BlogCategory.objects.get(title_or_slug(category))
            blog_posts = blog_posts.filter(categories=category)
        except BlogCategory.DoesNotExist:
            return []
    if username is not None:
        try:
            author = User.objects.get(username=username)
            blog_posts = blog_posts.filter(user=author)
        except User.DoesNotExist:
            return []
    return list(blog_posts[:limit])


@register.simple_tag
def my_gravatar_url(email, size=32):
    """
    Return the full URL for a Gravatar given an email hash.
    """
    # bits = (md5(email.lower().encode("utf-8")).hexdigest(), size)
    # return "//www.gravatar.com/avatar/%s?s=%s&d=identicon&r=PG" % bits

    # user = User.model(email=email, is_staff=False, is_active=True, **extra_fields)
    try:
        user = User.objects.get(email=email)
        avatar = str(user.profile.avatar)
        media_url = settings.MEDIA_URL
        avatar = media_url + '/' + avatar
        return avatar
    except:
        bits = (hashlib.md5(email.lower().encode("utf-8")).hexdigest(), size)
        return "//www.gravatar.com/avatar/%s?s=%s&d=identicon&r=PG" % bits


@register.as_tag
def book_categories(*args):
    """
    Put a list of categories for blog posts into the template context.
    """
    posts = Book.objects.published()
    categories = BookCategory.objects.filter(blogposts__in=posts)
    return list(categories.annotate(post_count=Count("blogposts")))


@register.as_tag
def results_categories(results):
    """
    Put a list of categories for blog posts into the template context.
    """
    posts = results
    categories = BookCategory.objects.filter(blogposts__in=posts)
    return list(categories.annotate(post_count=Count("blogposts")))


@register.simple_tag(takes_context=True)
def my_fields_for(context, form, template="includes/my_form_fields.html"):
    """
    Renders fields for a form with an optional template choice.
    """
    context["form_for_fields"] = form
    return get_template(template).render(context)
