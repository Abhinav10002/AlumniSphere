from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Q, Max, OuterRef, Subquery, Count
from core.models import Profile, Connection, Post, MentorshipSession, Message

@login_required
def index(request):
    """
    Renders the platform homepage with a reactive user discovery 
    search system to instantly locate and open chat threads.
    """
    query = request.GET.get('q', '').strip()
    search_results = None

    # Process live network user searches
    if query:
        search_results = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:6] # Top 6 relevant results for card symmetry

    return render(request, 'core/index.html', {
        'search_results': search_results,
        'query': query
    })

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
    """Processes profile modifications and file avatar uploads securely."""
    # Safely gets the profile or creates it if missing
    profile, created = Profile.objects.get_or_create(user=request.user)
    
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
        
        # Handle file upload for profile picture
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        profile.save()
        
        return redirect('profile', username=request.user.username)
        
    return render(request, 'core/edit_profile.html', {'profile': profile})

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

@login_required
def feed_view(request):
    """Fetches full post arrays optimizing structural authors database extraction joins."""
    posts = Post.objects.all().select_related('author', 'author__profile')
    return render(request, 'core/feed.html', {'posts': posts})

@login_required
def create_post_view(request):
    """Interceptors form POST pipelines and publishes fresh updates onto timelines."""
    if request.method == 'POST':
        content_input = request.POST.get('content', '').strip()
        if content_input:
            Post.objects.create(author=request.user, content=content_input)
    return redirect('feed')

@login_required
def dashboard_view(request):
    """Generates the main central user management workspace panel for bookings handling."""
    my_sessions_as_student = MentorshipSession.objects.filter(student=request.user).select_related('mentor')
    my_sessions_as_mentor = MentorshipSession.objects.filter(mentor=request.user).select_related('student')
    
    context = {
        'sessions_as_student': my_sessions_as_student,
        'sessions_as_mentor': my_sessions_as_mentor,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def book_session_view(request, username):
    """Processes mentorship scheduling requests targeting specific alumni."""
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
            return redirect('dashboard')
            
    return render(request, 'core/book_session.html', {'mentor': mentor_user})

@login_required
def update_session_status(request, session_id, action):
    """Updates the execution lifecycle states of scheduled mentorship tracks securely."""
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
def chat_dashboard_view(request):
    """Displays a list of all distinct profiles the current logged-in user has actively messaged."""
    messages = Message.objects.filter(Q(sender=request.user) | Q(receiver=request.user))
    chat_partners_ids = set()
    
    for msg in messages:
        if msg.sender != request.user:
            chat_partners_ids.add(msg.sender.id)
        if msg.receiver != request.user:
            chat_partners_ids.add(msg.receiver.id)
            
    chat_partners = User.objects.filter(id__in=chat_partners_ids).select_related('profile')
    return render(request, 'core/chat_dashboard.html', {'chat_partners': chat_partners})

@login_required
def chat_room_view(request, username):
    """Handles an unrestricted one-to-one conversation stream between any two distinct network users."""
    partner = get_object_or_404(User, username=username)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(sender=request.user, receiver=partner, content=content)
            return redirect('chat_room', username=username)
            
    # Compile the ordered sequence of message communication logs
    thread = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=partner)) | 
        (Q(sender=partner) & Q(receiver=request.user))
    ).order_by('timestamp')
    
    # Update state matrices: Mark unread elements as viewed
    Message.objects.filter(sender=partner, receiver=request.user, is_read=False).update(is_read=True)
    
    return render(request, 'core/chat_room.html', {'partner': partner, 'thread': thread})

def unread_messages_processor(request):
    """Globally injects the count of unread incoming messages for the logged-in user."""
    if request.user.is_authenticated:
        count = Message.objects.filter(receiver=request.user, is_read=False).count()
        return {'unread_message_count': count}
    return {'unread_message_count': 0}

@login_required
def chat_room(request, username):
    partner = get_object_or_404(User, username=username)
    
    # Handle incoming message form submission
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                sender=request.user,
                receiver=partner,
                content=content
            )
        return redirect('chat_room', username=username)
    
    # GET: Retrieve message history thread
    messages = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=partner)) |
        (Q(sender=partner) & Q(receiver=request.user))
    ).order_by('timestamp')
    
    # NOTIFICATION TRIGGER: Clear all unread messages sent by this partner to the logged-in user
    Message.objects.filter(
        sender=partner, 
        receiver=request.user, 
        is_read=False
    ).update(is_read=True)
    
    return render(request, 'core/chat_room.html', {
        'partner': partner,
        'messages': messages,
    })

@login_required
def chat_dashboard(request):
    """
    Renders the inbox dashboard with an integrated search filter to find 
    other alumni and view active message threads.
    """
    query = request.GET.get('q', '').strip()
    search_results = None

    # Handle Search Queries
    if query:
        search_results = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:8]  # Limit to top 8 matches for clean UI

    # Active Threads Query Logic
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