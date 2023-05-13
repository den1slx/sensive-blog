from django.db import models
from django.urls import reverse
from django.db.models import Count, Prefetch
from django.contrib.auth.models import User


class PostQuerySet(models.QuerySet):

    def year(self, year):
        return self.filter(published_at__year=year).order_by('published_at')

    def popular(self):
        return self.annotate(Count('likes', distinct=True)).order_by('-likes__count')

    def fetch_likes_count(self):
        return self.annotate(Count('likes'))

    def fetch_with_comments_id_and_count(self):
        '''
        Dict {post.id: post.comments.count()}
        :return:
        '''
        posts = self.annotate(Count('comments'))
        comments_count = dict([(post.id, post.comments__count) for post in posts])
        return comments_count

    def fetch_with_comments_count_old(self):
        '''
        list comments.count() for post in posts
        :return: list of int
        '''
        comments_count = [post.comments.count() for post in self]
        return comments_count

    def fetch_with_comments_count(self):
        posts = self
        comments_count = [post.comments.count() for post in posts]
        for i, post in enumerate(posts):
            post.comments_count = comments_count[i]

        return posts

    def prefetch_tags(self, to_attr='tags_'):
        return self.prefetch_related(Prefetch(
            'tags',
            queryset=Tag.objects.all().fetch_with_posts_count(),
            to_attr=to_attr
        ))


class TagQuerySet(models.QuerySet):
    def popular(self):
        return self.annotate(Count('posts')).order_by('-posts__count')

    def fetch_with_posts_count(self, changed=False):
        """
        Add comments_count
        :param changed: if True changed base QuerySet, else 'self' not changed
        :return: QuerySet
        """

        if changed:
            return self.annotate(posts_count=Count('posts'))

        model = self
        return model.annotate(posts_count=Count('posts'))


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)

    objects = TagQuerySet.as_manager()

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    def clean(self):
        self.title = self.title.lower()


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        verbose_name='Пост, к которому написан',
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='comments',
    )

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'
