from django.test import TestCase
from django.urls import reverse
from django.urls import resolve
from ..views import about


class AboutTests(TestCase):
    def setUp(self):
        url = reverse('about')
        self.response = self.client.get(url)

    def test_about_view_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_about_url_resolves_about_view(self):
        view = resolve('/about/')
        self.assertEquals(view.func, about)

    def test_about_view_contains_link_to_home_page(self):
        homepage_url = reverse('home')
        self.assertContains(
            self.response, 'href="{0}"'.format(homepage_url))
