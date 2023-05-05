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


def serialize_post_optimized(post, ids_and_counts):
    post.comments_count = ids_and_counts[post.id]
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count,
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


def index(request):
    all_posts = Post.objects.all()
    annotated_posts = all_posts.annotate(Count('likes'))
    ids_and_counts = get_id_and_count(all_posts)

    popular_posts = annotated_posts.order_by('-likes__count')
    most_popular_posts = popular_posts[:5].prefetch_related('tags')

    fresh_posts = annotated_posts.order_by('-published_at')
    most_fresh_posts = fresh_posts[:5].prefetch_related('tags')

    annotated_tags = Tag.objects.annotate(Count('posts'))
    popular_tags = annotated_tags.order_by('-posts__count')
    most_popular_tags = popular_tags[:5]

    context = {
        'most_popular_posts': [
            serialize_post_optimized(post, ids_and_counts) for post in most_popular_posts
        ],
        'page_posts': [serialize_post_optimized(post, ids_and_counts) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = Post.objects.get(slug=slug)
    comments = Comment.objects.filter(post=post)
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    likes = post.likes.all()

    related_tags = post.tags.all()

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': len(likes),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
    }

    # all_tags = Tag.objects.all()
    # popular_tags = sorted(all_tags, key=get_related_posts_count)

    annotated_tags = Tag.objects.annotate(Count('posts'))
    popular_tags = annotated_tags.order_by('-posts__count')
    most_popular_tags = popular_tags[:5]

    most_popular_posts = []  # TODO. Как это посчитать?

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = Tag.objects.get(title=tag_title)

    # all_tags = Tag.objects.all()
    # popular_tags = sorted(all_tags, key=get_related_posts_count)
    # most_popular_tags = popular_tags[-5:]
    annotated_tags = Tag.objects.annotate(Count('posts'))
    popular_tags = annotated_tags.order_by('-posts__count')
    most_popular_tags = popular_tags[:5]


    most_popular_posts = []  # TODO. Как это посчитать?

    related_posts = tag.posts.all()[:20]

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
