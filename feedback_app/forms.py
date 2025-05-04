from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Event, Question, FeedbackForm, Response, Answer

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'event_type']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'required', 'order']

class FeedbackResponseForm(forms.ModelForm):
    anonymous = forms.BooleanField(required=False, initial=False)
    participant_email = forms.EmailField(required=False)
    
    class Meta:
        model = Response
        fields = ['anonymous', 'participant_email']

class AIFormGenerationForm(forms.Form):
    event_summary = forms.CharField(widget=forms.Textarea(attrs={'rows': 6}))
    num_questions = forms.IntegerField(min_value=3, max_value=10, initial=5)