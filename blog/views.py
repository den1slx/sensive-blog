from django.shortcuts import render
from blog.models import Comment, Post, Tag
from django.db.models import Count


def add_template_field(queryset, counts):
    for i, post in enumerate(queryset):
        post.comments_count = counts[i]


def get_related_posts_count(tag):
    return tag.posts__count


def get_likes_count(post):
    return post.likes__count


def serialize_post(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': len(Comment.objects.filter(post=post)),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': Post.objects.filter(tags=tag).count(),
    }


def serialized_comment(comment):
    return {
        'text': comment.text,
        'published_at': comment.published_at,
        'author': comment.author.username,
    }


def serialize_post_optimized(post, comments, post_count_tags=None):
    if type(comments) == dict:
        comments_count = comments[post.id]
    elif type(comments) == int:
        comments_count = comments
    else:
        comments_count = comments.post_comments(post)

    if type(post_count_tags) == list:
        count_tags = post_count_tags
        tags = post.tags.all()
    else:
        tags = post.tags.all().prefetch_related('posts')
        count_tags = tags.fetch_with_posts_count()

    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag_optimized(tag, count_tags[i]) for (i, tag) in enumerate(tags)],
        'first_tag_title': tags[0].title,
    }


def serialize_post_new(post):
    tags = post.tags.all()
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag_new(tag) for tag in tags.fetch_with_posts_count_new()],
        'first_tag_title': tags.first().title,
    }


def serialize_tag_new(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_count,
    }


def serialize_tag_optimized(tag, count=None):
    if type(count) == int:
        tag_count = count
    else:
        tag_count = tag.posts__count
    return {
        'title': tag.title,
        'posts_with_tag': tag_count,
    }


def index(request):
    all_posts = Post.objects.all()
    tags = Tag.objects.all().posts_count()

    most_popular_posts = all_posts.popular()[:5]\
        .prefetch_related('tags', 'comments', 'author')
    popular_counts = most_popular_posts.fetch_with_comments_count()
    add_template_field(most_popular_posts, popular_counts)

    most_fresh_posts = all_posts.order_by('-published_at')[:5]\
        .prefetch_related('tags', 'comments', 'author')
    fresh_counts = most_popular_posts.fetch_with_comments_count()
    add_template_field(most_fresh_posts, fresh_counts)

    most_popular_tags = tags.popular()[:5].fetch_with_posts_count_new()

    context = {
        'most_popular_posts': [
            serialize_post_new(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post_new(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag_new(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    posts = Post.objects.all().prefetch_related('tags', 'author', 'comments')
    all_comments = Comment.objects.all().prefetch_related('post')
    tags = Tag.objects.all()
    post = posts.get(slug=slug)
    comments = all_comments.filter(post=post)
    serialized_comments = []
    serialized_comments = [serialized_comment(comment) for comment in comments]
    # TODO Fix multiple queries in serialized_comments

    likes = post.likes.count()

    related_tags = post.tags.all().fetch_with_posts_count_new()

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': likes,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag_new(tag) for tag in related_tags],
    }

    most_popular_tags = tags.popular()[:5].prefetch_related('posts').fetch_with_posts_count_new()

    most_popular_posts = posts.popular()[:5]
    popular_counts = most_popular_posts.fetch_with_comments_count()
    add_template_field(most_popular_posts, popular_counts)

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag_new(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post_new(post) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tags = Tag.objects.all()
    posts = Post.objects.all()

    tag = tags.get(title=tag_title)
    most_popular_tags = tags.popular()[:5].prefetch_related('posts').fetch_with_posts_count_new()  # need prefetch ?

    most_popular_posts = posts.popular()[:5].prefetch_related('tags', 'author', 'comments')
    popular_counts = most_popular_posts.fetch_with_comments_count()
    add_template_field(most_popular_posts, popular_counts)

    related_posts = tag.posts.all()[:20].prefetch_related('tags', 'author', 'comments')
    related_counts = related_posts.fetch_with_comments_count()
    add_template_field(related_posts, related_counts)

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag_new(tag) for tag in most_popular_tags],
        'posts': [serialize_post_new(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post_new(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
