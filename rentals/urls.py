from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
    path('book/<int:car_id>/', views.book_car, name='book_car'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path(
        'cancel-booking/<int:booking_id>/',
        views.cancel_booking,
        name='cancel_booking'
    ),
    path('dashboard/', views.dashboard, name='dashboard'),
    path(
        'wishlist/add/<int:car_id>/',
        views.add_to_wishlist,
        name='add_to_wishlist'
    ),
    
    path(
        'my-wishlist/',
        views.my_wishlist,
        name='my_wishlist'
    ),
    
    path(
        'wishlist/remove/<int:wishlist_id>/',
        views.remove_from_wishlist,
        name='remove_from_wishlist'
    ),
    
    path(
        'contact/',
        views.contact_view,
        name='contact'
    ),
    
    path(
        'about/',
        views.about_view,
        name='about'
    ),
    
    path(
    "booking/<int:booking_id>/edit/",
    views.edit_booking,
    name="edit_booking",
),
    
path(
    "booking/<int:booking_id>/",
    views.booking_detail,
    name="booking_detail",
),

path(
    "apply-coupon/",
    views.apply_coupon,
    name="apply_coupon",
),
    
path(
    "booking/<int:booking_id>/extend/",
    views.extend_booking,
    name="extend_booking",
),

path(
    "booking/<int:booking_id>/start/",
    views.start_trip,
    name="start_trip",
),

path(
    "booking/<int:booking_id>/end/",
    views.end_trip,
    name="end_trip",
),
        
path(
    "booking/<int:booking_id>/payment/",
    views.payment_page,
    name="payment_page",
),  
path(
    "payment-success/",
    views.payment_success,
    name="payment_success",
),  
]