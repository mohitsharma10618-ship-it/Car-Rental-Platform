from django.contrib import admin
from .models import Car, Booking, Coupon, Wishlist,Contact,CarImage,Review,Profile

admin.site.register(Car)
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
    "id",
    "user",
    "car",
    "booking_status",
    "coupon",
    "discount_amount",
    "pickup_time",
    "return_time",
)
# admin.site.register(Booking)
admin.site.register(Wishlist)
admin.site.register(Contact)
admin.site.register(CarImage)
admin.site.register(Review)
admin.site.register(Profile)
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):

    list_display = (
        "code",
        "discount_type",
        "discount_value",
        "minimum_amount",
        "used_count",
        "usage_limit",
        "active",
        "valid_until",
    )

    list_filter = (
        "active",
        "discount_type",
    )

    search_fields = (
        "code",
    )