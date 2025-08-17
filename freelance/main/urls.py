from django.urls import path
from . import views

urlpatterns = [
    # path('', views.index, name='home'),
    path('client_home', views.index, name='client-home'),
    path('performers', views.performers_search, name='performers-search'),
    path('performers/<int:pk>', views.PerformersDetailView.as_view(), name='performers-detail'),
    path('client_profile/', views.get_curr_client, name='client-profile-own'),
    path('client_profile/<int:client_id>/', views.get_curr_client, name='client-profile'),
    path('client_profile/update/<int:pk>/', views.ProfileUpdateView.as_view(), name='update-client-profile'),
    path('rating', views.ratings_view, name='rating'),
    path('performers/search/', views.performers_search, name='performers-search'),
    path('performer_home', views.performer_index, name='performer-home'),
    path('performer_profile', views.get_curr_performer, name='performer-profile-own'),
    path('admin_home/', views.admin_index, name='admin-home'),
    path('admin_view/warned_users', views.warned_users, name='warned-users'),
    path('performers_admin_view/', views.performers_admin_view, name='performers-admin-view'),
    path('admin/ban_user/', views.ban_user, name='ban-user'),
    path('admin/unban_user/', views.unban_user, name='unban-user'),
    path('admin/clients_search', views.clients_search, name='clients-search'),
    path('admin_profile/', views.admin_profile, name='admin-profile'),
    path('admin_profile/update', views.AdminProfileUpdateView.as_view(), name='update-admin-profile')
]