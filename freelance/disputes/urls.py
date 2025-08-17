from django.urls import path
from . import views
from .views import PerformersReviewsListView, PerformersPortfolioListView, create_review, user_complaints, user_portfolio, PortfolioDeleteView

urlpatterns = [
    # path('reviews', views.reviews_home, name='reviews-home'),
    path('<int:performer_id>/reviews/', PerformersReviewsListView.as_view(), name='performers-reviews'),
    path('<int:performer_id>/portfolio/', PerformersPortfolioListView.as_view(), name='performers-portfolio'),
    path('performer/<int:performer_id>/add-review/', create_review, name='create-review'),
    path('user_profile/complaints/<int:user_id>', user_complaints, name='user-complaints'),
    path('performer/user_portfolio/', user_portfolio, name='user-portfolio'),
    path('admin_view/', views.complaints_admin_view, name='complaints-admin-view'),
    path('accept_complaint/', views.accept_complaint, name='accept-complaint'),
    path('reject_complaint/', views.reject_complaint, name='reject-complaint'),
    path('portfolio/delete/<int:pk>', PortfolioDeleteView.as_view(), name='delete-portfolio'),
]