from django.contrib import admin

from blog.models import Category, Location, Post

admin.site.empty_value_display = 'Не задано'


class PostInline(admin.TabularInline):
    model = Post
    extra = 0


class CategoryAdmin(admin.ModelAdmin):
    inlines = (
        PostInline,
    )
    list_display = (
        'title',
        'description',
        'is_published',
        'slug',
        'created_at',
    )
    list_editable = (
        'is_published',
    )


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'text',
        'is_published',
        'category',
        'location',
        'author',
        'pub_date',
        'created_at',
    )
    list_editable = (
        'is_published',
        'category',
        'pub_date',
    )
    search_fields = ('title',)
    list_filter = ('is_published',)
    list_display_links = ('title',)


admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Location)
