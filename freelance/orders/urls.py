from django.urls import path
from . import views
from .views import OrderProgressListView

urlpatterns = [
    path('client', views.orders_home, name='orders-home'), # пробую сделать путь /orders/client/
    path('create_order', views.create_order, name='create-order'),
    path('<int:pk>', views.OrderDetailView.as_view(), name='orders-detail'), # pk - название параметра
    # path('<int:order_id>/redirect/', OrderProgressRedirectView.as_view(), name='order-progress-redirect'),
    path('<int:order_id>/progress/', OrderProgressListView.as_view(), name='order-progress-list'),
    path('<int:pk>/update', views.OrderUpdateView.as_view(), name='order-update'),
    path('<int:order_id>/complete', views.complete_order_form, name='complete-order-form'),
    path('<int:pk>/delete', views.OrderDeleteView.as_view(), name='order-delete'),
    path('performer', views.perf_orders, name='perf-orders'),
    path('performer/<int:order_id>/progress/', views.perf_progress, name='perf-progress'),
    path('performer/search/', views.orders_search, name='orders-search'),
    path('performer/<int:order_id>/progress/<int:progress_id>/update', views.perf_progress, name='progress-update'),
    path('progress/<int:pk>/delete/', views.ProgressDeleteView.as_view(), name='progress-delete')
]