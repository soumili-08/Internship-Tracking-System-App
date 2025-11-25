from django import forms
from application_tracking.models import Question, TestCategory

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["category", "question_text", "option1", "option2", "option3", "option4", "correct_option"]

        widgets = {
            "category": forms.Select(attrs={"class": "form-control"}),
            "question_text": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "option1": forms.TextInput(attrs={"class": "form-control"}),
            "option2": forms.TextInput(attrs={"class": "form-control"}),
            "option3": forms.TextInput(attrs={"class": "form-control"}),
            "option4": forms.TextInput(attrs={"class": "form-control"}),
            "correct_option": forms.Select(choices=[("1", "Option 1"), ("2", "Option 2"), ("3", "Option 3"), ("4", "Option 4")],
                                           attrs={"class": "form-control"}),
        }
