from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

def index(request):
    """
    Renders the custom premium landing environment for the platform.
    """
    return render(request, 'core/index.html')

def login_view(request):
    """Handles secure user session authentication routing."""
    if request.user.is_authenticated:
        return redirect('index')
        
    error = None
    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')
        
        user = authenticate(request, username=username_input, password=password_input)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            error = "Invalid username or password configuration."
            
    return render(request, 'core/login.html', {'error': error})

def register_view(request):
    """Processes signup data and spins up new active user records."""
    if request.user.is_authenticated:
        return redirect('index')
        
    error = None
    if request.method == 'POST':
        username_input = request.POST.get('username')
        email_input = request.POST.get('email')
        password_input = request.POST.get('password')
        confirm_input = request.POST.get('password_confirm')
        
        if password_input != confirm_input:
            error = "Passwords do not match."
        elif User.objects.filter(username=username_input).exists():
            error = "Username is already taken."
        elif User.objects.filter(email=email_input).exists():
            error = "An account with that email already exists."
        else:
            user = User.objects.create_user(username=username_input, email=email_input, password=password_input)
            login(request, user)
            return redirect('index')
            
    return render(request, 'core/register.html', {'error': error})

def logout_view(request):
    """Terminates user sessions securely."""
    logout(request)
    return redirect('index')

def profile_view(request, username):
    """Fetches targeted context payload data for user showcase cards."""
    profile_user = get_object_or_404(User, username=username)
    return render(request, 'core/profile.html', {'profile_user': profile_user})

@login_required
def edit_profile_view(request):
    """Processes modification state adjustments securely."""
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.save()
        
        profile = request.user.profile
        profile.role = request.POST.get('role')
        profile.bio = request.POST.get('bio')
        profile.company = request.POST.get('company')
        profile.job_title = request.POST.get('job_title')
        
        grad_year = request.POST.get('graduation_year')
        profile.graduation_year = int(grad_year) if grad_year and grad_year.isdigit() else None
        
        profile.linkedin_url = request.POST.get('linkedin_url')
        profile.github_url = request.POST.get('github_url')
        profile.save()
        
        return redirect('profile', username=request.user.username)
        
    return render(request, 'core/edit_profile.html')