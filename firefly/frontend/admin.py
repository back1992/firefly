import os

from django.contrib import admin
from .models import Publisher, UserProfile, Author, Book, BookCategory, Chapter, TrackPosition
from copy import deepcopy
from mezzanine.conf import settings
from mezzanine.core.admin import (DisplayableAdmin, OwnableAdmin,
                                  BaseTranslationModelAdmin)
from django.utils.translation import ugettext_lazy as _
from mezzanine.blog.admin import BlogPostAdmin
from ordered_model.admin import OrderedModelAdmin


class PublisherAdmin(admin.ModelAdmin):
    fields = ('name', 'website',)
    list_display = ('name', 'website',)
    list_display_link = ('name')


admin.site.register(Publisher, PublisherAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    pass
    # fieldsets = (
    #     (None, {
    #         'fields': (("first_name", "last_name",), 'username')
    #     }),
    #     ('Advanced options', {
    #         'classes': ('collapse',),
    #         'fields': ('bio', 'shirt_size'),
    #     }),
    # )


admin.site.register(UserProfile, UserProfileAdmin)


class TrackPositionAdmin(admin.ModelAdmin):
    list_display = ('user', 'chapter', 'position', 'time')


admin.site.register(TrackPosition, TrackPositionAdmin)


class AuthorAdmin(admin.ModelAdmin):
    # list_display = ('english_name', 'chinese_name', 'country')
    # search_fields = ('english_name', 'chinese_name')
    list_display = ('english_name', 'country')
    search_fields = ('english_name',)


admin.site.register(Author, AuthorAdmin)

book_fieldsets = deepcopy(DisplayableAdmin.fieldsets)
book_fieldsets[0][1]["fields"].insert(1, "categories")
book_fieldsets[0][1]["fields"].extend(["content", "allow_comments"])
book_list_display = ["title", "user", "status", "admin_link"]
if settings.BLOG_USE_FEATURED_IMAGE:
    book_fieldsets[0][1]["fields"].insert(-2, "featured_image")
    book_list_display.insert(0, "admin_thumb")
book_fieldsets = list(book_fieldsets)
book_fieldsets.insert(1, (_("Other posts"), {
    "classes": ("collapse-closed",),
    "fields": ("related_posts",)}))
book_list_filter = deepcopy(DisplayableAdmin.list_filter) + ("categories",)


class BookAdmin(BlogPostAdmin):
    pass


admin.site.register(Book, BookAdmin)


class BookCategoryAdmin(OrderedModelAdmin):
    fields = ('title', 'slug', 'cover', 'npid')
    readonly_fields = ('image_tag',)
    list_display = ('title', 'slug', 'image_tag', 'npid', 'move_up_down_links')
    list_display_link = ('title', 'slug',)


admin.site.register(BookCategory, BookCategoryAdmin)


#
# def custom_delete_selected(self, request, queryset):
#     n = queryset.count()
#     for i in queryset:
#         if i.audio_file:
#             if os.path.exists(i.audio_file.path):
#                 os.remove(i.audio_file.path)
#         i.delete()
#     self.message_user(request, ("Successfully deleted %d audio files.") % n)
#
#
# custom_delete_selected.short_description = "Delete selected items"
#
#
# # def get_actions(self, request):
# #     actions = super(AudioFileAdmin, self).get_actions(request)
# #     del actions['delete_selected']
# #     return actions
#
#
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('no', 'title', 'npid', 'book', 'audio_file_player')
    list_filter = ('book',)
    actions = ['custom_delete_selected']

    def custom_delete_selected(self, request, queryset):
        # custom delete code
        n = queryset.count()
        for i in queryset:
            if i.audio_file:
                if os.path.exists(i.audio_file.path):
                    os.remove(i.audio_file.path)
            i.delete()
        self.message_user(request, ("Successfully deleted %d audio files.") % n)

    custom_delete_selected.short_description = "Delete selected items"

    def get_actions(self, request):
        actions = super(ChapterAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions


admin.site.register(Chapter, ChapterAdmin)
# list_display_links = ('no', 'title')
# # list_display_links = None
# list_filter = ('book',)
#
# def get_form(self, request, obj=None, **kwargs):
#     form = super(ChapterAdmin, self).get_form(request, obj, **kwargs)
#     form.base_fields['user'].initial = 'daniel'
#     return form
#
# def get_changeform_initial_data(self, request):
#     if request.GET and request.GET['book__id__exact']:
#         book = int(request.GET['book__id__exact'])
#         data = {'user': 1, 'book': book}
#     else:
#         data = {'user': 1}
#     print(data)
#
#     return data
#     # return {'user': 1}
#
# def response_change(self, request, obj):
#     """ if user clicked "edit this page", return back to main site """
#     response = super(ChapterAdmin, self).response_change(request, obj)
#
#     if (isinstance(response, HttpResponseRedirect) and
#                 response['location'] == '../' and
#                 request.GET.get('source') == 'main'):
#         response['location'] = obj.get_absolute_url()
#     response['location'] = '/admin/backend/chapter/?book__id__exact=' + str(obj.book.id)
#     return response

# def number_of_orders(self, obj):
#     end_number = re.match('.*?([0-9]+)$', obj.title).group(1)
#     return end_number
#
# number_of_orders.admin_order_field = 'order__count'

# actions = ['custom_delete_selected']

# def save_model(self, request, obj, form, change):
#     obj.user = request.user
#     obj.save()


#
#

#
# # class ChapterInline(admin.TabularInline):
# # class ChapterInline(admin.StackedInline):
# #     model = Chapter
# #     # exclude = ('image', 'url')
# #     fields = ('no', 'title', 'content', 'audio_file', 'book', 'user')
# #     list_display = ('no', 'title', 'book', 'audio_file_player')
# #     list_display_links = None
# #     extra = 0
# #
# #     # view_on_site = False
# #
# #     def view_on_site(self, obj):
# #         # url = reverse('book_detail', kwargs={'title': obj.title})
# #         url = reverse('home')
# #         return url
#
#
# class BookAdmin(admin.ModelAdmin):
#     # date_hierarchy = 'pub_date'
#     # fields = ('title', 'titlezh', 'npid', 'author', 'publisher', 'categories', 'cover', 'description', 'is_published')
#     # readonly_fields = ('image_tag',)
#     # list_display = ('title', 'titlezh', 'npid', 'slug', 'author', 'publisher', 'cover', 'is_published', 'custom_action')
#     # list_display_link = ('title', 'npid', 'titlezh',)
#     # list_filter = ('categories',)
#     pass
#
#
# admin.site.register(Book, BookAdmin)
