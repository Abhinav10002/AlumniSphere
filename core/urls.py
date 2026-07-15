from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('directory/', views.directory_view, name='directory'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('connect/send/<str:username>/', views.send_connection_request, name='send_connection'),
    path('connect/accept/<str:username>/', views.accept_connection_request, name='accept_connection'),
]