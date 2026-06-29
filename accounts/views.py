from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rentals.models import Profile, Booking, Wishlist, Review
from django.core.mail import send_mail
from django.conf import settings

def signup_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        return redirect('/accounts/login/')

    return render(request, 'signup.html')


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:
            login(request, user)
            return redirect('/')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('/')

@login_required
def profile_view(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    bookings_count = Booking.objects.filter(
        user=request.user
    ).count()

    wishlist_count = Wishlist.objects.filter(
        user=request.user
    ).count()

    review_count = Review.objects.filter(
        user=request.user
    ).count()

    context = {
        'profile': profile,
        'bookings_count': bookings_count,
        'wishlist_count': wishlist_count,
        'review_count': review_count
    }

    return render(
        request,
        'profile.html',
        context
    )
    
@login_required
def update_profile(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        profile.phone = request.POST.get(
            'phone'
        )

        profile.city = request.POST.get(
            'city'
        )

        profile.driving_license_number = request.POST.get(
            'driving_license_number'
        )

        profile.date_of_birth = request.POST.get(
            'date_of_birth'
        )

        if 'profile_image' in request.FILES:
            profile.profile_image = request.FILES[
                'profile_image'
            ]

        if 'license_image' in request.FILES:
            profile.license_image = request.FILES[
                'license_image'
            ]
            
        license_uploaded = False

        if 'license_image' in request.FILES:

            profile.license_image = request.FILES[
                'license_image'
            ]

            license_uploaded = True

        profile.save()
        
        if license_uploaded:

            send_mail(
                subject='New License Verification Request',

                message=f'''
        User: {request.user.username}
        Email: {request.user.email}

        has uploaded a driving license.

        Please review and verify the license.
        ''',

                from_email=settings.EMAIL_HOST_USER,

                recipient_list=[
                    settings.EMAIL_HOST_USER
                ],

                fail_silently=False
            )

        return redirect('profile')

    return render(
        request,
        'update_profile.html',
        {'profile': profile}
    )