from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from .models import Lead, Appointment, SalesAgent, VoiceCall, VoiceMessage
from .serializers import UserSerializer, LeadSerializer
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from twilio.twiml.voice_response import VoiceResponse, Gather,Hangup
from twilio.rest import Client
from huggingface_hub import InferenceClient
import webbrowser
from urllib.parse import urlencode
from django.utils import timezone
import json
from datetime import timedelta
import datetime

# using Facebook Meta-LLMA large language model for call reply.
model_name = "SuruchiPokhrel/finetuned_llama3.1"
client = InferenceClient(model=model_name, token=settings.HUGGINGFACE_TOKEN)

speaker_timeout = 5
twilio_account_sid = settings.TWILIO_ACCOUNT_SID
twilio_auth_token = settings.TWILIO_AUTH_TOKEN

@method_decorator(csrf_exempt, name='dispatch')
class InboundCalls(View):
    def __init__(self):
        self.welcome_message = "Welcome to Weaver Eco Home, please tell us why you\'re calling?"
        self.fallback_message = "Thank you for Calling Weaver Eco Home. Have a good day and Goodbye!"
        self.closing_message = "Thank you for calling today! Enjoy your rest of the day."
        
    def get(self, request):
        phone_number = request.GET.get('From')
        leads = Lead.objects.filter(phone_number=phone_number)
        return render(request, "admin/aicaller/inbounds.html", {
            "data": request.GET,
            "callId": request.GET.get("CallSid"),
            "twilio_account_sid": twilio_account_sid,
            "twilio_auth_token": twilio_auth_token
        })

    def post(self, request):
        prompt = {
            "role": "system", 
            "content": f"""You are an AI voice call assistant at Weaver Eco Home for the role of
                customer support. Weaver Eco Home is an HVAC company that sells heat pump, 
                air conditioner, and so on. Please access the website for this company hosted at 
                https://www.weaverecohome.ca/ for more information. Please act the way to provide
                customer support asking them about problems. Only reply in two sentences.\n
            """
        }
        CallSid = request.POST.get("CallSid")
        call = VoiceCall.objects.filter(call_id=CallSid).first()
        if not call:
            call = VoiceCall(
                call_id = CallSid,
                ai_caller = "Beaver", 
                start_time = timezone.now(), 
                call_type = "inbound"
            )
            call.save()
            webbrowser.open_new(f"{settings.BASE_URL}/inbounds/?"+ urlencode(request.POST))
        
        response = VoiceResponse()
        if request.POST.get('SpeechResult', ""):
            speech = request.POST['SpeechResult']
            message = VoiceMessage.objects.create(
                voice_chat=call, role="user", content=speech, call_id=CallSid
            )
            messages = VoiceMessage.objects.filter(voice_chat = call)
            all_messages = [{"role": message.role, "content": message.content} for message in messages]
            reply = ''
            for message in client.chat_completion(
                    messages=[prompt, *all_messages, {"role": "user", "content": speech}],
                    max_tokens=120,
                    stream=True,
                ):
                reply += message.choices[0].delta.content + ""
            message = VoiceMessage.objects.create(
                voice_chat=call, role="assistant", content=reply, call_id=CallSid
            )
            gather = Gather(
                input='speech', 
                action=f'{settings.BASE_URL}/inbounds/', 
                timeout=speaker_timeout
            )
            response.append(gather)
            gather.say(reply)
            response.say(self.fallback_message)
            # Check if conversation should end        
            return HttpResponse(str(response), content_type='text/xml')
        
        gather = Gather(
            input='speech', 
            action=f'{settings.BASE_URL}/inbounds/', 
            timeout=speaker_timeout,
        )
        gather.say(self.welcome_message) 
        response.append(gather)
        response.say(self.fallback_message)
        return HttpResponse(str(response), content_type='text/xml')



@method_decorator(csrf_exempt, name='dispatch')
class OutboundsCalls(View):
    def __init__(self):
        self.fallback_message = "Thank you for Calling Weaver Eco Home. Have a good day and Goodbye!"
        self.closing_message = "Thank you for calling today! Enjoy your rest of the day."

        # Fetch the first available sales agent
        agent = SalesAgent.objects.first()

        if agent:
            # Calculate available slots based on the agent's shift times
            shift_start_time = agent.shift_start_time
            shift_end_time = agent.shift_end_time
            
            # Assuming 1-hour appointment slots
            available_slots = []
            slot_time = shift_start_time
            while slot_time < shift_end_time:
                available_slots.append(slot_time.strftime("%H:%M"))
                slot_time = (datetime.datetime.combine(datetime.date.today(), slot_time) + timedelta(hours=1)).time()

            self.available_slots_str = ", ".join(available_slots)
            self.agent_name = "Alexander"
        else:
            self.available_slots_str = "currently no available slots"
            self.agent_name = "no agent available"

    def get(self, request, id=None):
        call_sid = None
        if id is not None:
            lead = Lead.objects.get(pk=id)
            client = Client(twilio_account_sid, twilio_auth_token)
            call = client.calls.create(
                from_=settings.TWILIO_PHONE_NUMBER,
                to=lead.phone_number,
                url=f'{settings.BASE_URL}/outbounds/{id}',
                method="POST",
            )
            call_sid = call.sid
            print(call_sid)
        return render(request, "admin/aicaller/outbounds.html", {
            "lead": lead, 
            "callId": call_sid, 
            "twilio_account_sid": twilio_account_sid, 
            "twilio_auth_token": twilio_auth_token
        })

    #prompt = Please ask about the size of their house, the type of gas they use, and the age of their furnace.
    def post(self, request, id=None):
        lead = Lead.objects.get(pk=id)
        system = {
            "role":"system",
            "content": f""""You're an assistant for Weaver Eco Home, reaching out to {lead.first_name} to see if they're interested in exploring heat pump options. 
            Be upbeat and casual, keep responses to no more than two sentences. Try to book an appointment with them. 
            If the time does not fall within monday to friday 9 am to 6 pm, offer them another time.
                {self.agent_name} will be there. "\n"""
        }
        prompt = {
            "role": "assistant",
            "content": f"""
                Hi! Am I speaking to {lead.first_name}? 
            """
        }
        CallSid = request.POST.get("CallSid")
        call = VoiceCall.objects.filter(call_id=CallSid).first()
        if not call:
            chat = VoiceCall(
                lead = lead,
                call_id=request.POST.get("CallSid"),
                ai_caller="Beaver", 
                start_time=timezone.now(), 
                call_type='outbound'
            )
            chat.save()

        response = VoiceResponse()
        if request.POST.get('SpeechResult', ""):
            speech = request.POST['SpeechResult']
            message = VoiceMessage.objects.create(
                voice_chat=call, role="user", content=speech, call_id=CallSid
            )
            messages = VoiceMessage.objects.filter(voice_chat = call)
            all_messages = [{"role": message.role, "content": message.content} for message in messages]
            reply = ''
            for message in client.chat_completion(
                    messages=[system, prompt, *all_messages, {"role": "user", "content": speech}],
                    max_tokens=150,
                    stream=True,
                ):
                reply += message.choices[0].delta.content + ""
            message = VoiceMessage.objects.create(
                voice_chat=call, role="assistant", content=reply, call_id=CallSid
            )
            # Check if conversation should end after sending the response
            should_hang_up = self.should_end_conversation(reply)
            if should_hang_up:
                response.say(reply)
                response.append(Hangup())
                self.intent_recognition(context= all_messages)
            
            gather = Gather(
                input='speech', 
                action=f'{settings.BASE_URL}/outbounds/{id}', 
                timeout=speaker_timeout
            )
            response.append(gather)
            
            

            gather.say(reply)
            response.say(self.fallback_message)
            return HttpResponse(str(response), content_type='text/xml')
            
        gather = Gather(
            input='speech', 
            action=f'{settings.BASE_URL}/outbounds/{id}', 
            timeout=speaker_timeout
        )
        response.append(gather)
        gather.say(prompt['content'])
        response.say(self.fallback_message)
        return HttpResponse(str(response), content_type='text/xml')

    def intent_recognition(self, context):
        current_date = timezone.now()

        prompt = f"""Review the entire conversation to identify any booking intent. If intent is found, determine the appointment time based on the conversation and the current date ({current_date}).
                 Output only a JSON object with the format:\n\n\"{{\"intent\": \"booking\", \"appointment_time\": \"YYYY-MM-DDTHH:MM:SSZ\"}}\"\n\n Do not explain, do not give any other output.
                 Ensure the `appointment_time` accurately reflects the user's intent and context provided: {context}."""
        
        reply = ''
        for message in client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                stream=True, 
                # The model sends partial responses as they are generated, 
                # rather than waiting to send the entire response at once.
            ):
            reply += message.choices[0].delta.content or ""
        print((reply))

        try:
            result = json.loads(reply)
            intent = result.get("intent")
            appointment_time = result.get("appointment_time")
            
            if intent == "booking" and appointment_time:
                # Create the Appointment if booking intent is found
                call = VoiceCall.objects.filter(call_id=self.request.POST.get("CallSid")).first()
                if call and call.lead:
                    lead = call.lead
                    # Assuming you want to assign the first available agent for simplicity
                    agent = SalesAgent.objects.first()
                    
                    # Convert appointment_time to a timezone-aware datetime
                    appointment_datetime = timezone.make_aware(datetime.datetime.strptime(appointment_time, "%Y-%m-%dT%H:%M:%SZ"))
                    
                    # Save the appointment
                    Appointment.objects.create(
                        lead=lead,
                        agent=agent,
                        appointment_date=appointment_datetime,
                        notes=f"Booked via AI assistant with {self.agent_name}"
                    )
                    
        except json.JSONDecodeError:
        # Handle case where the response isn't valid JSON
            print("Failed to decode JSON from intent recognition response.")

    def should_end_conversation(self, context):
        prompt = f"""Review the entire conversation to determine if the call should be ended. 
                    Consider the context and tone to decide if the conversation has naturally concluded. Make sure that the last message is from the user and that the conversation has fully ended before deciding to hang up.
                    Output format\n\n\"{{\"intent\": \"hang_up\" or \"progress\", \"reason\": \"brief reason here\"}}\"\n\n 
                 Do not explain, do not give any other output.
                 Ensure the `reason` accurately reflects the context provided: {context}."""
    
        reply = ''
        for message in client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                stream=True, 
            ):
            reply += message.choices[0].delta.content or ""
        print(reply)
        if "\"intent\": \"hang_up\"" in reply:
            return True
        else:
            return False
        

