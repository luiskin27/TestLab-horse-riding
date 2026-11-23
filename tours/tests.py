from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
from captcha.models import CaptchaStore
from tours.models import Category, Tour, UserProfile, Booking, Comment


class TourStartupTestCase(TestCase):
    """Тесты связей БД и ограничений бронирования."""

    def setUp(self):
        self.user = User.objects.create_user(username="rider1", password="password123")
        self.profile = UserProfile.objects.create(user=self.user, phone="+77001112233")
        self.cat_horse = Category.objects.create(name="Конный")
        self.cat_walk = Category.objects.create(name="Пеший")
        self.cat_moto = Category.objects.create(name="Мото")
        self.tour1 = Tour.objects.create(
            title="Конная прогулка по горам",
            description="Отличное путешествие на 3 часа",
            price=15000.00
        )
        self.tour2 = Tour.objects.create(
            title="Мото-сафари",
            description="Скоростной заезд",
            price=25000.00
        )

    def test_one_to_one_relationship(self):
        """Связь 1 к 1: профиль пользователя"""
        self.assertEqual(self.user.profile.phone, "+77001112233")

    def test_many_to_many_relationship(self):
        """Связь многие ко многим: категории туров"""
        self.tour1.categories.add(self.cat_horse, self.cat_walk)
        self.assertEqual(self.tour1.categories.count(), 2)

    def test_one_to_many_comments(self):
        """Связь 1 ко многим: несколько комментариев от одного пользователя"""
        Comment.objects.create(user=self.user, tour=self.tour1, text="Было супер!")
        Comment.objects.create(user=self.user, tour=self.tour2, text="Отличный маршрут!")
        self.assertEqual(self.user.comments.count(), 2)

    def test_single_booking_per_datetime_success(self):
        """Успешная покупка 1 тура на конкретное время"""
        dt = timezone.make_aware(datetime(2026, 6, 1, 10, 0))
        Booking.objects.create(user=self.user, tour=self.tour1, booking_datetime=dt)
        self.assertEqual(Booking.objects.count(), 1)

    def test_single_booking_per_datetime_failure(self):
        """Запрет покупки второго тура на то же время"""
        dt = timezone.make_aware(datetime(2026, 6, 1, 10, 0))
        Booking.objects.create(user=self.user, tour=self.tour1, booking_datetime=dt)
        duplicate_booking = Booking(user=self.user, tour=self.tour2, booking_datetime=dt)
        with self.assertRaises(ValidationError):
            duplicate_booking.save()


class AuthCaptchaAndProfileTestCase(TestCase):
    """Тесты регистрации, авторизации с проверкой капчи и личного кабинета."""

    def setUp(self):
        self.username = "test_rider"
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            username=self.username,
            email="rider@example.com",
            password=self.password
        )
        self.profile = UserProfile.objects.create(user=self.user, phone="+996555123456")

        self.tour = Tour.objects.create(
            title="Горный конный тур",
            description="Маршрут к озеру",
            price=12000.00
        )
        self.booking = Booking.objects.create(
            user=self.user,
            tour=self.tour,
            booking_datetime=timezone.make_aware(datetime(2026, 7, 15, 11, 0))
        )
        self.comment = Comment.objects.create(
            user=self.user,
            tour=self.tour,
            text="Незабываемая поездка!"
        )

    def test_registration_success(self):
        """Регистрация нового пользователя и автоматическое создание профиля"""
        response = self.client.post(reverse('register'), {
            'username': 'new_rider',
            'email': 'new@example.com',
            'phone': '+996700999888',
            'password': 'NewPassword123!',
            'password_confirm': 'NewPassword123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profile'))
        created_user = User.objects.get(username='new_rider')
        self.assertEqual(created_user.profile.phone, '+996700999888')

    def test_registration_password_mismatch(self):
        """Ошибка регистрации при несовпадении паролей"""
        response = self.client.post(reverse('register'), {
            'username': 'bad_rider',
            'email': 'bad@example.com',
            'phone': '+996700111222',
            'password': 'Password123!',
            'password_confirm': 'DifferentPass456!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='bad_rider').exists())

    def test_login_fails_with_invalid_captcha(self):
        """Запрет входа при вводе неверной капчи"""
        # Открываем страницу входа, чтобы сгенерировалась реальная капча
        self.client.get(reverse('login'))
        captcha_obj = CaptchaStore.objects.latest('id')

        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password,
            'captcha_0': captcha_obj.hashkey,
            'captcha_1': 'WRONG_CODE',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_fails_with_empty_captcha(self):
        """Запрет входа с пустым полем капчи"""
        self.client.get(reverse('login'))
        captcha_obj = CaptchaStore.objects.latest('id')

        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password,
            'captcha_0': captcha_obj.hashkey,
            'captcha_1': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_success_with_valid_captcha(self):
        """Успешный вход при правильном пароле и верной капче"""
        self.client.get(reverse('login'))
        captcha_obj = CaptchaStore.objects.latest('id')

        response = self.client.post(reverse('login'), {
            'username': self.username,
            'password': self.password,
            'captcha_0': captcha_obj.hashkey,
            'captcha_1': captcha_obj.response,
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profile'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_profile_requires_login(self):
        """Защита личного кабинета: редирект неавторизованного пользователя на вход"""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_profile_displays_user_data_bookings_and_comments(self):
        """Личный кабинет отображает телефон, бронирования и комментарии пользователя"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.username)
        self.assertContains(response, "+996555123456")
        self.assertContains(response, "Горный конный тур")
        self.assertContains(response, "Незабываемая поездка!")

    def test_logout_closes_access_to_profile(self):
        """Выход из аккаунта закрывает доступ к личному кабинету"""
        self.client.force_login(self.user)
        self.client.get(reverse('logout'))
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)