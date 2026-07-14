
from tracemalloc import start

from django.db import models
from django.utils import timezone

class Car(models.Model):
    brand = models.CharField(max_length=100)

    model = models.CharField(max_length=100)

    year = models.IntegerField()

    rent_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    available = models.BooleanField(default=True)

    image = models.ImageField(
        upload_to='cars/',
        blank=True,
        null=True
    )

    fuel_type = models.CharField(
        max_length=20,
        default='Petrol'
    )

    transmission = models.CharField(
        max_length=20,
        default='Manual'
    )

    seats = models.IntegerField(
        default=5
    )

    location = models.CharField(
        max_length=100,
        default='Ghaziabad'
    )

    ac = models.BooleanField(
        default=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.brand} {self.model}"

class CarImage(models.Model):

    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(
        upload_to='car_gallery/'
    )

    def __str__(self):
        return f"{self.car.brand} {self.car.model}"

from django.contrib.auth.models import User

class Booking(models.Model):
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2    
    )
    
    estimated_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    refund_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    extra_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    BILLING_STATUS = [
        ("Settled", "Settled"),
        ("Refund Pending", "Refund Pending"),
        ("Extra Payment Pending", "Extra Payment Pending"),
        ("Refunded", "Refunded"),
    ]

    billing_status = models.CharField(
        max_length=30,
        choices=BILLING_STATUS,
        default="Settled"
    )
    
    coupon = models.ForeignKey(
        "Coupon",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    payment_order_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    payment_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("Pending", "Pending"),
            ("Paid", "Paid"),
            ("Failed", "Failed"),
            ("Refunded", "Refunded"),
        ],
        default="Pending"
    )

    booking_status = models.CharField(
        max_length=20,
        choices=[
            ("Pending Payment", "Pending Payment"),
            ("Upcoming", "Upcoming"),
            ("Active", "Active"),
            ("Completed", "Completed"),
            ("Cancelled", "Cancelled"),
        ],
        default="Pending Payment"
    )

    booked_at = models.DateTimeField(auto_now_add=True)
    
    pickup_time = models.DateTimeField(
        null=True,
        blank=True
    )

    return_time = models.DateTimeField(
        null=True,
        blank=True
    )
    
    def __str__(self):
        return f"{self.user.username} - {self.car}"
    
    @property
    def status(self):

        if self.booking_status == "Cancelled":
            return "Cancelled"

        if self.booking_status == "Completed":
            return "Completed"

        now = timezone.now()

        if now < self.start_time:
            return "Upcoming"

        elif self.start_time <= now <= self.end_time:
            return "Active"

        return "Completed"
    
class Coupon(models.Model):

    DISCOUNT_TYPE = [
        ("Fixed", "Fixed"),
        ("Percentage", "Percentage"),
    ]

    code = models.CharField(
        max_length=30,
        unique=True
    )

    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE
    )

    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    minimum_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    valid_from = models.DateTimeField()

    valid_until = models.DateTimeField()

    usage_limit = models.PositiveIntegerField(
        default=1
    )

    used_count = models.PositiveIntegerField(
        default=0
    )

    active = models.BooleanField(
        default=True
    )

    def __str__(self):

        return self.code

    
from django.contrib.auth.models import User

class Wishlist(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE
    )

    added_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.car}"
    
class Review(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE
    )

    rating = models.IntegerField()

    comment = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.car}"
    
class Contact(models.Model):
    name = models.CharField(max_length=100)

    email = models.EmailField()

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name
    
class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    profile_image = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )
    
    date_of_birth = models.DateField(

        blank=True,

        null=True

    )

    driving_license_number = models.CharField(

        max_length=50,

        blank=True

    )

    license_verified = models.BooleanField(

        default=False

    )
    
    license_image = models.ImageField(

        upload_to='licenses/',

        blank=True,

        null=True

    )

    def __str__(self):
        return self.user.username