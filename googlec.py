import os.path
import datetime as dt

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]

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

        start_time = "2024-07-01T16:00:00-04:00"
        end_time = "2024-07-01T17:00:00-04:00"
        time_zone = "America/Toronto"

        # Check if the time is available
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            timeZone=time_zone,
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
                    "timeZone": time_zone
                },
                "end": {
                    "dateTime": end_time,
                    "timeZone": time_zone
                },
                "recurrence": [
                    "RRULE:FREQ=DAILY;COUNT=3"
                ],
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
