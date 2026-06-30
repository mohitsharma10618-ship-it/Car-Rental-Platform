from time import timezone

from django.shortcuts import render, get_object_or_404, redirect
from .models import Car, Wishlist
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .models import Booking,Coupon
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from django.db.models import Avg
from .models import Review
from rentals.models import Profile
from django.utils import timezone
from decimal import Decimal
from django.http import JsonResponse
import razorpay
from django.conf import settings



def home(request):

    query = request.GET.get('q')

    min_price = request.GET.get('min_price')

    max_price = request.GET.get('max_price')

    brand = request.GET.get('brand')

    fuel_type = request.GET.get('fuel_type')

    transmission = request.GET.get('transmission')

    cars = Car.objects.all()

    wishlist_car_ids = []

    if request.user.is_authenticated:
        wishlist_car_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list(
            'car_id',
            flat=True
        )

    if query:
        cars = cars.filter(
            Q(brand__icontains=query) |
            Q(model__icontains=query)
        )

    if min_price:
        cars = cars.filter(
            rent_per_hour__gte=min_price
        )

    if max_price:
        cars = cars.filter(
            rent_per_hour__lte=max_price
        )

    if brand:
        cars = cars.filter(
            brand__iexact=brand
        )

    if fuel_type:
        cars = cars.filter(
            fuel_type__iexact=fuel_type
        )

    if transmission:
        cars = cars.filter(
            transmission__iexact=transmission
        )

    brands = Car.objects.values_list(
        'brand',
        flat=True
    ).distinct()

    return render(
        request,
        'home.html',
        {
            'cars': cars,
            'wishlist_car_ids': wishlist_car_ids,
            'brands': brands
        }
    )

from .models import Wishlist

def car_detail(request, car_id):

    car = get_object_or_404(Car, id=car_id)
    
    can_review = False

    if request.user.is_authenticated:

        from django.utils import timezone

        can_review = Booking.objects.filter(
            user=request.user,
            car=car,
            end_time__lt=timezone.now()
        ).exists()

    if (
        request.method == "POST"
        and request.user.is_authenticated
        and can_review
    ):

        rating = request.POST.get('rating')

        comment = request.POST.get('comment')
        
        existing_review = Review.objects.filter(
            user=request.user,
            car=car
        ).exists()

        if existing_review:
            return redirect(
                'car_detail',
                car_id=car.id
            )

        Review.objects.create(
            user=request.user,
            car=car,
            rating=rating,
            comment=comment
        )

        return redirect(
            'car_detail',
            car_id=car.id
        )

    is_in_wishlist = False

    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(
            user=request.user,
            car=car
        ).exists()

    reviews = Review.objects.filter(
        car=car
    ).order_by('-created_at')

    average_rating = reviews.aggregate(
        Avg('rating')
    )['rating__avg']
    
    car_images=car.images.all()

    context = {
        'car': car,
        'is_in_wishlist': is_in_wishlist,
        'reviews': reviews,
        'average_rating': average_rating,
        'car_images': car_images,
        'can_review' : can_review
    }

    return render(
        request,
        'car_detail.html',
        context
    )

@login_required
def book_car(request, car_id):
    
    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if not profile.license_verified:

        messages.warning(
            request,
            "Please wait for driving license verification before booking a car."
        )
        return redirect('profile')
    
    profile, created = Profile.objects.get_or_create(
        user=request.user
    )
    
    car = get_object_or_404(Car, id=car_id)
    
    now = timezone.now()

    bookings = Booking.objects.filter(car=car)

    for booking in bookings:

        if booking.booking_status != "Cancelled":

            if booking.start_time <= now < booking.end_time:

                booking.booking_status = "Active"

            elif now >= booking.end_time:

                booking.booking_status = "Completed"

            else:

                booking.booking_status = "Upcoming"

            booking.save()

    if request.method == "POST":
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        
        coupon_code = request.POST.get("coupon_code", "").strip().upper()

        start = timezone.make_aware(
            datetime.strptime(start_time, "%Y-%m-%dT%H:%M")
        )

        end = timezone.make_aware(
            datetime.strptime(end_time, "%Y-%m-%dT%H:%M")
        )
        
        if start < timezone.now():

            messages.error(
                request,
                "You cannot book a car in the past."
            )

            return redirect(
                "book_car",
                car_id=car.id
            )

        if end <= start:

            messages.error(
                request,
                "End time must be later than the start time."
            )

            return redirect(
                "book_car",
                car_id=car.id
            )

        hours = (end - start).total_seconds() / 3600
        
        if hours < 1:

            messages.error(
                request,
                "Minimum booking duration is 1 hour."
            )

            return redirect("book_car", car_id=car.id)

        total_amount = hours * float(car.rent_per_hour)
        
        discount_amount = 0
        coupon = None

        if coupon_code:

            try:

                coupon = Coupon.objects.get(
                    code=coupon_code,
                    active=True
                )

                now = timezone.now()

                if (
                    coupon.valid_from <= now <= coupon.valid_until
                    and coupon.used_count < coupon.usage_limit
                    and total_amount >= float(coupon.minimum_amount)
                ):

                    if coupon.discount_type == "Fixed":

                        discount_amount = float(coupon.discount_value)

                    else:

                        discount_amount = (
                            total_amount * float(coupon.discount_value) / 100
                        )

                    if discount_amount > total_amount:

                        discount_amount = total_amount

                    total_amount -= discount_amount

                else:

                    coupon = None

            except Coupon.DoesNotExist:

                coupon = None
        

        conflicting_booking = Booking.objects.filter(
            car=car
        ).exclude(
            booking_status="Cancelled"
        ).filter(
            start_time__lt=end,
            end_time__gt=start
        ).first()

        if conflicting_booking:

            local_start = timezone.localtime(conflicting_booking.start_time)
            local_end = timezone.localtime(conflicting_booking.end_time)

            messages.error(
                request,
                f"This car is already booked from "
                f"{local_start.strftime('%d %b %Y %I:%M %p')} "
                f"to "
                f"{local_end.strftime('%I:%M %p')}. "
                f"Please select another time slot."
            )

            return redirect("book_car", car_id=car.id)

        booking = Booking.objects.create(
            user=request.user,
            car=car,
            start_time=start,
            end_time=end,
            total_amount=total_amount,
            coupon=coupon,
            discount_amount=discount_amount
        )
        
        if coupon:

            coupon.used_count += 1
            coupon.save()
        send_mail(
            subject='Car Booking Confirmation',
            message=f'''
        Hello {request.user.username},

        Your booking has been confirmed.

        Car: {car.brand} {car.model}

        Start Time: {start}

        End Time: {end}

        Total Amount: ₹{total_amount}

        Thank you for choosing our Car Rental Platform.
        ''',
            from_email='mohitsharma10618@gmail.com',
            recipient_list=[request.user.email],
            fail_silently=False,
        )
        return redirect('/')
    
    booked_slots = Booking.objects.filter(
        car=car,
        booking_status__in=["Upcoming", "Active"],
        end_time__gt=timezone.now()
    ).order_by("start_time")
    
    for booking in booked_slots:

        booking.duration_hours = (
            booking.end_time - booking.start_time
        ).total_seconds() / 3600
        
    booked_slots_json = []

    for booking in booked_slots:

        booked_slots_json.append({
            "start_time": booking.start_time.isoformat(),
            "end_time": booking.end_time.isoformat(),
            "status": booking.booking_status,
        })
    

    return render(request, "book_car.html", {"car": car, "booked_slots": booked_slots,"booked_slots_json": booked_slots_json,})

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user)
    return render(
        request,
        'my_bookings.html',
        {'bookings': bookings}
    )
    
    
@login_required
def cancel_booking(request, booking_id):
    booking = Booking.objects.get(
        id=booking_id,
        user=request.user
    )
    if booking.booking_status == "Cancelled":

        messages.info(
            request,
            "This booking has already been cancelled."
        )

        return redirect("my_bookings")

    send_mail(
        subject='Car Booking Cancelled',
        message=f'''
Hello {request.user.username},

Your booking has been cancelled successfully.

Car: {booking.car.brand} {booking.car.model}

Start Time: {booking.start_time}

End Time: {booking.end_time}

Amount: ₹{booking.total_amount}

We hope to serve you again soon.

Car Rental Platform
''',
        from_email='mohitsharma10618@gmail.com',
        recipient_list=[request.user.email],
        fail_silently=False,
    )

    booking.booking_status = "Cancelled"
    booking.save()
    
    messages.success(

        request,

        "Your booking has been cancelled successfully."

    )

    return redirect('my_bookings')


from django.db.models import Sum

@login_required
def dashboard(request):

    total_cars = Car.objects.count()

    total_bookings = Booking.objects.count()

    total_revenue = (
        Booking.objects.aggregate(
            Sum('total_amount')
        )['total_amount__sum']
        or 0
    )

    context = {
        'total_cars': total_cars,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
    }

    return render(
        request,
        'dashboard.html',
        context
    )
from .models import Wishlist
   
@login_required
def add_to_wishlist(request, car_id):

    car = get_object_or_404(
        Car,
        id=car_id
    )

    Wishlist.objects.get_or_create(
        user=request.user,
        car=car
    )
    
    messages.success(
        request,
        "Car added to wishlist successfully!"
    )

    return redirect(
        'car_detail',
        car_id=car.id
    )
    
@login_required
def my_wishlist(request):

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    )

    return render(
        request,
        'my_wishlist.html',
        {
            'wishlist_items': wishlist_items
        }
    )
    
@login_required
def remove_from_wishlist(request, wishlist_id):

    wishlist_item = Wishlist.objects.get(
        id=wishlist_id,
        user=request.user
    )

    wishlist_item.delete()

    return redirect('my_wishlist')

from .models import Contact

@login_required
def contact_view(request):

    if request.method == "POST":

        name = request.POST["name"]
        email = request.POST["email"]
        message_text = request.POST["message"]

        Contact.objects.create(
            name=name,
            email=email,
            message=message_text
        )

        send_mail(
            subject=f"New Contact Message from {name}",
            message=f"""
Name: {name}

Email: {email}

Message:
{message_text}
""",
            from_email='mohitsharma10618@gmail.com',
            recipient_list=['mohitsharma10618@gmail.com'],
            fail_silently=False,
        )

        messages.success(
            request,
            "Your message has been sent successfully!"
        )

        return redirect('contact')

    return render(
        request,
        'contact.html'
    )
@login_required   
def about_view(request):
    return render(
        request,
        'about.html'
    )
    
@login_required
def edit_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    if booking.booking_status != "Upcoming":
        messages.error(
            request,
            "Only upcoming bookings can be modified."
        )
        return redirect("my_bookings")

    if request.method == "POST":

        start_time = request.POST["start_time"]
        end_time = request.POST["end_time"]

        start = timezone.make_aware(
            datetime.strptime(
                start_time,
                "%Y-%m-%dT%H:%M"
            )
        )

        end = timezone.make_aware(
            datetime.strptime(
                end_time,
                "%Y-%m-%dT%H:%M"
            )
        )

        hours = (end - start).total_seconds() / 3600

        if hours < 1:
            messages.error(
                request,
                "Minimum booking duration is 1 hour."
            )
            return redirect(
                "edit_booking",
                booking.id
            )
            
        conflicting_booking = Booking.objects.filter(
            car=booking.car
        ).exclude(
            id=booking.id
        ).exclude(
            booking_status="Cancelled"
        ).filter(
            start_time__lt=end,
            end_time__gt=start
        ).first()
        
        if start < timezone.now():

            messages.error(
                request,
                "You cannot change a booking to a past date or time."
            )

            return redirect(
                "edit_booking",
                booking_id=booking.id
            )
            
        if end <= start:

            messages.error(
                request,
                "End time must be later than start time."
            )

            return redirect(
                "edit_booking",
                booking_id=booking.id
            )

        if conflicting_booking:

            messages.error(
                request,
                "Selected time slot is already booked."
            )

            return redirect(
                "edit_booking",
                booking.id
                )
        
        
        conflicting_booking = Booking.objects.filter(
            car=booking.car
        ).exclude(
            id=booking.id
        ).exclude(
            booking_status="Cancelled"
        ).filter(
            start_time__lt=end,
            end_time__gt=start
        ).first()

        if conflicting_booking:

            messages.error(
                request,
                "This time slot is already booked."
            )

            return redirect(
                "edit_booking",
                booking_id=booking.id
            )
        booking.start_time = start
        booking.end_time = end
        booking.total_amount = (
            Decimal(str(hours)) * booking.car.rent_per_hour
        )

        booking.save()

        messages.success(
            request,
            "Booking updated successfully."
        )

        return redirect("my_bookings")
    
    return render(
        request,
        "edit_booking.html",
        {
            "booking": booking
        }
    )
    
@login_required
def extend_booking(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    return render(
        request,
        "extend_booking.html",
        {
            "booking": booking
        }
    )
    
@login_required
def booking_detail(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    duration = booking.end_time - booking.start_time
    duration_hours = duration.total_seconds() / 3600

    return render(
        request,
        "booking_detail.html",
        {
            "booking": booking,
            "duration_hours": duration_hours,
        }
    )
    
@login_required
def apply_coupon(request):

    code = request.GET.get("code", "").strip().upper()

    amount = float(request.GET.get("amount", 0))

    try:

        coupon = Coupon.objects.get(
            code=code,
            active=True
        )

    except Coupon.DoesNotExist:

        return JsonResponse({
            "success": False,
            "message": "Invalid coupon."
        })

    now = timezone.now()

    if now < coupon.valid_from or now > coupon.valid_until:

        return JsonResponse({
            "success": False,
            "message": "Coupon has expired."
        })

    if coupon.used_count >= coupon.usage_limit:

        return JsonResponse({
            "success": False,
            "message": "Coupon usage limit reached."
        })

    if amount < float(coupon.minimum_amount):

        return JsonResponse({
            "success": False,
            "message": f"Minimum booking amount is ₹{coupon.minimum_amount}"
        })

    if coupon.discount_type == "Fixed":

        discount = float(coupon.discount_value)

    else:

        discount = amount * float(coupon.discount_value) / 100

    if discount > amount:

        discount = amount

    final_amount = amount - discount

    return JsonResponse({

        "success": True,

        "discount": round(discount, 2),

        "final_amount": round(final_amount, 2),

        "message": "Coupon applied successfully."

    })
    
@login_required
def start_trip(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    if booking.status != "Active":

        messages.error(
            request,
            "Trip can only be started during the active booking period."
        )

        return redirect("my_bookings")

    if booking.pickup_time is None:

        booking.pickup_time = timezone.now()
        booking.save()

        messages.success(
            request,
            "Trip started successfully."
        )

    return redirect("booking_detail", booking_id=booking.id)

@login_required
def end_trip(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    if booking.pickup_time is None:

        messages.error(
            request,
            "Please start the trip first."
        )

        return redirect(
            "booking_detail",
            booking_id=booking.id
        )

    if booking.return_time is None:

        booking.return_time = timezone.now()

        booking.booking_status = "Completed"

        booking.save()

        messages.success(
            request,
            "Trip completed successfully."
        )

    return redirect(
        "booking_detail",
        booking_id=booking.id
    )
    
@login_required
def payment_page(request, booking_id):

    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    amount = int(booking.total_amount * 100)

    payment = client.order.create({

        "amount": amount,

        "currency": "INR",

        "payment_capture": 1

    })

    booking.payment_order_id = payment["id"]

    booking.save()

    return render(
        request,
        "payment.html",
        {
            "booking": booking,
            "payment": payment,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
        }
    )
    
@login_required
def payment_success(request):

    payment_id = request.GET.get("payment_id")
    order_id = request.GET.get("order_id")
    signature = request.GET.get("signature")

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    try:

        client.utility.verify_payment_signature({

            "razorpay_order_id": order_id,

            "razorpay_payment_id": payment_id,

            "razorpay_signature": signature,

        })

    except:

        messages.error(
            request,
            "Payment verification failed."
        )

        return redirect("my_bookings")

    booking = Booking.objects.get(
        payment_order_id=order_id
    )

    booking.payment_id = payment_id

    booking.payment_status = "Paid"

    booking.save()

    messages.success(
        request,
        "Payment successful."
    )

    return redirect(
        "booking_detail",
        booking_id=booking.id
    )




    
