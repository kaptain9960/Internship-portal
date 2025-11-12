from datetime import datetime, timezone

from django.contrib import auth, messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.utils.crypto import get_random_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings

from common.tasks import send_email

from .decorators import redirect_autheticated_user
from .models import PendingUser, Token, TokenType
from .utils import generate_otp
from .forms import ForgotPasswordForm, ResetPasswordForm

# Get custom User model
User = get_user_model()


# Create your views here.
def home(request: HttpRequest):
    return render(request, "home.html")


@redirect_autheticated_user
def user_login(request: HttpRequest):
    if request.method == "POST":
        email: str = request.POST.get("email")
        password: str = request.POST.get("password")

        user = auth.authenticate(request, email=email, password=password)

        if user is not None:
            auth.login(request, user)
            messages.success(request, "You are now logged in")
            return redirect("home")
        else:
            messages.error(request, "Invalid credentials")
            return redirect("login")

    else:
        return render(request, "login.html")


def logout(request: HttpRequest):
    auth.logout(request)
    messages.success(request, "You are now logged out.")
    return redirect("home")


# ============================================
# FORGOT PASSWORD - NEW SYSTEM
# ============================================

def reset_password_via_email(request):
    """Forgot password - request reset link"""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email=email)
            
            # Generate token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Build reset link
            reset_link = request.build_absolute_uri(
                f'/auth/reset-password/{uid}/{token}/'
            )
            
            # FOR DEVELOPMENT: Print to console
            print("\n" + "="*80)
            print("PASSWORD RESET LINK GENERATED")
            print("="*80)
            print(f"User Email: {email}")
            print(f"Reset Link: {reset_link}")
            print("="*80 + "\n")
            
            # Display the link on the page
            return render(request, 'forgot_password.html', {
                'form': form,
                'reset_link': reset_link,
                'email': email
            })
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'forgot_password.html', {'form': form})


def reset_password_confirm(request, uidb64, token):
    """Reset password with token"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = ResetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(
                    request, 
                    'Your password has been reset successfully! You can now login with your new password.'
                )
                return redirect('login')
        else:
            form = ResetPasswordForm(user)
        
        return render(request, 'reset_password.html', {'form': form, 'validlink': True})
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return render(request, 'reset_password.html', {'validlink': False})


# ============================================
# OLD PASSWORD RESET SYSTEM (KEEP IF NEEDED)
# ============================================

def send_password_reset_link(request: HttpRequest):
    """Old system using Token model"""
    if request.method == "POST":
        email: str = request.POST.get("email", "")
        user = User.objects.filter(email=email.lower()).first()

        if user:
            token, _ = Token.objects.update_or_create(
                user=user,
                token_type=TokenType.PASSWORD_RESET,
                defaults={
                    "token": get_random_string(20),
                    "created_at": datetime.now(timezone.utc),
                },
            )

            email_data = {"email": email.lower(), "token": token.token}
            send_email.delay(
                "Your Password Reset Link",
                [email],
                "emails/password_reset_template.html",
                email_data,
            )
            messages.success(request, "Reset link sent to your email")
            return redirect("reset_password_via_email")

        else:
            messages.error(request, "Email not found")
            return redirect("reset_password_via_email")

    else:
        return render(request, "forgot_password.html")


def verify_password_reset_link(request: HttpRequest):
    """Old system verification"""
    email = request.GET.get("email")
    reset_token = request.GET.get("token")

    token: Token = Token.objects.filter(
        user__email=email, token=reset_token, token_type=TokenType.PASSWORD_RESET
    ).first()

    if not token or not token.is_valid():
        messages.error(request, "Invalid or expired reset link.")
        return redirect("reset_password_via_email")

    return render(
        request,
        "set_new_password_using_reset_token.html",
        context={"email": email, "token": reset_token},
    )


def set_new_password_using_reset_link(request: HttpRequest):
    """Old system - Set a new password given the token sent to the user email"""
    if request.method == "POST":
        password1: str = request.POST.get("password1")
        password2: str = request.POST.get("password2")
        email: str = request.POST.get("email")
        reset_token = request.POST.get("token")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return render(
                request,
                "set_new_password_using_reset_token.html",
                {"email": email, "token": reset_token},
            )

        token: Token = Token.objects.filter(
            token=reset_token, token_type=TokenType.PASSWORD_RESET, user__email=email
        ).first()

        if not token or not token.is_valid():
            messages.error(request, "Expired or Invalid reset link")
            return redirect("reset_password_via_email")

        token.reset_user_password(password1)
        token.delete()
        messages.success(request, "Password changed.")
        return redirect("login")


# ============================================
# REGISTRATION SECTION
# ============================================

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST['email']
        mobile_number = request.POST['mobile_number']
        password = request.POST['password']

        if User.objects.filter(mobile_number=mobile_number).exists():
            messages.error(request, "Mobile number already exists.")
            return render(request, 'register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, 'register.html') 

        user = User.objects.create_user(
            username=username, 
            email=email, 
            mobile_number=mobile_number, 
            password=password
        )

        # Generate and save OTPs
        email_otp = generate_otp()
        mobile_otp = generate_otp()
        user.email_otp = email_otp
        user.mobile_otp = mobile_otp
        user.save()

        # Send email OTP
        send_mail(
            'Email Verification OTP',
            f'Your OTP for email verification is: {email_otp}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        print(f"Mobile OTP: {mobile_otp}")

        return redirect('verify_account', user_id=user.id)

    return render(request, 'register.html')


def verify_account(request, user_id):
    """Verify account with OTP"""
    context = {
        'user_id': user_id
    }
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('register')

    if request.method == 'POST':
        entered_code = request.POST.get('code')

        if not entered_code:
            messages.error(request, "Verification code is required.")
            return redirect('verify_account', user_id=user_id)

        if entered_code == user.email_otp or entered_code == user.mobile_otp:
            user.is_email_verified = True
            user.is_mobile_verified = True
            user.email_otp = None
            user.mobile_otp = None
            user.save()
            login(request, user)
            messages.success(request, "Account verified successfully!")
            return redirect('home')
        else:
            messages.error(request, "Invalid verification code.")
            return render(request, 'verify_account.html', context)

    return render(request, 'verify_account.html', context)