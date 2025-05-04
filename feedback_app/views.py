from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.db.models import Avg, Count
from .models import Event, FeedbackForm, Question, Response, Answer
from .forms import (
    RegistrationForm, 
    EventForm, 
    QuestionForm, 
    FeedbackResponseForm,
    AIFormGenerationForm
)
import random
import nltk

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'registration/login.html')

@login_required
def dashboard(request):
    events = Event.objects.filter(host=request.user)
    return render(request, 'dashboard.html', {'events': events})

@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.host = request.user
            event.save()
            return redirect('create_feedback_form', event_id=event.id)
    else:
        form = EventForm()
    return render(request, 'event_create.html', {'form': form})

@login_required
def create_feedback_form(request, event_id):
    event = get_object_or_404(Event, id=event_id, host=request.user)
    
    if request.method == 'POST':
        if 'ai_generate' in request.POST:
            ai_form = AIFormGenerationForm(request.POST)
            if ai_form.is_valid():
                return ai_generate_questions(request, event, ai_form)
        else:
            question_form = QuestionForm(request.POST)
            if question_form.is_valid():
                question = question_form.save(commit=False)
                question.form = FeedbackForm.objects.get_or_create(event=event)[0]
                question.save()
                return redirect('create_feedback_form', event_id=event.id)
    else:
        ai_form = AIFormGenerationForm()
        question_form = QuestionForm()
    
    feedback_form, created = FeedbackForm.objects.get_or_create(event=event)
    if created:
        feedback_form.unique_link = get_random_string(length=32)
        feedback_form.save()
    
    questions = Question.objects.filter(form=feedback_form)
    
    return render(request, 'form_create.html', {
        'event': event,
        'ai_form': ai_form,
        'question_form': question_form,
        'questions': questions,
        'feedback_form': feedback_form,
    })

def ai_generate_questions(request, event, ai_form):
    event_type = event.event_type
    summary = ai_form.cleaned_data['event_summary']
    num_questions = ai_form.cleaned_data['num_questions']
    
    questions = []
    
    base_questions = [
        "How would you rate the overall event?",
        "What did you like most about the event?",
        "What could be improved for future events?",
    ]
    
    type_questions = {
        'CONF': [
            "How would you rate the keynote speakers?",
            "Were the sessions relevant to your interests?",
            "How was the networking opportunities?"
        ],
        'WORK': [
            "How effective were the hands-on activities?",
            "Was the workshop pace appropriate?",
            "How knowledgeable was the instructor?"
        ],
        'SEM': [
            "How engaging was the presentation?",
            "Did the seminar meet your expectations?",
            "How relevant was the content to your needs?"
        ],
        'TRAIN': [
            "How would you rate the training materials?",
            "Were the learning objectives clear?",
            "How effective was the trainer's delivery?"
        ]
    }
    
    all_questions = base_questions + type_questions.get(event_type, [])
    
    selected_questions = random.sample(all_questions, min(num_questions, len(all_questions)))
    
    feedback_form, created = FeedbackForm.objects.get_or_create(event=event)
    if created:
        feedback_form.unique_link = get_random_string(length=32)
        feedback_form.save()
    
    Question.objects.filter(form=feedback_form).delete()
    
    for i, q_text in enumerate(selected_questions):
        question_type = 'RATING' if 'rate' in q_text.lower() else 'TEXT'
        Question.objects.create(
            form=feedback_form,
            question_text=q_text,
            question_type=question_type,
            required=True,
            order=i+1
        )
    
    return redirect('create_feedback_form', event_id=event.id)

@login_required
def share_feedback_form(request, form_id):
    feedback_form = get_object_or_404(FeedbackForm, id=form_id, event__host=request.user)
    share_url = request.build_absolute_uri(f'/feedback/{feedback_form.unique_link}/')
    return render(request, 'form_share.html', {'feedback_form': feedback_form, 'share_url': share_url})

def submit_feedback(request, unique_link):
    feedback_form = get_object_or_404(FeedbackForm, unique_link=unique_link, is_active=True)
    questions = Question.objects.filter(form=feedback_form).order_by('order')
    
    if request.method == 'POST':
        response_form = FeedbackResponseForm(request.POST)
        if response_form.is_valid():
            response = response_form.save(commit=False)
            response.form = feedback_form
            if response.anonymous:
                response.participant_email = None
            response.save()
            
            for question in questions:
                answer_value = request.POST.get(f'question_{question.id}')
                if answer_value:
                    if question.question_type == 'RATING':
                        Answer.objects.create(
                            response=response,
                            question=question,
                            rating_answer=int(answer_value)
                        )
                    else:
                        Answer.objects.create(
                            response=response,
                            question=question,
                            text_answer=answer_value
                        )
            
            return render(request, 'form_submit.html', {'success': True})
    else:
        response_form = FeedbackResponseForm()
    
    return render(request, 'form_submit.html', {
        'feedback_form': feedback_form,
        'questions': questions,
        'response_form': response_form,
        'success': False
    })

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import defaultdict

@login_required
def view_analytics(request, event_id):
    event = get_object_or_404(Event, id=event_id, host=request.user)
    feedback_form = get_object_or_404(FeedbackForm, event=event)
    questions = Question.objects.filter(form=feedback_form)
    responses = Response.objects.filter(form=feedback_form).count()

    rating_questions = questions.filter(question_type='RATING')
    text_questions = questions.filter(question_type='TEXT')

    rating_data = []
    for question in rating_questions:
        avg_rating = Answer.objects.filter(
            question=question,
            rating_answer__isnull=False
        ).aggregate(Avg('rating_answer'))['rating_answer__avg'] or 0

        rating_counts = Answer.objects.filter(
            question=question,
            rating_answer__isnull=False
        ).values('rating_answer').annotate(count=Count('rating_answer')).order_by('rating_answer')

        rating_data.append({
            'question': question.question_text,
            'avg_rating': round(avg_rating, 1),
            'rating_counts': list(rating_counts),
        })

    sid = SentimentIntensityAnalyzer()
    text_data = []
    for question in text_questions:
        answers = Answer.objects.filter(question=question, text_answer__isnull=False)
        sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
        text_feedback = []

        for ans in answers:
            sentiment = sid.polarity_scores(ans.text_answer)
            compound = sentiment['compound']
            if compound >= 0.05:
                sentiments['positive'] += 1
            elif compound <= -0.05:
                sentiments['negative'] += 1
            else:
                sentiments['neutral'] += 1
            text_feedback.append({'text': ans.text_answer, 'score': compound})

        text_data.append({
            'question': question.question_text,
            'sentiments': sentiments,
            'feedbacks': text_feedback
        })

    return render(request, 'analytics.html', {
        'event': event,
        'feedback_form': feedback_form,
        'responses_count': responses,
        'rating_questions': rating_data,
        'text_questions': text_data,
    })