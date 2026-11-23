from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, LoginWithCaptchaForm


def register_view(request):
    """Регист юзера и автоматический вход в личный кабинет."""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('profile')
    else:
        form = RegistrationForm()
    return render(request, 'tours/register.html', {'form': form})


def login_view(request):
    """Авториз  юзера с проверкой логина, пароля и капчи."""
    if request.method == 'POST':
        form = LoginWithCaptchaForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('profile')
    else:
        form = LoginWithCaptchaForm(request)
    return render(request, 'tours/login.html', {'form': form})


def logout_view(request):
    """лог аут из аккаунта."""
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def profile_view(request):
    """кабинет юзера: профиль, забронированные туры и отзывы."""
    profile = getattr(request.user, 'profile', None)
    bookings = request.user.bookings.select_related('tour').all()
    comments = request.user.comments.select_related('tour').all()
    context = {
        'profile': profile,
        'bookings': bookings,
        'comments': comments,
    }
    return render(request, 'tours/profile.html', context)