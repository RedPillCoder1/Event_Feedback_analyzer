from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Event(models.Model):
    EVENT_TYPES = [
        ('CONF', 'Conference'),
        ('WORK', 'Workshop'),
        ('SEM', 'Seminar'),
        ('TRAIN', 'Training'),
    ]
    
    host = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=5, choices=EVENT_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class FeedbackForm(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    unique_link = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return f"Feedback for {self.event.title}"

class Question(models.Model):
    QUESTION_TYPES = [
        ('TEXT', 'Text Response'),
        ('RATING', 'Rating (1-5)'),
        ('MC', 'Multiple Choice'),
    ]
    
    form = models.ForeignKey(FeedbackForm, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=6, choices=QUESTION_TYPES)
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.question_text

class Response(models.Model):
    form = models.ForeignKey(FeedbackForm, on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    participant_email = models.EmailField(blank=True, null=True)
    anonymous = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Response to {self.form} at {self.submitted_at}"

class Answer(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text_answer = models.TextField(blank=True, null=True)
    rating_answer = models.IntegerField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    def __str__(self):
        return f"Answer to {self.question}"