# frontend/urls.py
from django.urls import path
from frontend.views import front, start_recording, stop_recording, update_status, set_state, get_conversation_state

urlpatterns = [
    path('', front, name='front'),
    path('start_recording/', start_recording, name='start_recording'),
    path('update_status/', update_status, name='update_status'),
    path('stop_recording/', stop_recording, name='stop_recording'),
    path('set_state/', set_state, name='set_state'),
    path('api/conversation-state/', get_conversation_state, name='get_conversation_state'),

]
