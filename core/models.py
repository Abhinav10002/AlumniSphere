from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import random
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Profile(models.Model):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('alumni', 'Alumni'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', blank=True)
    bio = models.TextField(max_length=500, blank=True)

    cv = models.FileField(upload_to='cvs/', blank=True, null=True)
    
    # Professional details
    graduation_year = models.IntegerField(null=True, blank=True)
    company = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    # Social channels
    linkedin_url = models.URLField(max_length=200, blank=True)
    github_url = models.URLField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# Automation Signals
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Connection(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_connections')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_connections')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.status})"

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    file_attachment = models.FileField(upload_to='post_attachments/', blank=True, null=True)
    
    # New Engagement Fields
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    saved_by = models.ManyToManyField(User, related_name='saved_posts', blank=True)

    class Meta:
        ordering = ['-created_at']  

    def __str__(self):
        return f"Post by {self.author.username} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def total_likes(self):
        return self.likes.count()

    def total_comments(self):
        return self.comments.count()


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments')
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on Post #{self.post.id}"
    
class MentorshipSession(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booked_sessions')
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='guided_sessions')
    topic = models.CharField(max_length=255)
    scheduled_for = models.DateTimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_for']

    def __str__(self):
        return f"Session: {self.student.username} with {self.mentor.username} on {self.scheduled_for.strftime('%Y-%m-%d %H:%M')}"
    
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    file_attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username} at {self.timestamp}"

class EmailOTP(models.Model):
    PURPOSE_CHOICES = (
        ('register', 'Registration'),
        ('login', 'Login'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='otps')
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def generate_otp(self):
        """Generates a random 6-digit numeric OTP string."""
        self.otp = f"{random.randint(100000, 999999)}"
        self.save()

    def is_valid(self):
        """Checks if OTP is unverified and created within the last 10 minutes."""
        now = timezone.now()
        return not self.is_verified and (now - self.created_at) < timedelta(minutes=10)

    def __str__(self):
        return f"{self.email} - {self.otp} ({self.purpose})"