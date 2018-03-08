from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from ..views import signup
from ..forms import SignUpForm


class SignUpTests(TestCase):
    def setUp(self):
        url = reverse('signup')
        self.response = self.client.get(url)

    def test_signup_status_code(self):
        self.assertEquals(self.response.status_code, 200)

    def test_signup_url_resolves_signup_view(self):
        view = resolve('/signup/')
        self.assertEquals(view.func, signup)

    def test_csrf(self):
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_contains_form(self):
        form = self.response.context.get('form')
        self.assertIsInstance(form, SignUpForm)

    def test_form_inputs(self):
        # this test validates that SignUpForm has same number of inputs as signup.html template.
        self.assertContains(self.response, '<input', 5)  # 1 csrf, 4 params
        self.assertContains(self.response, 'type="text"', 1)
        self.assertContains(self.response, 'type="email"', 1)
        self.assertContains(self.response, 'type="password"', 2)


class SuccessfulSignUpTests(TestCase):
    def setUp(self):
        url = reverse('signup')
        data = {
            'username': 'jdoe',
            'email': 'jdoe@localhost.localdomain',
            'password1': 'abcdef123456',
            'password2': 'abcdef123456'
        }
        self.response = self.client.post(url, data)
        self.home_url = reverse('home')

    def test_redirection(self):
        # valid submission redirects to homepage
        self.assertRedirects(self.response, self.home_url)

    def test_user_creation(self):
        # a user object gets created on valid submission
        self.assertTrue(User.objects.exists())

    def test_user_authentication(self):
        # when navigating to webpage other than '/signup', a user context
        # object is present on server side.
        response = self.client.get(self.home_url)
        user = response.context.get('user')
        self.assertTrue(user.is_authenticated)


class InvalidSignUpTests(TestCase):
    def setUp(self):
        url = reverse('signup')
        # send empty data
        self.response = self.client.post(url, {})

    def test_signup_status_code(self):
        # invalid data during signup should send the user back to signup form.
        self.assertEquals(self.response.status_code, 200)

    def test_form_errors(self):
        # form.errors is present when form is invalid.
        form = self.response.context.get('form')
        self.assertTrue(form.errors)

    def test_dont_create_user(self):
        # no user objects should exist as form was invalid.
        self.assertFalse(User.objects.exists())
