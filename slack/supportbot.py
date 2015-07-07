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
        self.new_session = True
        self.token = token
        self.slack = SlackClient(token)
        self.connected = self.slack.rtm_connect()
        if debug:
            self.at = "" # remove mention from the message
            self.room = 'bot-cantina'
        else:
            self.room = room
            self.at = "@"
        self.support_members = [
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
            'U04U6EQ5F', # Hilary Stone
            'U04TK5XQG', # Christine Kim
            'U04U76VMM', # Marina Milenkovic
            'U063DLPTL', # Eric Hwang
        ]

        self.support_emea = [
            'U04TK07TN', # Jared McFarland
            'U052AKX8X', # Argenis Ferrer
        ]

        self.support_uppers = [
            'U03QH6WN0', # Dan Lee
            'U0503HD9H', # Marshall Luis Reaves
            'U04U6L0BH', # Drew Ritter
        ]

        self.support_org = self.support_members+self.support_uppers+self.support_emea

    def terminate(self, signum, frame):
        self.stopped = True

    def send_message(self,text):
        self.slack.rtm_send_message(self.room, text)

    def get_userlist(self, printout=False):
        url = "https://slack.com/api/users.list?token={}".format(self.token)
        data = requests.get(url)
        userlist = json.loads(data.text)['members']
        if printout:
            for user in userlist:
                if user['profile']:
                    print user['profile'].get('real_name'), user['profile'].get('email'), user['id']
        else:
            return userlist

    def choose_member(self):
        try:
            with open('handoff_list.json') as f:
                handoff_list = json.load(f)
        except:
            handoff_list = []

        if not handoff_list:
            handoff_list = self.support_members

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

    def alias_check(self, data):
        message = data['text'].lower()
        if "@support" in message:
            sender, message = data.get('user', ''), data.get('text').replace('@support ','', 1).encode('ascii', 'ignore')
            teammention = ' '.join(['<{at}{0}>'.format(member, at=self.at) for member in self.support_org])
            text = 'from <{at}{0}>: "{message}"\n{teammention}'.format(sender, message=message, teammention=teammention, at=self.at)
            self.send_message(text)

    def review_message(self, data):
        '''
        Organizes all message checks
        '''
        checklist = [
            'status_check',
            'handoff_check',
            'alias_check'
        ]
        for check in checklist:
            getattr(self, check)(data)

    def run(self):
        signal.signal(signal.SIGTERM, self.terminate)
        signal.signal(signal.SIGINT, self.terminate)
        if self.new_session:
            print "bot activated in {}".format(self.room)
            self.new_session = False
        if not self.stopped:
            for data in self.slack.rtm_read():
                if all (k in data for k in ('type', 'text')) and data['type'] == 'message' and data['text'] and data['user'] != 'U055URFUX':
                    self.review_message(data)
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
    while not bot.stopped:
        bot.run()
        sleep(5)
