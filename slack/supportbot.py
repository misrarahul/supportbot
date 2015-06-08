#/usr/bin/env python

import signal
import requests
import json
import re
import random
import sys
from slackclient import SlackClient
from time import sleep

class SupportBot(object):
    def __init__(self, room, token, debug=False):
        self.stopped = False
        self.token = token
        self.slack = SlackClient(token)
        if debug:
            self.at = "" # remove mention from the message
            self.room = 'bot-cantina'
        else:
            self.room = room
            self.at = "@"

    def terminate(self, signum, frame):
        self.stopped = True

    def send_message(self,text):
        self.slack.rtm_send_message(self.room, text)

    def get_userlist(self):
        url = "https://slack.com/api/users.list?token={}".format(self.token)
        data = requests.get(url)
        userlist = json.loads(data.text)['members']
        return userlist

    def choose_member(self):
        try:
            with open('handoff_list.json') as f:
                handoff_list = json.load(f)
        except:
            handoff_list = []

        if not handoff_list:
            handoff_list = [
                'U03QDP6J9', # Alex Bensick
                'U03QUCH68', # Robert Ott
                'U04TJP6TQ', # Marco Junco
                'U03DS1TF1', # Diggory Rycroft
                'U04U808CF', # Jordan Nunez
                'U04U6E9V3', # Karl Moll
                'U0517AJF0', # Cassie Gamm
                'U04TJQBP6', # Maddie Busacca
                'U04URV3TH', # Arthur Cilley
                'U04U6FDR7', # Rahul Misra
                'U04TJNQJ8', # Ryan Seams
                'U04U7TWKB', # Shriya Ravishankar
                'U04U6EQ5F', # Hilary Stone
                'U04TK5XQG', # Christine Kim
                'U04U76VMM', # Marina Milenkovic
            ]   

        picked = random.choice(handoff_list)
        handoff_list.remove(picked)

        with open('handoff_list.json', 'w') as f:
            json.dump(handoff_list, f)
            
        return picked

    def status_check(self, data):
        message = data['text'].lower()
        if message == "support_bot status":
            self.send_message('I am active! :blessed:')

    def handoff_check(self, data):
        message = data['text'].lower()
        if "handoff" in message and re.match(r"[^@]+@[^@]+\.[^@]+", message):
            sender = data.get('user','No One')
            text = '<{at}{0}> Please send an email to support@mixpanel.com with a warm hand off to <{at}{1}>.'.format(sender, self.choose_member(), at=self.at)
            self.send_message(text)

    def review_message(self, data):
        '''
        Organizes all message checks
        '''
        checklist = [
            'status_check',
            'handoff_check'
        ]
        for check in checklist:
            getattr(self, check)(data)

    def run(self):
        signal.signal(signal.SIGTERM, self.terminate)
        signal.signal(signal.SIGINT, self.terminate)

        if self.slack.rtm_connect():
            print "bot activated in {}".format(self.room)
            while not self.stopped:
                for data in self.slack.rtm_read():
                    if all (k in data for k in ('type', 'text')) and data['type'] == 'message' and data['text']:
                        self.review_message(data)
                sleep(5)
        else:
            raise Exception("connection failed")

if __name__ == "__main__":
    try:
        with open('config.json') as config_file:
            config = json.load(config_file)
            token = config['token']
            room = config['room']
            debug = config.get('debug', False)
    except Exception:
        sys.exit('Unable to load config file')

    bot = SupportBot(room, token, debug)
    bot.run()
