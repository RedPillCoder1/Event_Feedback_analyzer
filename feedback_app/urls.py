from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

class CustomLogoutView(LogoutView):
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('events/create/', views.create_event, name='create_event'),
    path('events/<int:event_id>/feedback-form/', views.create_feedback_form, name='create_feedback_form'),
    path('feedback-forms/<int:form_id>/share/', views.share_feedback_form, name='share_feedback_form'),
    path('feedback/<str:unique_link>/', views.submit_feedback, name='submit_feedback'),
    path('events/<int:event_id>/analytics/', views.view_analytics, name='view_analytics'),
]