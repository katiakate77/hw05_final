import shutil
import tempfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django import forms

from ..models import Post, Group, Comment, Follow
from ..forms import CommentForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        for i in range(
            settings.POSTS_PER_PAGE + settings.POSTS_ON_SECOND_PAGE
        ):
            Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group,
            )

    def test_paginator(self):
        pages = (
            reverse('posts:index'),
            reverse('posts:group_list', args=(self.group.slug,)),
            reverse('posts:profile', args=(self.user.username,))
        )
        posts_per_page = {
            1: settings.POSTS_PER_PAGE,
            2: settings.POSTS_ON_SECOND_PAGE,
        }
        for url in pages:
            for page, count in posts_per_page.items():
                with self.subTest(page=page, count=count):
                    response = self.client.get(url, {'page': page})
                    self.assertEqual(
                        len(response.context.get('page_obj')), count
                    )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий',
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def check_context(self, response, post_or_page_obj_flag=False):
        if post_or_page_obj_flag:
            first_object = response.context.get('post')
        else:
            first_object = response.context.get('page_obj')[0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.image, f'posts/{self.uploaded.name}')

    def test_post_or_page_obj_context(self):
        pages = (
            ('posts:index', None),
            ('posts:group_list', (self.group.slug,)),
            ('posts:profile', (self.user.username,)),
            ('posts:post_detail', (self.post.id,)),
        )
        for name, args in pages:
            response = self.authorized_client.get(reverse(name, args=args))
            with self.subTest(url=reverse(name, args=args)):
                if reverse(name, args=args) == reverse(
                   'posts:post_detail', args=(self.post.id,)):
                    self.check_context(response, post_or_page_obj_flag=True)
                else:
                    self.check_context(response)

    def test_group_posts_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', args=(self.group.slug,)))
        self.assertEqual(response.context.get('group'), self.post.group)

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', args=(self.user.username,)))
        self.assertEqual(response.context.get('author'), self.user)

    def test_create_edit_pages_show_correct_context(self):
        pages = (
            ('posts:post_create', None),
            ('posts:post_edit', (self.post.id,)),
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for name, args in pages:
            response = self.authorized_client.get(reverse(name, args=args))
            self.assertIn('form', response.context)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_detail_page_show_correct_context(self):
        form_fields = {
            'text': forms.fields.CharField,
        }
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=(self.post.id,)))
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context.get('form'), CommentForm)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(
            response.context.get('comments')[0].text, self.comment.text
        )

    def test_check_cache_index_page(self):
        """Проверка кеширования главной страницы."""
        self.post_2 = Post.objects.create(
            text='Текст 2',
            author=self.user,
            group=self.group,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        resp_content_1 = response.content
        Post.objects.get(id=self.post_2.id).delete()
        response = self.authorized_client.get(reverse('posts:index'))
        resp_content_2 = response.content
        self.assertEqual(resp_content_1, resp_content_2)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        resp_content_3 = response.content
        self.assertNotEqual(resp_content_2, resp_content_3)


class FollowViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        cls.follower = User.objects.create_user(username='test_follower')
        cls.post = Post.objects.create(
            text='Текст для подписки',
            author=cls.author,
        )
        cls.authorized_client_author = Client()
        cls.authorized_client_author.force_login(cls.author)
        cls.authorized_client_follower = Client()
        cls.authorized_client_follower.force_login(cls.follower)

    def test_following_users(self):
        """Авторизованный пользователь может подписываться
        на других пользователей"""
        follow_count = Follow.objects.count()
        self.authorized_client_follower.get(
            reverse('posts:profile_follow', args=(self.author.username,)))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_follow_index_show_posts(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан"""
        response = self.authorized_client_follower.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(self.post, response.context.get('page_obj'))
        Follow.objects.create(user=self.follower, author=self.author)
        response = self.authorized_client_follower.get(
            reverse('posts:follow_index')
        )
        self.assertIn(self.post, response.context.get('page_obj'))
