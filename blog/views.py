from django.shortcuts import render, get_object_or_404
from blog.models import Comment, Post, Tag


def serialized_comment(comment):
    return {
        'text': comment.text,
        'published_at': comment.published_at,
        'author': comment.author.username,
    }


def serialize_post(post):
    tags = post.tags_
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in tags],
        'first_tag_title': tags[0].title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_count,
    }


def index(request):
    tags = Tag.objects.all().fetch_with_posts_count()
    all_posts = Post.objects.all().prefetch_tags()

    most_popular_posts = all_posts.popular()[:5] \
        .prefetch_related('tags', 'comments', 'author')\
        .fetch_with_comments_count()

    most_fresh_posts = all_posts.order_by('-published_at')[:5]\
        .prefetch_related('tags', 'comments', 'author') \
        .fetch_with_comments_count()

    most_popular_tags = tags.popular()[:5].fetch_with_posts_count()

    context = {
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    tags = Tag.objects.all().fetch_with_posts_count()

    posts = Post.objects.all()\
        .fetch_likes_count()\
        .prefetch_tags()\
        .prefetch_related('tags', 'author', 'comments')

    post = get_object_or_404(posts, slug=slug)
    comments = post.comments.all().prefetch_related('author')
    serialized_comments = [serialized_comment(comment) for comment in comments]

    related_tags = post.tags.all().fetch_with_posts_count()

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': post.likes__count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
    }

    most_popular_tags = tags.popular()[:5].prefetch_related('posts').fetch_with_posts_count()

    most_popular_posts = posts.popular()[:5].fetch_with_comments_count()

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tags = Tag.objects.all().fetch_with_posts_count()
    posts = Post.objects.all().prefetch_tags()

    tag = get_object_or_404(tags, title=tag_title)
    most_popular_tags = tags.popular()[:5].prefetch_related('posts')

    most_popular_posts = posts.popular()[:5]\
        .prefetch_related('tags', 'author', 'comments')\
        .fetch_with_comments_count()

    related_posts = tag.posts.all()[:20]\
        .prefetch_tags()\
        .prefetch_related('tags', 'author', 'comments')\
        .fetch_with_comments_count()

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
