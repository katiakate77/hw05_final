from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group


User = get_user_model()


class PostFormTests(TestCase):
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
            author=cls.user,
            text='Тестовый текст 2',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        set_1 = {post for post in Post.objects.all()}
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        set_2 = {post for post in Post.objects.all()}
        set_diff = set_2.difference(set_1)
        self.assertRedirects(
            response, reverse('posts:profile',
                              args=(self.user.username,))
        )
        self.assertEqual(len(set_diff), 1)
        created_post_obj = list(set_diff)[0]
        self.assertEqual(created_post_obj.text, form_data['text'])
        self.assertEqual(created_post_obj.group, self.group)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        form_data = {
            'text': 'Отредактированный тестовый текст 2',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=(self.post.id,)))
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, form_data['text'])
        self.assertEqual(self.post.group, self.group)
