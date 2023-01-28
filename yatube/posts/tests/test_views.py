from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings
from django import forms

from ..models import Post, Group


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
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.group,
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def check_context(self, response, post_or_page_obj_flag=False):
        if post_or_page_obj_flag:
            first_object = response.context.get('post')
        else:
            first_object = response.context.get('page_obj')[0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.group, self.group)

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




