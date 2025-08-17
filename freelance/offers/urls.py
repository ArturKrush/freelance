from django.urls import path
from . import views
from .views import agree_break

urlpatterns = [
    path('', views.offers_home, name='offers-home'),
    path('accept/', views.accept_offer, name='accept-offer'),
    path('reject/', views.reject_offer, name='reject-offer'),
    path('performer/', views.performer_offers, name='performer-offers'),
    path('<int:order_id>/create_offer/', views.create_offer, name='create-offer'),
    path('agree_break/', views.agree_break, name='agree-break'),
    path('disagree_break/', views.disagree_break, name='disagree-break'),
    path('<int:pk>/update', views.OfferUpdateView.as_view(), name='offer-update'),
    path('<int:pk>/delete', views.OfferDeleteView.as_view(), name='offer-delete'),
]