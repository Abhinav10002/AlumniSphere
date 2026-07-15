from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import models
from core.models import Profile, Connection

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
    """Fetches profile context payload data and checks real-time connection status states."""
    profile_user = get_object_or_404(User, username=username)
    connection_status = None
    
    if request.user.is_authenticated and request.user != profile_user:
        # Check if a connection record exists between these two users
        conn = Connection.objects.filter(
            (models.Q(sender=request.user, receiver=profile_user) | 
             models.Q(sender=profile_user, receiver=request.user))
        ).first()
        
        if conn:
            if conn.status == 'accepted':
                connection_status = 'connected'
            elif conn.status == 'pending':
                if conn.sender == request.user:
                    connection_status = 'sent_pending'
                else:
                    connection_status = 'received_pending'
                    
    return render(request, 'core/profile.html', {
        'profile_user': profile_user,
        'connection_status': connection_status
    })

@login_required
def edit_profile_view(request):
    """Processes modification state adjustments securely."""
    # Safely gets the profile or creates it if it's missing in the DB
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.save()
        
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

def directory_view(request):
    """
    Queries active system user accounts, optimizing data extraction paths
    using select_related execution parameters to solve the N+1 problem.
    """
    role_filter = request.GET.get('role_filter', '').strip()
    
    user_query = User.objects.all().select_related('profile').filter(is_active=True)
    
    if role_filter in ['alumni', 'student']:
        user_query = user_query.filter(profile__role=role_filter)
        
    context = {
        'members': user_query,
        'active_filter': role_filter
    }
    return render(request, 'core/directory.html', context)

@login_required
def send_connection_request(request, username):
    """Initiates a connection request link to a target user."""
    receiver = get_object_or_404(User, username=username)
    if request.user != receiver:
        Connection.objects.get_or_create(sender=request.user, receiver=receiver, status='pending')
    return redirect('profile', username=username)

@login_required
def accept_connection_request(request, username):
    """Accepts an incoming pending connection request."""
    sender = get_object_or_404(User, username=username)
    conn = Connection.objects.filter(sender=sender, receiver=request.user, status='pending').first()
    if conn:
        conn.status = 'accepted'
        conn.save()
    return redirect('profile', username=username)