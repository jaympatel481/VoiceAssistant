from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import time
import playsound
import speech_recognition as sr
from gtts import gTTS
import pytz
import subprocess

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
DAY_EXTENSIONS = ["st", "nd", "rd", "th"]

def speak(text):
   tts = gTTS(text = text, lang = "en")
   filename = "voice.mp3"
   tts.save(filename)
   playsound.playsound(filename)


def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(audio)
            print(said)
        except Exception as e:
                print("Exception: " + str(e))

    return said.lower()


def authenticate_google():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    return service

def get_events(day,service):    
    # Call the Calendar API
    date = datetime.datetime.combine(day, datetime.datetime.min.time())
    end_date = datetime.datetime.combine(day, datetime.datetime.max.time())
    utc = pytz.UTC
    date = date.astimezone(utc)
    end_date = end_date.astimezone(utc)

    events_result = service.events().list(calendarId='primary', timeMin=date.isoformat(), timeMax = end_date.isoformat(),
                                        singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak('No upcoming events found.')
    else:
        speak(f"You have {len(events)} events on this day.")        
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(start, event['summary'])
            start_time = str(start.split("T")[1].split("-")[0])
            if int(start_time.split(":")[0]) < 12:
                start_time += "am"
            else:
                start_time = str(int(start_time.split(":")[0])-12) + start_time.split(":")[1]
                start_time += "pm"

            speak(events["summary"] + "at" + start_time)    
def get_date(text):
    today = datetime.date.today()

    if text.count("today")>0 :
        return today 
    
    day = -1
    day_of_weak = -1
    month = -1
    year = today.year

    for word in text:
        if word in MONTHS:
            month = MONTHS.index(word) + 1
        elif word in DAYS:
            day_of_week = DAYS.index(word) 
        elif word.isdigit():
            day = int(word)
        else:
            for ext in DAY_EXTENSIONS:
                found = word.find(ext)
                if found > 0:
                    try:
                        day = int(word[:found])
                    except:
                        pass

    if month < today.month and month != -1:
        year += 1
    if day < today.day and day!=-1 and month == -1:
        month += 1
    if month == -1 and day == -1 and day_of_weak != -1:
        current_day_of_week = today.weekday()
        dif = day_of_weak - current_day_of_week

        if dif < 0:
            dif += 7
            if text.count("next") >= 1:
                dif += 7

        return today + datetime.timedelta(dif)
    if month == -1 or day == -1:
        return None

    return datetime.date(month = month, day = day, year = year)


def note(text):
    date = datetime.datetime.now()
    file_name = str(date).replace(":","-") + "-note.txt"
    with open(file_name, "w") as f:
        f.write(text)

    subprocess.Popen(["notepad.exe", file_name])


wake = "hey mark"
service = authenticate_google()

while True:
    print("Listening...")
    text = get_audio()

    if text.count(wake) > 0:
        speak("Go ahead")
        text = get_audio()


        calendar_strs = ["what do i have", "do i have plans", "what is my schedule", "what am i doing", "what events"]
        for phrase in calendar_strs:
            if phrase in text:
                date = get_date(text)
                if date:
                    get_events(date, service)
                else:
                    speak("I don't understand!")
        note_strs = ["write a note", "open notepad and write", "write", "take a note", "note in a file", "open a file and write", "open a file and note"]
        for phrase2 in note_strs:
            if phrase in text:
                speak("what would you like me to write down?")
                note_text = get_audio()
                note(note_text)
                speak("Note written!")