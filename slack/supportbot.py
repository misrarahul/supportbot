#/usr/bin/env python

from goolander import Goolander
import json
import random
import re
import requests
from slackclient import SlackClient
import signal
import sys
from time import sleep


try:
    with open('config.json') as config_file:
        config = json.load(config_file)
        token = config['token']
        room = config['room']
        debug = config.get('debug', False)
except Exception:
    sys.exit('Unable to load config file')

new_session = True
slack = SlackClient(token)
service = Goolander('privatekey.pem', account_email, 'mp.se.scheduler@gmail.com')

stopped = False
def terminate(signum, frame):
    global stopped
    stopped = True
signal.signal(signal.SIGTERM, terminate)
signal.signal(signal.SIGINT, terminate)

if debug:
    at = "" # remove mention from the message
    room = 'bot-cantina'
else:
    at = "@"

support_members = [
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
    'U079WJZU1', # Joey Malysz
    'U08H348VB', # Brandon Skerda
    'U086EBLBE', # Will Ginsberg
    'U08HC66KT', # Marissa Kuhrau
]

support_newbies = [
]

support_emea = [
    'U04TK07TN', # Jared McFarland
    'U052AKX8X', # Argenis Ferrer
]

support_uppers = [
    'U03QH6WN0', # Dan Lee
    'U0503HD9H', # Marshall Luis Reaves
    'U04U6L0BH', # Drew Ritter
]

support_org = support_members+support_uppers+support_emea+support_newbies

def terminate(signum, frame):
    stopped = True

def send_message(text):
    slack.rtm_send_message(room, text)

def get_userlist(printout=False):
    url = "https://slack.com/api/users.list?token={}".format(token)
    data = requests.get(url)
    userlist = json.loads(data.text)['members']
    if printout:
        for user in userlist:
            if user['profile']:
                print user['profile'].get('real_name'), user['profile'].get('email'), user['id']
    else:
        return userlist

def choose_member():
    try:
        with open('handoff_list.json') as f:
            handoff_list = json.load(f)
    except:
        handoff_list = []

    if not handoff_list:
        handoff_list = support_members
    picked = random.choice(handoff_list)
    handoff_list.remove(picked)
    with open('handoff_list.json', 'w') as f:
        json.dump(handoff_list, f)

    return picked

def status_check(data):
    message = data['text'].lower()
    if message == "support_bot status":
        send_message('I am active! :blessed:')

def handoff_check(data):
    message = data['text'].lower()
    if "handoff" in message and re.match(r"[^@]+@[^@]+\.[^@]+", message):
        sender = data.get('user','No One')
        text = '<{at}{0}> Please send an email to support@mixpanel.com with a warm hand off to <{at}{1}>.'.format(sender, choose_member(), at=at)
        send_message(text)

def alias_check(data):
    message = data['text'].lower()
    if "@support" in message:
        sender, message = data.get('user', ''), data.get('text').replace('@support ','', 1).encode('ascii', 'ignore')
        teammention = ' '.join(['<{at}{0}>'.format(member, at=at) for member in support_org])
        text = 'from <{at}{0}>: "{message}"\n{teammention}'.format(sender, message=message, teammention=teammention, at=at)
        send_message(text)

def review_message(data):
    status_check(data)
    handoff_check(data)
    alias_check(data)

if __name__ == "__main__":
    if slack.rtm_connect():
        while not stopped:
            if new_session:
                print "bot activated in {}".format(room)
                new_session = False
            for data in slack.rtm_read():
                if all (k in data for k in ('type', 'text', 'user')) and data['type'] == 'message' and data['text'] and data['user'] != 'U055URFUX':
                    review_message(data)
            sleep(5)
    else:
        raise Exception("connection failed")
