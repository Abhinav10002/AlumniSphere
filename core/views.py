from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.db.models import Q
from core.models import Profile, Connection, Post, MentorshipSession, Message

@login_required
def index(request):
    """Renders the platform homepage with a reactive user discovery search system."""
    query = request.GET.get('q', '').strip()
    search_results = None

    if query:
        search_results = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:6]

    return render(request, 'core/index.html', {
        'search_results': search_results,
        'query': query
    })

def login_view(request):
    """Handles secure user authentication with message alerts."""
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        password_input = request.POST.get('password', '')
        
        user = authenticate(request, username=username_input, password=password_input)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, @{user.username}!")
            return redirect('index')
        else:
            messages.error(request, "Invalid username or password configuration.")
            
    return render(request, 'core/login.html')

def register_view(request):
    """Processes signup data and spins up new active user records."""
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        email_input = request.POST.get('email', '').strip()
        password_input = request.POST.get('password', '')
        confirm_input = request.POST.get('confirm_password', '') or request.POST.get('password_confirm', '')
        
        if not username_input or not email_input or not password_input:
            messages.error(request, "Please fill in all required fields.")
        elif password_input != confirm_input:
            messages.error(request, "Passwords do not match. Please re-enter them.")
        elif User.objects.filter(username=username_input).exists():
            messages.error(request, "Username is already taken. Please choose another.")
        elif User.objects.filter(email=email_input).exists():
            messages.error(request, "An account with that email address already exists.")
        else:
            user = User.objects.create_user(username=username_input, email=email_input, password=password_input)
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome to AlumniSphere, @{user.username}.")
            return redirect('index')
            
    return render(request, 'core/register.html')

def logout_view(request):
    """Terminates user sessions securely."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')

def profile_view(request, username):
    """Fetches profile context payload data and checks connection states."""
    profile_user = get_object_or_404(User, username=username)
    connection_status = None
    
    if request.user.is_authenticated and request.user != profile_user:
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
    """Processes profile modifications and file avatar uploads securely."""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        profile.role = request.POST.get('role', 'student')
        profile.bio = request.POST.get('bio', '')
        profile.company = request.POST.get('company', '')
        profile.job_title = request.POST.get('job_title', '')
        profile.location = request.POST.get('location', '')
        
        grad_year = request.POST.get('graduation_year')
        profile.graduation_year = int(grad_year) if grad_year and grad_year.isdigit() else None
        
        profile.linkedin_url = request.POST.get('linkedin_url', '')
        profile.github_url = request.POST.get('github_url', '')
        
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        profile.save()
        messages.success(request, "Your profile parameters have been updated.")
        return redirect('profile', username=request.user.username)
        
    return render(request, 'core/edit_profile.html', {'profile': profile})

def directory_view(request):
    """Queries active system user accounts with select_related optimization."""
    role_filter = request.GET.get('role_filter', '').strip()
    user_query = User.objects.all().select_related('profile').filter(is_active=True)
    
    if role_filter in ['alumni', 'student']:
        user_query = user_query.filter(profile__role=role_filter)
        
    return render(request, 'core/directory.html', {'members': user_query, 'active_filter': role_filter})

@login_required
def send_connection_request(request, username):
    """Initiates a connection request link to a target user."""
    receiver = get_object_or_404(User, username=username)
    if request.user != receiver:
        Connection.objects.get_or_create(sender=request.user, receiver=receiver, status='pending')
        messages.success(request, f"Connection request sent to @{username}.")
    return redirect('profile', username=username)

@login_required
def accept_connection_request(request, username):
    """Accepts an incoming pending connection request."""
    sender = get_object_or_404(User, username=username)
    conn = Connection.objects.filter(sender=sender, receiver=request.user, status='pending').first()
    if conn:
        conn.status = 'accepted'
        conn.save()
        messages.success(request, f"You are now connected with @{username}.")
    return redirect('profile', username=username)

@login_required
def feed_view(request):
    """Fetches post arrays with optimized foreign key joins."""
    posts = Post.objects.all().select_related('author', 'author__profile')
    return render(request, 'core/feed.html', {'posts': posts})

@login_required
def create_post_view(request):
    """Handles new post submissions including images and attachments."""
    if request.method == 'POST':
        content_input = request.POST.get('content', '').strip()
        image_input = request.FILES.get('image')
        file_attachment_input = request.FILES.get('file_attachment')

        if content_input or image_input or file_attachment_input:
            Post.objects.create(
                author=request.user,
                content=content_input,
                image=image_input,
                file_attachment=file_attachment_input
            )
            messages.success(request, "Your post has been published to the network feed.")
        else:
            messages.error(request, "Cannot submit an empty post.")

    return redirect('feed')

@login_required
def dashboard_view(request):
    """Generates the mentorship dashboard panel."""
    my_sessions_as_student = MentorshipSession.objects.filter(student=request.user).select_related('mentor')
    my_sessions_as_mentor = MentorshipSession.objects.filter(mentor=request.user).select_related('student')
    
    return render(request, 'core/dashboard.html', {
        'sessions_as_student': my_sessions_as_student,
        'sessions_as_mentor': my_sessions_as_mentor,
    })

@login_required
def book_session_view(request, username):
    """Processes mentorship booking requests."""
    mentor_user = get_object_or_404(User, username=username)
    
    if request.user == mentor_user:
        return redirect('profile', username=username)
        
    if request.method == 'POST':
        topic_input = request.POST.get('topic')
        datetime_input = request.POST.get('scheduled_for')
        
        if topic_input and datetime_input:
            MentorshipSession.objects.create(
                student=request.user,
                mentor=mentor_user,
                topic=topic_input,
                scheduled_for=datetime_input
            )
            messages.success(request, f"Mentorship session booked with @{mentor_user.username}!")
            return redirect('dashboard')
            
    return render(request, 'core/book_session.html', {'mentor': mentor_user})

@login_required
def update_session_status(request, session_id, action):
    """Updates mentorship session states."""
    session = get_object_or_404(MentorshipSession, id=session_id)
    
    if request.user == session.mentor:
        if action == 'approve':
            session.status = 'approved'
        elif action == 'complete':
            session.status = 'completed'
        elif action == 'cancel':
            session.status = 'canceled'
        session.save()
        
    return redirect('dashboard')

@login_required
def chat_dashboard(request):
    """Renders the inbox dashboard with active threads and user search."""
    query = request.GET.get('q', '').strip()
    search_results = None

    if query:
        search_results = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:8]

    sent_to = Message.objects.filter(sender=request.user).values_list('receiver', flat=True)
    received_from = Message.objects.filter(receiver=request.user).values_list('sender', flat=True)
    partner_ids = set(list(sent_to) + list(received_from))
    
    chat_partners = User.objects.filter(id__in=partner_ids).exclude(id=request.user.id)
    
    threads = []
    for partner in chat_partners:
        latest_message = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=partner)) |
            (Q(sender=partner) & Q(receiver=request.user))
        ).order_by('-timestamp').first()
        
        unread_count = Message.objects.filter(
            sender=partner,
            receiver=request.user,
            is_read=False
        ).count()
        
        threads.append({
            'partner': partner,
            'latest_message': latest_message,
            'unread_count': unread_count
        })
    
    threads.sort(key=lambda x: x['latest_message'].timestamp if x['latest_message'] else None, reverse=True)
    
    return render(request, 'core/chat_dashboard.html', {
        'threads': threads,
        'search_results': search_results,
        'query': query
    })

@login_required
def chat_room(request, username):
    """Handles 1:1 direct messaging threads between two users."""
    partner = get_object_or_404(User, username=username)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip() or request.POST.get('body', '').strip()
        if content:
            Message.objects.create(
                sender=request.user,
                receiver=partner,
                content=content
            )
        return redirect('chat_room', username=username)
    
    thread = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=partner)) |
        (Q(sender=partner) & Q(receiver=request.user))
    ).order_by('timestamp')
    
    Message.objects.filter(sender=partner, receiver=request.user, is_read=False).update(is_read=True)
    
    return render(request, 'core/chat_room.html', {
        'partner': partner,
        'thread': thread,
    })

def unread_messages_processor(request):
    """Globally injects the count of unread incoming messages."""
    if request.user.is_authenticated:
        count = Message.objects.filter(receiver=request.user, is_read=False).count()
        return {'unread_message_count': count, 'global_unread_count': count}
    return {'unread_message_count': 0, 'global_unread_count': 0}