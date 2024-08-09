from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
import json
from .talking import SpeechRecorder

recorder = SpeechRecorder()
conversation_state = 'IDLING'

def front(request, *args, **kwargs):
    context = {
        'debug': settings.DEBUG,
    }
    return render(request, "new.html", context)

def get_conversation_state(request):
    global conversation_state
    return JsonResponse({'state': conversation_state})

def start_recording(request):
    global conversation_state
    recorder.record()
    conversation_state = 'LISTENING'
    return JsonResponse({'status': 'recording started', 'conversationState': conversation_state})

def stop_recording(request):
    global conversation_state
    recorder.update_status('stopped')
    conversation_state = 'STOPPED'
    return JsonResponse({'status': 'recording stopped', 'conversationState': conversation_state})

def set_state(request):
    global conversation_state
    data = json.loads(request.body)
    state = data.get('state')
    if state in ['LISTENING', 'RESPONDING', 'STOPPED', 'IDLING']:
        conversation_state = state
        return JsonResponse({'status': 'state updated', 'conversationState': conversation_state})
    else:
        return JsonResponse({'status': 'invalid state'}, status=400)

def update_status(request):
    global conversation_state
    return JsonResponse({'status': conversation_state})
