from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
from tours.models import Category, Tour, UserProfile, Booking, Comment

class TourStartupTestCase(TestCase):
    """
    набор тестов для проверки связей в бд и бизнес логики стартапа
    """

    def setUp(self):
        """Создание базовых тестовых данных перед каждым тестом."""
        # 1. Создаем пользователя
        self.user = User.objects.create_user(username="rider1", password="password123")
        
        # 2. Создаем 1-to-1 профиль
        self.profile = UserProfile.objects.create(user=self.user, phone="+77001112233")

        # 3. Создаем категории
        self.cat_horse = Category.objects.create(name="Конный")
        self.cat_walk = Category.objects.create(name="Пеший")
        self.cat_moto = Category.objects.create(name="Мото")

        # 4. Создаем тур
        self.tour1 = Tour.objects.create(
            title="Конное катание по горам",
            description="супер путешествие на 3 часа",
            price=15000.00
        )
        self.tour2 = Tour.objects.create(
            title="Мото-сафари",
            description="Скоростной заезд",
            price=25000.00
        )

    def test_one_to_one_relationship(self):
        """Тест связи 1 к 1: у пользователя есть ровно один профиль."""
        self.assertEqual(self.user.profile.phone, "+77001112233")
        self.assertEqual(self.profile.user, self.user)

    def test_many_to_many_relationship(self):
        """Тест связи многие ко многим: привязка категорий к турам."""
        # Добавляем две категории к первому туру
        self.tour1.categories.add(self.cat_horse, self.cat_walk)
        
        self.assertEqual(self.tour1.categories.count(), 2)
        self.assertIn(self.cat_horse, self.tour1.categories.all())
        self.assertIn(self.cat_walk, self.tour1.categories.all())
        
        # Проверяем обратную связь (у категории несколько туров)
        self.assertEqual(self.cat_horse.tours.count(), 1)

    def test_one_to_many_comments(self):
        """Тест связи 1 ко многим: один человек оставляет несколько комментариев."""
        comment1 = Comment.objects.create(user=self.user, tour=self.tour1, text="Было супер!")
        comment2 = Comment.objects.create(user=self.user, tour=self.tour1, text="Лошади очень послушные.")
        comment3 = Comment.objects.create(user=self.user, tour=self.tour2, text="В следующий раз пойду снова.")

        # У пользователя 3 комментария
        self.assertEqual(self.user.comments.count(), 3)
        # У тура1 2 комментария
        self.assertEqual(self.tour1.comments.count(), 2)

    def test_single_booking_per_datetime_success(self):
        """Тест успешной покупки тура на определенное время."""
        dt = timezone.make_aware(datetime(2026, 6, 1, 10, 0))
        booking = Booking.objects.create(user=self.user, tour=self.tour1, booking_datetime=dt)
        self.assertEqual(Booking.objects.count(), 1)

    def test_single_booking_per_datetime_failure(self):
        """
        Тест ошибки: 1 чел НЕ может купить второй тур на то же самое время.
        """
        dt = timezone.make_aware(datetime(2026, 6, 1, 10, 0))
        # Первая покупка
        Booking.objects.create(user=self.user, tour=self.tour1, booking_datetime=dt)

        # Попытка купить другой тур на то же самое время тем же пользователем
        duplicate_booking = Booking(user=self.user, tour=self.tour2, booking_datetime=dt)

        with self.assertRaises(ValidationError):
            duplicate_booking.save()