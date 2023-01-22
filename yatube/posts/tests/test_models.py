from django.contrib.auth import get_user_model
from django.test import TestCase
from django.conf import settings

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_post_model_has_correct_object_name(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = self.post
        expected_object_name_post = post.text[:settings.POST_LENGTH]
        self.assertEqual(expected_object_name_post, str(post))

    def test_group_model_has_correct_object_name(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = self.group
        expected_object_name_group = group.title
        self.assertEqual(expected_object_name_group, str(group))
