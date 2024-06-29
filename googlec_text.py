import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import spacy
from dateutil.parser import parse
from datetime import datetime
import pytz

SCOPES = ["https://www.googleapis.com/auth/calendar"]

def extract_datetime(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    
    date = None
    start_time = None
    end_time = None
    
    for ent in doc.ents:
        
        if ent.label_ == "DATE":
            date = ent.text
        elif ent.label_ == "TIME":
            if "to" in ent.text:
                times = ent.text.split("to")
                if len(times) == 2:
                    start_time, end_time = times[0].strip(), times[1].strip()
            else:
                if not start_time:
                    start_time = ent.text
                else:
                    end_time = ent.text
    
    
    if date and start_time and end_time:
        try:
            # Use dateutil to parse date and time
            date_obj = parse(date, fuzzy=True, default=datetime.now())
            start_time_obj = parse(start_time, fuzzy=True)
            end_time_obj = parse(end_time, fuzzy=True)

            # Combine date and time
            start_datetime = datetime.combine(date_obj.date(), start_time_obj.time())
            end_datetime = datetime.combine(date_obj.date(), end_time_obj.time())

            # Make datetime objects timezone-aware
            tz = pytz.timezone("America/Toronto")
            start_datetime = tz.localize(start_datetime)
            end_datetime = tz.localize(end_datetime)

            return start_datetime, end_datetime
        except ValueError as e:
            print(f"Error parsing date or time: {e}")
            return None, None
    else:
        return None, None

def main():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
    
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        ### USER INPUT
        
        user_input = "I would like to book an appointment for July 4rd, 2pm to 3pm."
        
        # Extract date and time from the input text
        start_datetime, end_datetime = extract_datetime(user_input)

        if not start_datetime or not end_datetime:
            print("Could not extract date and time from the input text.")
            return

        # Convert datetime to ISO format
        start_time = start_datetime.isoformat()
        end_time = end_datetime.isoformat()

        # Check if the time is available
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            timeZone="America/Toronto",
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            # Time is available, create the event
            event = {
                "summary": "Appointment for Suruchi",
                "location": "via call",
                "description": "Regarding Heatpump maintenance planning",
                "colorId": 6,
                "start": {
                    "dateTime": start_time,
                    "timeZone": "America/Toronto"
                },
                "end": {
                    "dateTime": end_time,
                    "timeZone": "America/Toronto"
                },
                "attendees": [
                    {"email": "kikasslucifer9@gmail.com"},
                    {"email": "pokhrelsuruchi@gmail.com"}
                ]
            }

            event = service.events().insert(calendarId="primary", body=event, sendUpdates="all").execute()
            print(f"Event created: {event.get('htmlLink')}")
        else:
            print("The selected time slot is not available. Here are the conflicting events:")
            for event in events:
                print(event['summary'], event['start'].get('dateTime'), event['end'].get('dateTime'))

    except HttpError as error:
        print("An error occurred:", error)

if __name__ == "__main__":
    main()
