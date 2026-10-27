from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, ProfileUpdateForm
from .models import Profile

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Ensure profile exists
            Profile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f"Welcome to Fitora, {user.username}! Your fitness journey begins today.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below to register.")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form, 'title': 'Create Your Account'})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
        
    return render(request, 'accounts/login.html', {'form': form, 'title': 'Sign In to Fitora'})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out of Fitora. See you next time!")
    return redirect('home')

@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your daily nutrition goals have been updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the values below.")
    else:
        form = ProfileUpdateForm(instance=profile)
        
    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile,
        'title': 'My Nutrition Goals'
    })
