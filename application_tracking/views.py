from django.shortcuts import render, redirect, get_object_or_404
from .forms import JobAdvertForm, JobApplicationForm
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from .models import JobAdvert, JobApplication
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count, Q
from common.tasks import send_email
from application_tracking.enums import ApplicationStatus

# ---------------- JOB VIEWS ---------------- #

@login_required
def create_advert(request: HttpRequest):
    form = JobAdvertForm(request.POST or None)

    if form.is_valid():
        instance: JobAdvert = form.save(commit=False)
        instance.created_by = request.user
        instance.save()

        messages.success(request, "Advert created. You can now receive applications.")
        return redirect(instance.get_absolute_url())

    context = {
        "job_advert_form": form,
        "title": "Create a new advert",
        "btn_text": "Create advert"
    }
    return render(request, "create_advert.html", context)


def get_advert(request: HttpRequest, advert_id):
    form = JobApplicationForm()
    job_advert = get_object_or_404(JobAdvert, pk=advert_id)

    context = {
        "job_advert": job_advert,
        "application_form": form
    }
    return render(request, "advert.html", context)


def list_adverts(request: HttpRequest):
    active_jobs = JobAdvert.objects.filter(
        is_published=True, deadline__gte=timezone.now().date()
    )
    paginator = Paginator(active_jobs, 10)
    requested_page = request.GET.get("page")
    paginated_adverts = paginator.get_page(requested_page)

    context = {
        "job_adverts": paginated_adverts
    }
    return render(request, "home.html", context)


def apply(request: HttpRequest, advert_id):
    advert = get_object_or_404(JobAdvert, pk=advert_id)

    if request.method == "POST":
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data["email"]

            # check duplicate application
            if advert.applications.filter(email__iexact=email).exists():
                messages.error(request, "You have already applied for this position")
                return redirect("job_advert", advert_id=advert_id)

            # save the new application
            application: JobApplication = form.save(commit=False)
            application.job_advert = advert
            application.save()

            messages.success(request, "Application submitted successfully.")
            return redirect("job_advert", advert_id=advert_id)
    else:
        form = JobApplicationForm()

    context = {
        "job_advert": advert,
        "application_form": form,
    }
    return render(request, "advert.html", context)


@login_required
def my_applications(request: HttpRequest):
    user = request.user
    applications = JobApplication.objects.filter(email=user.email)
    paginator = Paginator(applications, 10)
    requested_page = request.GET.get("page")
    paginated_applications = paginator.get_page(requested_page)

    context = {
        "my_applications": paginated_applications
    }
    return render(request, "my_applications.html", context)


@login_required
def my_jobs(request: HttpRequest):
    user = request.user
    jobs = JobAdvert.objects.filter(created_by=user).annotate(
        total_applicants=Count("applications")
    )
    paginator = Paginator(jobs, 10)
    requested_page = request.GET.get("page")
    paginated_jobs = paginator.get_page(requested_page)

    context = {
        "my_jobs": paginated_jobs,
        "current_date": timezone.now().date()
    }
    return render(request, "my_jobs.html", context)


@login_required
def update_advert(request: HttpRequest, advert_id):
    advert = get_object_or_404(JobAdvert, pk=advert_id)
    if request.user != advert.created_by:
        return HttpRequestForbidden("You can only update an advert created by you.")

    form = JobAdvertForm(request.POST or None, instance=advert)
    if form.is_valid():
        instance: JobAdvert = form.save(commit=False)
        instance.save()
        messages.success(request, "Advert updated successfully")
        return redirect(instance.get_absolute_url())

    context = {
        "job_advert_form": form,
        "btn_text": "Update advert"
    }
    return render(request, "create_advert.html", context)


@login_required
def delete_advert(request: HttpRequest, advert_id):
    advert = get_object_or_404(JobAdvert, pk=advert_id)
    if request.user != advert.created_by:
        return HttpReponseForbidden("You can only update an advert created by you.")

    advert.delete()
    messages.success(request, "Advert deleted successfully.")
    return redirect("my_jobs")


@login_required
def advert_applications(request: HttpRequest, advert_id):
    advert = get_object_or_404(JobAdvert, pk=advert_id)
    if request.user != advert.created_by:
        return HttpReponseForbidden("You can only see applications for an advert created by you.")

    applications = advert.applications.all()
    paginator = Paginator(applications, 10)
    requested_page = request.GET.get("page")
    paginated_applications = paginator.get_page(requested_page)

    context = {
        "applications": paginated_applications,
        "advert": advert
    }
    return render(request, "advert_applications.html", context)


@login_required
def decide(request: HttpRequest, job_application_id):
    job_application = get_object_or_404(JobApplication, pk=job_application_id)

    if request.user != job_application.job_advert.created_by:
        return HttpResponseForbidden("You can only decide on an advert created by you.")

    if request.method == "POST":
        status = request.POST.get("status")
        job_application.status = status
        job_application.save(update_fields=["status"])
        messages.success(request, f"Application status updated to {status}")

        if status == ApplicationStatus.REJECTED:
            context = {
                "application_name": job_application.name,
                "job_title": job_application.job_advert.title,
                "company_name": job_application.job_advert.company_name,
            }
            send_email(
                f"Application Outcome for {job_application.job_advert.title}",
                [job_application.email],
                "emails/job_application_update.html",
                context
            )

        return redirect("advert_applications", advert_id=job_application.job_advert.id)


def search(request: HttpRequest):
    keyword = request.GET.get('keyword')
    location = request.GET.get('location')

    query = Q()

    if keyword:
        query &= (
            Q(title__icontains=keyword)
            | Q(company_name__icontains=keyword)
            | Q(description__icontains=keyword)
            | Q(skills__icontains=keyword)
        )

    if location:
        query &= Q(location__icontains=location)

    active_jobs = JobAdvert.objects.filter(
        is_published=True, deadline__gte=timezone.now().date()
    )
    result = active_jobs.filter(query)
    paginator = Paginator(result, 10)
    requested_page = request.GET.get("page")
    paginated_adverts = paginator.get_page(requested_page)

    context = {
        "job_adverts": paginated_adverts
    }
    return render(request, "home.html", context)


# ---------------- TEST VIEWS ---------------- #

import random
from django.contrib import messages
from .models import TestCategory, Question, UserTestResult, UserAnswer

@login_required
def test_categories(request):
    categories = TestCategory.objects.all()
    return render(request, "tests/categories.html", {"categories": categories})


@login_required
def take_test(request, category_id):
    category = get_object_or_404(TestCategory, id=category_id)

    # Fetch all questions in this category
    questions_pool = list(category.questions.all())
    num_questions = min(len(questions_pool), 20)
    selected_questions = random.sample(questions_pool, num_questions)

    if request.method == "POST":
        score = 0

        # Create a new UserTestResult for this attempt
        test_result = UserTestResult.objects.create(
            user=request.user,
            category=category,
            score=0,  # update later
            total=num_questions
        )

        # Save each answer safely
        for question in selected_questions:
            user_answer_value = request.POST.get(str(question.id))

            if not user_answer_value:  # skip unanswered
                continue

            is_correct = user_answer_value == question.correct_option
            if is_correct:
                score += 1

            UserAnswer.objects.create(
                user=request.user,
                question=question,
                selected_option=user_answer_value,
                is_correct=is_correct,
                test_result=test_result
            )

        # Update score
        test_result.score = score
        test_result.save()

        messages.success(request, f"Test completed! You scored {score}/{num_questions}.")
        return redirect("test_result", result_id=test_result.id)

    return render(request, "tests/take_test.html", {
        "category": category,
        "questions": selected_questions
    })


@login_required
def test_result(request, result_id):
    result = get_object_or_404(UserTestResult, id=result_id, user=request.user)
    answers = result.answers.all()  # All UserAnswer objects for this attempt

    return render(request, "tests/result.html", {
        "result": result,
        "answers": answers
    })
