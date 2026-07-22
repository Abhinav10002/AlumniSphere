from django.urls import path
from . import views

urlpatterns = [
    # --- Authentication Views Matrix ---
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # --- Profile & Networking Engine Views ---
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/<str:username>/connect/', views.send_connection_request, name='send_connection_request'),
    path('profile/<str:username>/accept/', views.accept_connection_request, name='accept_connection_request'),
    
    # --- Directory & Activity Stream Core Views ---
    path('directory/', views.directory_view, name='directory'),
    path('feed/', views.feed_view, name='feed'),
    path('feed/post/', views.create_post_view, name='create_post'),
    
    # --- Mentorship Tracking System Module ---
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/<str:username>/book/', views.book_session_view, name='book_session'),
    path('session/<int:session_id>/<str:action>/', views.update_session_status, name='update_session_status'),

    # --- Real-Time Messaging Workspace ---
    path('messages/', views.chat_dashboard, name='chat_dashboard'),
    path('messages/t/<str:username>/', views.chat_room, name='chat_room'),
]