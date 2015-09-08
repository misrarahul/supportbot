import httplib2
from apiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials

class Goolander(object):
    def __init__(self, privatekey, account_email, calendarId):

        # Establish resources for credentials

        with open(privatekey, 'rb') as f:
            key = f.read()    

        credentials = SignedJwtAssertionCredentials(
            account_email, 
            key,
            scope=[
                'https://www.googleapis.com/auth/calendar',
                'https://www.googleapis.com/auth/calendar.readonly'
            ])

        http = credentials.authorize(httplib2.Http())

        # Build service from credentials

        self.service = build(serviceName='calendar', version='v3', http=http)

        # Additional Varaibles

        self.calendarId = calendarId

    def createEvent(self, body):
        self.service.events().insert(calendarId=self.calendarId, body=body, sendNotifications=True).execute()

    def getEventsByDate(self, timeMin, timeMax):
        events = []
        page_token = None
        while True:
          page_events = self.service.events().list(calendarId=self.calendarId, timeMin=timeMin, timeMax=timeMax).execute()
          [events.append(event) for event in page_events['items']]
          page_token = page_events.get('nextPageToken')
          if not page_token:
            break
        return events