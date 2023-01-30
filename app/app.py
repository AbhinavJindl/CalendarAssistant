from crypt import methods
import json
import os
from enum import Enum
from sre_constants import CH_LOCALE
from time import timezone
from urllib import request
import psycopg2
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
from recurrent.event_parser import RecurringEvent

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
try:
    from db_util import util
except:
    from .db_util import util
import pytz

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('simpleCalendarAssistant.html')

@app.route('/chatCalendarAssistant')
def chatCalendarAssistant():
    return render_template('chatCalendarAssistant.html')


@app.route('/simple_event')
def simpleEvent():
    return render_template('simpleEvent.html')


def get_or_add_user(creds):
    user_info_service = build('oauth2', 'v2', credentials=creds)
    # Call the User Info API
    print('Getting the User Info')
    user_info = user_info_service.userinfo().get().execute()

    user = util.get_user(user_info['id'])

    if user is not None:
        return user

    util.add_user(user_info['id'], user_info['given_name'], user_info['family_name'], user_info['email'])

    user = util.get_user(user_info['id'])

    util.add_chat(user['user_id'], '', 'Welcome! Lets set your first event. What would you like to name it', util.ChatType.EVENT_TIME.value)
    return user


@app.route('/add_event', methods=["POST"])
def add_event():
    user = request.json.get('user')
    token = request.json.get('token')
    event = request.json.get('event')
    creds = Credentials(token.get('access_token'))
    start_time = datetime.fromisoformat(event.get('start_time'))
    end_time = datetime.fromisoformat(event.get('end_time'))
   
    eventDetails = {
        'summary': event.get('event_name'),
        'location': 'USC ISI Lab',
        'description': 'Assistant Calendar Event Set.',
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'America/Los_Angeles',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'America/Los_Angeles',
        },
    }
    event = validate_and_add_event_helper(creds, eventDetails, start_time, end_time)
    if event is None:
        return "Error: Event is either conlficting or timings are incorrect", 400
    return jsonify({"event": event})


@app.route('/chat_history', methods=["POST"])
def chat_history():
    token = request.json.get('token')
    creds = Credentials(token.get('access_token'))
    user = get_or_add_user(creds)
    return json.dumps(util.get_chat_history(user['user_id']))


@app.route('/chat', methods=["POST"])
def chat():
    token = request.json.get('token')
    creds = Credentials(token.get('access_token'))
    user = get_or_add_user(creds)
    query = request.json.get('query')
    chat_history = util.get_chat_history(user['user_id'])
    last_chat = chat_history[-1]
    chat_type = None
    if last_chat['type'] == util.ChatType.EVENT_TIME.value:
        chat_type = util.ChatType.EVENT_NAME.value
    elif last_chat['type'] == util.ChatType.EVENT_NAME.value:
        chat_type = util.ChatType.EVENT_TIME.value
    else:
        chat_type = util.ChatType.EVENT_TIME.value

    if chat_type == util.ChatType.EVENT_NAME.value:
        response = "Got it! When will you like to set it?"
    elif chat_type == util.ChatType.EVENT_TIME.value:
        i = len(chat_history) - 1
        while (chat_history[i]['type'] != util.ChatType.EVENT_NAME.value):
            i -= 1
        event_name = chat_history[i]['query']
        r = RecurringEvent()
        time = r.parse(query)
        if time is None:
            response = 'Sorry! I am unable to understand. Please try again.'
            chat_type = util.ChatType.INVALID.value
        else:
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
                response = 'Event cannot be set due to constraints being broken. Please try to set proper time.'
                chat_type = util.ChatType.INVALID.value
            else:
                response =  'Woohoo! Event Created : <a href={} target="_blank">Link</a>. Lets create more events. What will be the name of the next one?'.format(event.get('htmlLink'))
    util.add_chat(user['user_id'], query, response, chat_type)
    return json.dumps(util.get_chat_history(user['user_id']))


def validate_and_add_event_helper(creds, eventDetails, start_time, end_time):
    if start_time >= end_time or start_time <= datetime.now():
        print ("Event should be in Future and end time after start time")
        return None
    service = build('calendar', 'v3', credentials=creds)
    existing_events = service.events().list(calendarId='primary', timeMax=pytz.timezone('America/Los_Angeles').localize(end_time).isoformat(), timeMin=pytz.timezone('America/Los_Angeles').localize(start_time).isoformat(),
                                            singleEvents=True, orderBy='startTime', timeZone='America/Los_Angeles').execute()

    for event in existing_events['items']:
        event_start_time = datetime.fromisoformat(event['start']['dateTime'].strip('Z')).replace(tzinfo=None)
        event_end_time = datetime.fromisoformat(event['end']['dateTime'].strip('Z')).replace(tzinfo=None)
        if event_start_time < end_time and event_end_time > start_time:
            print ("Event has a conflicting event")
            return None
    event = service.events().insert(calendarId='primary', body=eventDetails).execute()
    return event

    
