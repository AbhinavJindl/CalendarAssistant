from __future__ import print_function

from datetime import datetime, timedelta
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from recurrent.event_parser import RecurringEvent
from app import validate_and_add_event_helper


# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid',
]

TOKENS_FILE = 'token.json'


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKENS_FILE):
        creds = Credentials.from_authorized_user_file(TOKENS_FILE, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(host='127.0.0.1', port=5000)
    try:
        # Save the credentials for the next run
        with open(TOKENS_FILE, 'w') as token:
            token.write(creds.to_json())
        event_name = input('Enter Event Name: ')
        time_query = input('When do you want to set it? ')
        service = build('calendar', 'v3', credentials=creds)
        r = RecurringEvent()
        time = r.parse(time_query)
        while time is None:
            time_query = input('Sorry! I am unable to understand. Please try inputing the start time again. ')
            time = r.parse(time_query)
        eventDetails = {
            'summary': event_name,
            'location': 'USC ISI Lab',
            'description': 'Assistant Calendar Event Set.'
        }
        if not r.is_recurring:
            delta = timedelta(hours=1)
            start_time = time
            end_time = start_time + delta
            eventDetails['start'] = {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            }
            eventDetails['end'] = {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            }
            event = validate_and_add_event_helper(creds, eventDetails, start_time, end_time)
        else:
            delta = timedelta(hours=1)
            start_time = datetime.now()
            end_time = start_time + delta
            eventDetails['start'] = {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            }
            eventDetails['end'] = {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/Los_Angeles',
            }
            eventDetails['recurrence'] = [
                r.get_RFC_rrule()
            ]
            service = build('calendar', 'v3', credentials=creds)
            event = service.events().insert(calendarId='primary', body=eventDetails).execute()
        if event is None:
            print ("Couldn't set the event")
        else:
            print ('Event created: %s' % (event.get('htmlLink')))
            print ('All the details: {}'.format(event))
    except Exception as error:
        print('An error occurred: %s' % error)


if __name__ == '__main__':
    main()