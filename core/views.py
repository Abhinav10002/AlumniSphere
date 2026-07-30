from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.db.models import Q
from django.core.mail import send_mail
from django.utils.html import strip_tags

from core.models import (
    Profile,
    Connection,
    Post,
    MentorshipSession,
    Message,
    Comment,
    EmailOTP,
)


# ------------------------------------------------------------------
# Email OTP Helper Function
# ------------------------------------------------------------------

def send_otp_email(email, otp_code, purpose):
    """Sends a formatted HTML email containing the 6-digit OTP code."""
    subject = f"AlumniSphere Security Code: {otp_code}"
    
    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
        <h2 style="color: #3B826E; text-align: center;">AlumniSphere</h2>
        <p>Hello,</p>
        <p>Your verification code for <strong>{purpose}</strong> is:</p>
        <div style="background-color: #F4F6F2; padding: 15px; text-align: center; border-radius: 6px; margin: 20px 0;">
            <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #3B826E;">{otp_code}</span>
        </div>
        <p style="color: #666; font-size: 14px;">This code is valid for 10 minutes. Please do not share it with anyone.</p>
    </div>
    """
    
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email='AlumniSphere <abhinavkumar12102@gmail.com>',
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )


# ------------------------------------------------------------------
# Primary Navigation Views
# ------------------------------------------------------------------

@login_required
def index(request):
    """Renders platform homepage with user search capability."""
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


# ------------------------------------------------------------------
# Authentication & OTP Views
# ------------------------------------------------------------------

def login_view(request):
    """Stages user for 6-digit login OTP verification."""
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        password_input = request.POST.get('password', '')
        
        user = authenticate(request, username=username_input, password=password_input)
        if user is not None:
            # Save user in session prior to full authentication
            request.session['pending_user_id'] = user.id
            request.session['otp_target_email'] = user.email
            request.session['otp_purpose'] = 'login'

            # Generate and send OTP email
            otp_record = EmailOTP.objects.create(user=user, email=user.email, purpose='login')
            otp_record.generate_otp()
            send_otp_email(user.email, otp_record.otp, 'login')

            messages.info(request, f"Login OTP code sent to {user.email}")
            return redirect('verify_otp')
        else:
            messages.error(request, "Invalid username or password configuration.")
            
    return render(request, 'core/login.html')


def register_view(request):
    """Caches signup parameters and sends registration verification OTP."""
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
            # Cache registration parameters in session
            request.session['pending_registration'] = {
                'username': username_input,
                'email': email_input,
                'password': password_input,
            }

            # Generate and send OTP email
            otp_record = EmailOTP.objects.create(email=email_input, purpose='register')
            otp_record.generate_otp()
            send_otp_email(email_input, otp_record.otp, 'registration')

            request.session['otp_target_email'] = email_input
            request.session['otp_purpose'] = 'register'

            messages.info(request, f"Verification OTP sent to {email_input}")
            return redirect('verify_otp')
            
    return render(request, 'core/register.html')


def verify_otp_view(request):
    """Verifies submitted OTP code and completes login/registration."""
    target_email = request.session.get('otp_target_email')
    purpose = request.session.get('otp_purpose')

    if not target_email or not purpose:
        messages.error(request, "Session expired. Please start the login process again.")
        return redirect('login')

    if request.method == 'POST':
        user_otp = request.POST.get('otp', '').strip()

        otp_record = EmailOTP.objects.filter(
            email=target_email,
            purpose=purpose,
            is_verified=False
        ).order_by('-created_at').first()

        if otp_record and otp_record.is_valid() and otp_record.otp == user_otp:
            otp_record.is_verified = True
            otp_record.save()

            if purpose == 'register':
                reg_data = request.session.get('pending_registration')
                if reg_data:
                    user = User.objects.create_user(
                        username=reg_data['username'],
                        email=reg_data['email'],
                        password=reg_data['password']
                    )
                    Profile.objects.get_or_create(user=user)
                    login(request, user)

                    # Clean up session
                    del request.session['pending_registration']
                    del request.session['otp_target_email']
                    del request.session['otp_purpose']

                    messages.success(request, f"Account created successfully! Welcome to AlumniSphere, @{user.username}.")
                    return redirect('index')

            elif purpose == 'login':
                user_id = request.session.get('pending_user_id')
                if user_id:
                    user = User.objects.get(id=user_id)
                    login(request, user)

                    # Clean up session
                    del request.session['pending_user_id']
                    del request.session['otp_target_email']
                    del request.session['otp_purpose']

                    messages.success(request, f"Welcome back, @{user.username}!")
                    return redirect('index')
        else:
            messages.error(request, "Invalid or expired OTP code. Please try again.")

    return render(request, 'core/verify_otp.html', {'target_email': target_email})


def resend_otp_view(request):
    """Resends a fresh OTP code to the active target email."""
    target_email = request.session.get('otp_target_email')
    purpose = request.session.get('otp_purpose')

    if target_email and purpose:
        otp_record = EmailOTP.objects.create(email=target_email, purpose=purpose)
        otp_record.generate_otp()
        send_otp_email(target_email, otp_record.otp, purpose)
        messages.success(request, f"A new verification code has been sent to {target_email}.")
    else:
        messages.error(request, "Session expired. Please try logging in again.")
        return redirect('login')

    return redirect('verify_otp')


def logout_view(request):
    """Terminates user sessions securely."""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


# ------------------------------------------------------------------
# User Profile Views
# ------------------------------------------------------------------

def profile_view(request, username):
    """Fetches profile context, connection status, and user-published posts."""
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

    # Fetch all posts published by this specific user
    user_posts = Post.objects.filter(author=profile_user).select_related(
        'author', 'author__profile'
    ).prefetch_related('likes', 'saved_by', 'comments').order_by('-created_at')
                    
    return render(request, 'core/profile.html', {
        'profile_user': profile_user,
        'connection_status': connection_status,
        'user_posts': user_posts,
    })


@login_required
def edit_profile_view(request):
    """Processes profile modifications, avatar uploads, and CV/Resume attachments."""
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
            
        if 'cv' in request.FILES:
            profile.cv = request.FILES['cv']

        profile.save()
        messages.success(request, "Your profile and CV parameters have been updated.")
        return redirect('profile', username=request.user.username)
        
    return render(request, 'core/edit_profile.html', {'profile': profile})


@login_required
def directory_view(request):
    """Displays all platform members with search and role filtering."""
    profiles = Profile.objects.select_related('user').all()

    query = request.GET.get('q', '').strip()
    if query:
        profiles = profiles.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(job_title__icontains=query) |
            Q(company__icontains=query)
        )

    role_filter = request.GET.get('role', '').strip()
    if role_filter:
        profiles = profiles.filter(role__iexact=role_filter)

    return render(request, 'core/directory.html', {'profiles': profiles})


# ------------------------------------------------------------------
# Connections Views
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# Network Feed & Engagement Views
# ------------------------------------------------------------------

@login_required
def feed_view(request):
    """Fetches feed posts with preloaded comments and engagement metadata."""
    posts = Post.objects.all().select_related('author', 'author__profile').prefetch_related(
        'likes', 'saved_by', 'comments', 'comments__author', 'comments__author__profile'
    )
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
def toggle_like_post(request, post_id):
    """Toggles like status for a post."""
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return redirect('feed')


@login_required
def add_comment_view(request, post_id):
    """Submits a new comment on a post."""
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Comment.objects.create(
                post=post,
                author=request.user,
                content=content
            )
            messages.success(request, "Comment added.")
        else:
            messages.error(request, "Comment cannot be empty.")
    return redirect('feed')


@login_required
def toggle_save_post(request, post_id):
    """Bookmarks/Saves or unsaves a post."""
    post = get_object_or_404(Post, id=post_id)
    if request.user in post.saved_by.all():
        post.saved_by.remove(request.user)
        messages.info(request, "Post removed from your saved list.")
    else:
        post.saved_by.add(request.user)
        messages.success(request, "Post saved successfully.")
    return redirect('feed')


# ------------------------------------------------------------------
# Mentorship Dashboard Views
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# Direct Messaging & Context Processors
# ------------------------------------------------------------------

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
    """Handles 1:1 direct messaging threads restricted strictly to accepted connections."""
    partner = get_object_or_404(User, username=username)
    
    # Check connection status
    is_connected = Connection.objects.filter(
        (Q(sender=request.user, receiver=partner) | Q(sender=partner, receiver=request.user)),
        status='accepted'
    ).exists()

    if not is_connected:
        messages.warning(
            request, 
            f"You can only message @{username} once your connection request has been accepted."
        )
        return redirect('profile', username=username)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip() or request.POST.get('body', '').strip()
        image = request.FILES.get('image')
        file_attachment = request.FILES.get('file_attachment')

        if content or image or file_attachment:
            Message.objects.create(
                sender=request.user,
                receiver=partner,
                content=content,
                image=image,
                file_attachment=file_attachment
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
    """Globally injects the count of unread incoming messages into context templates."""
    if request.user.is_authenticated:
        count = Message.objects.filter(receiver=request.user, is_read=False).count()
        return {'unread_message_count': count, 'global_unread_count': count}
    return {'unread_message_count': 0, 'global_unread_count': 0}