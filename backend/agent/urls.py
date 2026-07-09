from django.urls import path
from . import views

urlpatterns = [
    path("ask/", views.ask_agent, name="ask-agent"),
    path("info/", views.agent_info, name="agent-info"),
]
