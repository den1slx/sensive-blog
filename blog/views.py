from django.shortcuts import render
from blog.models import Comment, Post, Tag
from django.db.models import Count


def get_related_posts_count(tag):
    return tag.posts__count


def get_id_and_count(posts, annotate_field='comments'):
    posts_ids = [post.id for post in posts]
    ids_and_count = posts.filter(id__in=posts_ids).annotate(Count(annotate_field))
    ids_and_count = ids_and_count.values_list('id', f'{annotate_field}__count')
    ids_and_count = dict(ids_and_count)
    return ids_and_count


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


def serialized_comment(comment):
    return {
        'text': comment.text,
        'published_at': comment.published_at,
        'author': comment.author.username,
    }


def serialize_post_optimized(post, ids_and_counts):
    post.comments_count = ids_and_counts[post.id]
    tags = post.tags.all()
    tags = tags.posts_count()
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag_optimized(tag) for tag in tags],
        'first_tag_title': tags[0].title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': Post.objects.filter(tags=tag).count(),
    }


def serialize_tag_optimized(tag):
    title = tag.title
    return {
        'title': title,
        'posts_with_tag': tag.posts__count,
    }


def index(request):
    all_posts = Post.objects.all()
    tags = Tag.objects.all()
    tags = tags.posts_count()
    ids_and_counts = get_id_and_count(all_posts)

    most_popular_posts = all_posts.popular()[:5].prefetch_related('tags')
    most_fresh_posts = all_posts.order_by('-published_at')[:5].prefetch_related('tags')
    most_popular_tags = tags.popular()[:5].prefetch_related('posts')

    context = {
        'most_popular_posts': [
            serialize_post_optimized(post, ids_and_counts) for post in most_popular_posts
        ],
        'page_posts': [serialize_post_optimized(post, ids_and_counts) for post in most_fresh_posts],
        'popular_tags': [serialize_tag_optimized(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    posts = Post.objects.all().prefetch_related('tags')
    tags = Tag.objects.all()
    tags = tags.posts_count()
    post = posts.get(slug=slug)
    comments = post.comments.all()
    # serialized_comments = []
    serialized_comments = [serialized_comment(comment) for comment in comments]
    # TODO Fix multiple queries in serialized_comments

    likes = post.likes.count()

    related_tags = post.tags.all().posts_count()

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': likes,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag_optimized(tag) for tag in related_tags],
    }
    ids_and_counts = get_id_and_count(posts)
    most_popular_tags = tags.popular()[:5].prefetch_related('posts')
    most_popular_posts = posts.popular()[:5].prefetch_related('tags')

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag_optimized(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post_optimized(post, ids_and_counts) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tags = Tag.objects.all()
    tags = tags.posts_count()
    tag = tags.get(title=tag_title)

    ids_and_counts = get_id_and_count(Post.objects.all())
    most_popular_tags = Tag.objects.popular()[:5].prefetch_related('posts')
    most_popular_posts = Post.objects.popular()[:5].prefetch_related('tags')

    related_posts = tag.posts.all()[:20].prefetch_related('tags')

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag_optimized(tag) for tag in most_popular_tags],  # many queries
        'posts': [serialize_post_optimized(post, ids_and_counts) for post in related_posts],
        'most_popular_posts': [
            serialize_post_optimized(post, ids_and_counts) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
