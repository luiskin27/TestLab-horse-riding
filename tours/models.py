from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Category(models.Model):
    """
    Модель категории тура (например: 'Конный', 'Пеший', 'Мото').

    :param name: Уникальное название категории.
    """
    name = models.CharField(max_length=50, unique=True, verbose_name="Название категории")

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    """
    Модель профиля пользователя.
    Демонстрирует связь 1 к 1 (OneToOneField) с дефолтной моделью User.

    :param user: Ссылка на стандартного пользователя Django.
    :param phone: Номер телефона.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, verbose_name="Номер телефона")

    def __str__(self):
        return f"Профиль {self.user.username}"


class Tour(models.Model):
    """
    Модель конного/туристического маршрута.
    Демонстрирует связь многие ко многим (ManyToManyField) с категорий.

    :param title: Название тура.
    :param description: Описание тура.
    :param price: Стоимость тура.
    :param categories: Список категорий, к которым относится тур.
    """
    title = models.CharField(max_length=200, verbose_name="Название тура")
    description = models.TextField(verbose_name="Описание тура")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    categories = models.ManyToManyField(Category, related_name="tours", verbose_name="Категории")

    def __str__(self):
        return self.title


class Booking(models.Model):
    """
    Модель покупки/бронирования тура на определенный день и время.
    Содержит правило: 1 человек может купить только 1 тур на один конкретный слот (дата и время).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="bookings")
    booking_datetime = models.DateTimeField(verbose_name="Дата и время тура")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'booking_datetime'],
                name='unique_user_booking_per_datetime'
            )
        ]

    def clean(self):
        """
        Проверка бизнес-логики: пользователь не может забронировать второй тур на то же время.
        """
        existing = Booking.objects.filter(user=self.user, booking_datetime=self.booking_datetime)
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        if existing.exists():
            raise ValidationError("Вы уже забронировали тур на это время!")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.tour.title} ({self.booking_datetime})"


class Comment(models.Model):
    """
    Модель отзыва/комментария к туру.
    Демонстрирует связь 1 ко многим (ForeignKey):
    1 чел может оставить нескл комментов к турам.

    :param user: автор комментария
    :param tour: тур, к которому относится комментарий
    :param text: текст отзыва
    :param created_at: дата публикации
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Отзыв от {self.user.username} к {self.tour.title}"