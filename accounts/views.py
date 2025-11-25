from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from datetime import datetime, timezone
from common.tasks import send_email
from .models import PendingUser, User
from django.contrib.auth import get_user_model
from .models import Token
from .models import TokenType
from django.contrib import auth, messages




# Create your views here.
def search(request: HttpResponse):
    return render(request, "home.html")




def logout(request: HttpResponse):
    auth.logout(request)
    messages.success(request, "You are now logged out.")
    return redirect("search")


def register(request: HttpResponse):
    if request.method == 'POST':
        email: str = request.POST["email"]
        password: str = request.POST["password"]
        role: str = request.POST.get("role")  # ✅ Get selected role from dropdown
        cleaned_email = email.lower()

        # Check if email already exists
        if User.objects.filter(email=cleaned_email).exists():
            messages.error(request, "Email already exists on the platform")
            return redirect("register")

        else:
            verification_code = get_random_string(10)

            # ✅ Store role in PendingUser
            PendingUser.objects.update_or_create(
                email=cleaned_email,
                defaults={
                    "password": make_password(password),
                    "verification_code": verification_code,
                    "role": role,  # ✅ Save role here
                    "created_at": datetime.now(timezone.utc),
                },
            )

            # Send email verification
            send_email(
                "Verify Your Account",
                [cleaned_email],
                "emails/email_verification_template.html",
                context={"code": verification_code},
            )

            messages.success(request, f"Verification code sent to {cleaned_email}")
            return render(request, "verify_account.html", context={"email": cleaned_email})

    else:
        return render(request, "register.html")


def verify_account(request: HttpResponse):
    if request.method == "POST":
        code: str = request.POST["code"]
        email: str = request.POST["email"]

        pending_user: PendingUser = PendingUser.objects.filter(
            verification_code=code, email=email
        ).first()

        if pending_user and pending_user.is_valid():
            # ✅ Create real user with role included
            user = User.objects.create(
                email=pending_user.email,
                password=pending_user.password,
                role=pending_user.role  # ✅ Apply role here
            )
            pending_user.delete()
            auth.login(request, user)
            messages.success(request, "Account verified. You are logged in")

            # ✅ Redirect based on role
            if user.role == "company":
                return redirect("company_home")
            else:
                return redirect("candidate_home")
        else:
            messages.error(request, "Invalid or expired verification code")
            return render(request, "verify_account.html", {"email": email}, status=400)




def send_password_reset_link(request: HttpResponse):
    if request.method == "POST":
        email: str = request.POST.get("email", "")
        user = get_user_model().objects.filter(email=email.lower()).first()

        if user:
            token, _ = Token.objects.update_or_create(
                user=user,
                token_type=TokenType.PASSWORD_RESET,
                defaults={
                    "token": get_random_string(20),
                    "created_at": datetime.now(timezone.utc)
                }
            )

            email_data = {
                "email": email.lower(),
                "token": token.token
            }
            send_email(
                "Your Password Reset Link",
                [email],
                "emails/password_reset_template.html",
                email_data
            )

            messages.success(request, "Password reset link sent to your email.")
            return redirect("reset_password_via_email")  
        else:
            messages.error(request, "Email not found.")
            return redirect("reset_password_via_email")

    return render(request, "forgot_password.html")


def verify_password_reset_link(request: HttpResponse):
    email = request.GET.get("email")
    reset_token = request.GET.get("token")

    user_model = get_user_model()
    user = user_model.objects.filter(email=email.lower()).first()

    token = Token.objects.filter(
        user=user, token=reset_token, token_type=TokenType.PASSWORD_RESET
    ).first()

    if not token or not token.is_valid():
        messages.error(request, "Invalid or expired reset link.")
        return redirect("reset_password_via_email")

    return render(request, "set_new_password_using_reset_token.html", context={"email": email, "token": reset_token})


def set_new_password_using_reset_link(request: HttpResponse):
    """Set a new password given the token sent to the user email"""

    if request.method == 'POST':
        password1: str = request.POST.get("password1")
        password2: str = request.POST.get("password2")
        email: str = request.POST.get("email")
        reset_token = request.POST.get("token")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return render(
                request,
                "set_new_password_using_reset_token.html",
                context={"email": email, "token": reset_token}
            )

        token: Token = Token.objects.filter(
            token=reset_token,
            token_type=TokenType.PASSWORD_RESET,
            user__email=email
        ).first()

        if not token or not token.is_valid():
            messages.error(request, "Invalid or expired reset link.")
            return redirect("reset_password_via_email")

        # ✅ Reset password
        token.reset_user_password(password1)
        user = token.user  # get the actual user object
        token.delete()

        messages.success(request, "Password changed successfully.")

        # ✅ Redirect based on role
        if getattr(user, "role", None) == "company":
            return redirect("company_login")
        else:
            return redirect("candidate_login")


from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User



from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages

# ---------------- COMPANY LOGIN ----------------
def company_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)
        
        if user is not None and getattr(user, 'role', None) == "company":
            login(request, user)
            messages.success(request, "Logged in successfully as company!")
            return redirect("company_home")
        else:
            messages.error(request, "Invalid credentials or not a company account.")
            return render(request, "company_login.html")
    return render(request, "company_login.html")

# ---------------- CANDIDATE LOGIN ----------------
def candidate_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)
        
        if user is not None and getattr(user, 'role', None) == "candidate":
            login(request, user)
            messages.success(request, "Logged in successfully as candidate!")
            return redirect("candidate_home")
        else:
            messages.error(request, "Invalid credentials or not a candidate account.")
            return render(request, "candidate_login.html")
    return render(request, "candidate_login.html")


from django.contrib.auth.decorators import login_required
from application_tracking.models import JobAdvert


@login_required
def company_home(request):
    job_adverts = JobAdvert.objects.all()  # or filter for company-specific jobs if needed
    return render(request, "home3.html", {"job_adverts": job_adverts})


@login_required
def candidate_home(request):
    job_adverts = JobAdvert.objects.all()  # or filter for company-specific jobs if needed
    return render(request, "home.html", {"job_adverts": job_adverts})


from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    """Decorator to allow only admin users."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not getattr(request.user, "role", None) == "admin":
            messages.error(request, "You are not authorized to access this page.")
            return redirect("search")
        return view_func(request, *args, **kwargs)
    return wrapper


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import User
from application_tracking.models import TestCategory, Question

# Admin Dashboard Home
@login_required
@admin_required
def admin_dashboard(request):
    return render(request, "admin_dashboard.html")

# View all companies
@login_required
@admin_required
def admin_companies(request):
    companies = User.objects.filter(role="company")
    return render(request, "admin_companies.html", {"companies": companies})

from application_tracking.models import UserTestResult

@login_required
@admin_required
def admin_candidates(request):
    # Fetch candidates with their test results in one query
    candidates = User.objects.filter(role="candidate").prefetch_related("usertestresult_set")
    return render(request, "admin_candidates.html", {"candidates": candidates})


# Add questions page
@login_required
@admin_required
def admin_add_question(request):
    categories = TestCategory.objects.all()

    if request.method == "POST":
        category_id = request.POST.get("category")
        question_text = request.POST.get("question_text")
        option1 = request.POST.get("option1")
        option2 = request.POST.get("option2")
        option3 = request.POST.get("option3")
        option4 = request.POST.get("option4")
        correct_option = request.POST.get("correct_option")

        category = TestCategory.objects.get(id=category_id)

        Question.objects.create(
            category=category,
            question_text=question_text,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option
        )

        messages.success(request, "Question added successfully!")
        return redirect("admin_add_question")

    return render(request, "admin_add_question.html", {"categories": categories})

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def admin_login_modal(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None and user.role == "admin":
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid credentials or not admin")
            return redirect('search')  # redirect back to homepage to show modal
    return redirect('search')


# ✅ View all questions (with edit & delete options)
@login_required
@admin_required
def admin_questions(request):
    questions = Question.objects.all().select_related("category")
    return render(request, "admin_questions.html", {"questions": questions})


# ✅ Edit a question
from .forms import QuestionForm  # ✅ import form

@login_required
@admin_required
def edit_question(request, question_id):
    question = Question.objects.get(id=question_id)

    if request.method == "POST":
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, "Question updated successfully!")
            return redirect("admin_questions")
    else:
        form = QuestionForm(instance=question)

    return render(request, "edit_question.html", {"form": form})


# ✅ Delete a question
@login_required
@admin_required
def delete_question(request, question_id):
    question = Question.objects.get(id=question_id)

    if request.method == "POST":
        question.delete()
        messages.success(request, "Question deleted successfully!")
        return redirect("admin_questions")

    # Optional confirmation page
    return render(request, "delete_question.html", {"question": question})





