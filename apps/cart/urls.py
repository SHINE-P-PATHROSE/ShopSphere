"""Cart web URLs."""
from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.CartView.as_view(), name='cart'),
    path('add/', views.AddToCartView.as_view(), name='add'),
    path('update/<int:item_id>/', views.UpdateCartItemView.as_view(), name='update'),
    path('remove/<int:item_id>/', views.RemoveCartItemView.as_view(), name='remove'),
    path('save/<int:item_id>/', views.ToggleSaveForLaterView.as_view(), name='save_for_later'),
]
