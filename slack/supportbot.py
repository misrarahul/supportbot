#/usr/bin/env python

from datetime import date
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
        account_email = config['account_email']
except Exception:
    sys.exit('Unable to load config file')

new_session = True
slack = SlackClient(token)

support_room = "C03QFM9BL"
mixpanel_room = "C024QH392"
bot_cantina_room = "C04U9BCCZ"

stopped = False
def terminate(signum, frame):
    global stopped
    stopped = True
signal.signal(signal.SIGTERM, terminate)
signal.signal(signal.SIGINT, terminate)

if debug:
    at = "" # remove mention from the message
    room = 'bot-cantina'
    active_room_id = bot_cantina_room
else:
    at = "@"
    active_room_id = support_room

sf_team_map = {
    'robert@mixpanel.com': 'U03QUCH68', # Robert Ott
    'marco@mixpanel.com': 'U04TJP6TQ', # Marco Junco
    'diggory@mixpanel.com': 'U03DS1TF1', # Diggory Rycroft
    'jordan@mixpanel.com': 'U04U808CF', # Jordan Nunez
    'karl@mixpanel.com': 'U04U6E9V3', # Karl Moll
    'cassie@mixpanel.com': 'U0517AJF0', # Cassie Gamm
    'maddy@mixpanel.com': 'U04TJQBP6', # Maddie Busacca
    'ryan.seams@mixpanel.com': 'U04URV3TH', # Arthur Cilley
    'rahul@mixpanel.com': 'U04U6FDR7', # Rahul Misra
    'arthur@mixpanel.com': 'U04TJNQJ8', # Ryan Seams
    'hilary@mixpanel.com': 'U04U6EQ5F', # Hilary Stone
    'christine.kim@mixpanel.com': 'U04TK5XQG', # Christine Kim
    'marina.milenkovic@mixpanel.com': 'U04U76VMM', # Marina Milenkovic
    'eric.hwang@mixpanel.com': 'U063DLPTL', # Eric Hwang
    'joe.malysz@mixpanel.com': 'U079WJZU1', # Joey Malysz
    'brandon.skerda@mixpanel.com': 'U08H348VB', # Brandon Skerda
    'will.ginsberg@mixpanel.com': 'U086EBLBE', # Will Ginsberg
    'marissa.kuhrau@mixpanel.com': 'U08HC66KT', # Marissa Kuhrau
}
sf_team = sf_team_map.values()

sf_newbies_map = {
}
sf_newbies = sf_newbies_map.values()

emea_map = {
    'jared@mixpanel.com': 'U04TK07TN', # Jared McFarland
    'argenis.ferrer@mixpanel.com': 'U052AKX8X', # Argenis Ferrer
}
emea = emea_map.values()

uppers_map = {
    'daniel@mixpanel.com': 'U03QH6WN0', # Dan Lee
    'marshall@mixpanel.com': 'U0503HD9H', # Marshall Luis Reaves
    'drew@mixpanel.com': 'U04U6L0BH', # Drew Ritter
}
uppers = uppers_map.values()


support_org = sf_team + uppers + emea + sf_newbies

def terminate(signum, frame):
    stopped = True

def send_message(text):
    slack.rtm_send_message(room, text)

def _get_user_email(user, printout=False):
    url = "https://slack.com/api/users.info?token=" % token
    return json.loads(requests.get(url)).get

def _get_userlist(user, printout=False):
    url = "https://slack.com/api/users.list?token=" % token
    data = requests.get(url)
    userlist = json.loads(data.text)['members']
    if printout:
        for user in userlist:
            if user['profile']:
                print user['profile'].get('real_name'), user['profile'].get('email'), user['id']
    else:
        return userlist

def _choose_member():
    try:
        with open('handoff_list.json') as f:
            handoff_list = json.load(f)
    except:
        handoff_list = []

    if not handoff_list:
        handoff_list = sf_team
    picked = random.choice(handoff_list)
    handoff_list.remove(picked)
    while picked in _vacationers():
        if not handoff_list:
            handoff_list = sf_team
        picked = random.choice(handoff_list)
        handoff_list.remove(picked)

    with open('handoff_list.json', 'w') as f:
        json.dump(handoff_list, f)

    return picked

def status_check(data):
    message = data['text'].lower()
    if message == "support_bot status":
        send_message('I am active! :blessed:')

def _vacationers():
    with Goolander('privatekey.pem', account_email, 'mp.se.scheduler@gmail.com') as service:
        today = date.today().isoformat()
        vacation_list = set()
        for event in service.getEventsByDate(today+'T00:00:00-08:00', today+'T23:59:00-08:00'):
            if 'mixpanel' in event['creator']['email']:
                vacation_list.add(sf_team_map.get(event['creator']['email']))
    return list(vacation_list)

def handoff_check(data):
    message = data['text'].lower()
    if "handoff" in message and re.match(r"[^@]+@[^@]+\.[^@]+", message):
        sender = data.get('user','No One')
        text = '<{at}{0}> Please send an email to support@mixpanel.com with a warm hand off to <{at}{1}>.'.format(sender, _choose_member(), at=at)
        send_message(text)

def alias_check(data):
    message = data['text'].lower()
    if "@support" in message:
        sender, message = data.get('user', ''), data.get('text').replace('@support ','', 1).encode('ascii', 'ignore')
        teammention = ' '.join(['<{at}{0}>'.format(member, at=at) for member in support_org])
        text = 'from <{at}{0}>: "{message}"\n{teammention}'.format(sender, message=message, teammention=teammention, at=at)
        send_message(text)

IMPACTFUL_DEPLOY = {'waiting':False}
def deploy_check(data):
    if data.get('username') == 'deploy':
        message = data['attachments']['text']
        if 'sabrina' in message:
            send_message('<!channel>: ' + message.replace(' @sabrina @aliisa @Misha @will', ''))
            IMPACTFUL_DEPLOY['waiting'] = True
        elif ('deploying' in message) and IMPACTFUL_DEPLOY['waiting']:
            send_message(message)
            IMPACTFUL_DEPLOY['waiting'] = False

def review_message(data):
    if data.get('channel') == active_room_id:
        status_check(data)
        handoff_check(data)
        alias_check(data)
    elif data.get('channel') == mixpanel_room:
        deploy_check(data)

if __name__ == "__main__":
    if slack.rtm_connect():
        while not stopped:
            if new_session:
                print "sending responses to {}".format(room)
                new_session = False
            for data in slack.rtm_read():
                if all (k in data for k in ('type', 'text', 'user')) and data['type'] == 'message' and data['text'] and data['user'] != 'U0B6XV760':
                    review_message(data)
            sleep(5)
    else:
        raise Exception("connection failed")
