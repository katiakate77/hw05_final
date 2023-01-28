from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus

from ..models import Group, Post


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.user_1 = User.objects.create_user(username='test_user_1')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.guest_client = Client()
        cls.authorized_client_1 = Client()
        cls.authorized_client_1.force_login(cls.user)
        cls.authorized_client_2 = Client()
        cls.authorized_client_2.force_login(cls.user_1)

        cls.ADDRESSES = (
            ('posts:index', None, '/'),
            ('posts:group_list', (cls.group.slug,),
             f'/group/{cls.group.slug}/'),
            ('posts:profile', (cls.user.username,),
             f'/profile/{cls.user.username}/'),
            ('posts:post_detail', (cls.post.id,),
             f'/posts/{cls.post.id}/'),
            ('posts:post_edit', (cls.post.id,),
             f'/posts/{cls.post.id}/edit/'),
            ('posts:post_create', None, '/create/'),
        )

    def test_check_reverse(self):
        """Проверка соответствия ссылки и reverse(name)"""
        for name, args, url in self.ADDRESSES:
            self.assertEqual(reverse(name, args=args), url)

    def test_url_for_guest_user_exists_at_desired_location(self):
        """Доступность страниц любому пользователю."""
        for _, _, url in self.ADDRESSES:
            with self.subTest(address=url):
                response = self.guest_client.get(url, follow=True)
                if url == reverse(
                    'posts:post_edit', args=(self.post.id,)
                ):
                    self.assertRedirects(response, f'/auth/login/?next={url}')
                elif url == reverse('posts:post_create'):
                    self.assertRedirects(response, f'/auth/login/?next={url}')
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_for_authorized_user_exists_at_desired_location(self):
        """Доступность страниц
        авторизованному пользователю - не автору поста."""
        for _, _, url in self.ADDRESSES:
            with self.subTest(address=url):
                response = self.authorized_client_2.get(url, follow=True)
                if url == reverse(
                    'posts:post_edit', args=(self.post.id,)
                ):
                    self.assertRedirects(response, reverse(
                        'posts:post_detail', args=(self.post.id,)
                    ))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_for_authorized_author_exists_at_desired_location(self):
        """Доступность страниц
        авторизованному пользователю - автору поста."""
        for _, _, url in self.ADDRESSES:
            with self.subTest(address=url):
                response = self.authorized_client_1.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_exists_at_desired_location(self):
        """Страница /unexisting_page/ недоступна любому
        пользователю."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    args=(self.group.slug,)): 'posts/group_list.html',
            reverse('posts:profile',
                    args=(self.user.username,)): 'posts/profile.html',
            reverse('posts:post_detail',
                    args=(self.post.id,)): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    args=(self.post.id,)): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for address, template in templates_pages_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_1.get(address)
                self.assertTemplateUsed(response, template)

    def test_page_not_found_uses_correct_template(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')
