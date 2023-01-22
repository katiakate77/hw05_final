from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_author_url_exists_at_desired_location(self):
        """Проверка доступности адреса /about/author/."""
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_url_uses_correct_template(self):
        """Проверка шаблона для адреса /about/author/."""
        response = self.guest_client.get('/about/author/')
        self.assertTemplateUsed(response, 'about/author.html')

    def test_author_page_uses_correct_template(self):
        """Проверка шаблона для reverse('about:author')."""
        response = self.guest_client.get(reverse('about:author'))
        self.assertTemplateUsed(response, 'about/author.html')
