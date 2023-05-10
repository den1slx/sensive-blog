from django.contrib import admin
from blog.models import Post, Tag, Comment, User


class LikesInline(admin.TabularInline):
    model = Post.likes.through
    raw_id_fields = ('user',)
    extra = 1


@admin.register(Post)
class AdminPost(admin.ModelAdmin):
    raw_id_field = ('tags', 'author', 'likes')
    list_display = ('title', 'author')
    fields = (
        'title', 'text', 'slug', 'image',
        'published_at', 'author', 'tags',
        'likes',  # many times for likes
    )

    # inlines = [LikesInline] # similar queries for every user, more speed - more queries


@admin.register(Tag)
class AdminTag(admin.ModelAdmin):
    list_display = ('title', 'id')
    pass


@admin.register(Comment)
class AdminComment(admin.ModelAdmin):
    list_display = ('post', 'author')
    raw_id_fields = ('post', 'author')

