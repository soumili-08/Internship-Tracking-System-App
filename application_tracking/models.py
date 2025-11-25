from django.db import models
from django.urls import reverse
from common.models import BaseModel
from accounts.models import User
from .enums import EmploymentType, ExperienceLevel, LocationTypeChoice, ApplicationStatus
from django.conf import settings


# Create your models here.  

class JobAdvert(BaseModel):
    title = models.CharField(max_length=150)
    company_name = models.CharField(max_length=150)
    employment_type = models.CharField(max_length=50, choices= EmploymentType)
    experience_level = models.CharField(max_length=150, choices = ExperienceLevel)
    description = models.TextField()
    job_type = models.CharField(max_length=50, choices= LocationTypeChoice)
    location = models.CharField(max_length=255, null=True, blank=True)
    is_published= models.BooleanField(default= True)
    deadline = models.DateField()
    skills = models.CharField(max_length= 255)
    created_by= models.ForeignKey(User, on_delete=models.CASCADE)


    class Meta:
        ordering = ("-created_at",)


    def publish_advert(self) -> None:
        self.is_published =True
        self.save(update_fields=["is_published"])

    def total_application(self):
        return self.applications.count()

    def get_absolute_url(self):
        return reverse("job_advert", kwargs={"advert_id": self.id})


class JobApplication(BaseModel):
    name=models.CharField(max_length= 50)
    email= models.EmailField()
    portfolio_url = models.URLField()
    cv = models.FileField()
    status= models.CharField(max_length= 20, choices=ApplicationStatus.choices,default=ApplicationStatus.APPLIED)
    job_advert= models.ForeignKey(JobAdvert, related_name= "applications", on_delete= models.CASCADE)


from django.db import models
from django.contrib.auth.models import User

class TestCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Question(models.Model):
    category = models.ForeignKey(TestCategory, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    correct_option = models.CharField(max_length=10, choices=[
        ("option1", "Option 1"),
        ("option2", "Option 2"),
        ("option3", "Option 3"),
        ("option4", "Option 4"),
    ])

    def __str__(self):
        return self.question_text[:50]


class UserTestResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(TestCategory, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    date_taken = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.category.name} ({self.score}/{self.total})"



class UserAnswer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=10)
    is_correct = models.BooleanField(default=False)
    test_result = models.ForeignKey(UserTestResult, on_delete=models.CASCADE, related_name="answers")

    def __str__(self):
        return f"{self.user.email} - {self.question.id} ({'Correct' if self.is_correct else 'Wrong'})"
  