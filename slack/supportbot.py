#/usr/bin/env python
import atexit
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

SUPPORT_ROOM = 'C03QFM9BL'
MIXPANEL_ROOM = 'C024QH392'
BOT_CANTINA_ROOM = 'C04U9BCCZ'

BOT_ID = 'U0B6XV760'
BOT_MENTION = '<@' + BOT_ID + '>'

stopped = False

# Store subscribed deploys in memory, updated before closing in terminate
_deploy_file = 'deploy_subscribe.json'
try:
    with open(_deploy_file) as f:
        subsribed_deploys = json.load(f)
except:
    subsribed_deploys = []

def _closing_options():
    with open(_deploy_file, 'w') as f:
        json.dump(subsribed_deploys, f)
    private_message(BOT_OWNERS, 'bot shutdown in %s' % room)
    print '\nbye'

def terminate(signum, frame):
    global stopped
    stopped = True
signal.signal(signal.SIGTERM, terminate)
signal.signal(signal.SIGINT, terminate)

atexit.register(_closing_options)

if debug:
    at = '' # remove mention from the message
    room = 'bot-cantina'
    active_room_id = BOT_CANTINA_ROOM
else:
    at = '@'
    active_room_id = SUPPORT_ROOM

sf_team_map = {
    'robert@mixpanel.com': 'U03QUCH68', # Robert Ott
    'marco@mixpanel.com': 'U04TJP6TQ', # Marco Junco
    'jordan@mixpanel.com': 'U04U808CF', # Jordan Nunez
    'karl@mixpanel.com': 'U04U6E9V3', # Karl Moll
    'cassie@mixpanel.com': 'U0517AJF0', # Cassie Gamm
    'maddy@mixpanel.com': 'U04TJQBP6', # Maddie Busacca
    'ryan.seams@mixpanel.com': 'U04TJNQJ8', # Ryan Seams
    'rahul@mixpanel.com': 'U04U6FDR7', # Rahul Misra
    'arthur@mixpanel.com': 'U04URV3TH', # Arthur Cilley
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
    'pj.ople@mixpanel.com': 'U0BM9ARK7', # PJ Ople
}
uppers = uppers_map.values()

support_org = sf_team + uppers + emea + sf_newbies

BOT_OWNERS = [
    sf_team_map['jordan@mixpanel.com'],
]

def terminate(signum, frame):
    stopped = True

def send_message(text):
    slack.rtm_send_message(room, text)

def private_message(users, text):
    if isinstance(users, list):
        for user in users:
            slack.api_call(
                'chat.postMessage',
                channel=user,
                text=text,
                username='support bot'
            )

def _get_user_email(user, printout=False):
    url = 'https://slack.com/api/users.info?token=%s' % token
    return json.loads(requests.get(url)).get

def _get_userlist(printout=False):
    url = 'https://slack.com/api/users.list?token=%s' % token
    data = requests.get(url)
    userlist = json.loads(data.text)['members']
    if printout:
        for user in userlist:
            if user['profile']:
                print user['profile'].get('real_name'), user['profile'].get('email'), user['id']
    else:
        return userlist

def _vacationers():
    with Goolander('privatekey.pem', account_email, 'mp.se.scheduler@gmail.com') as service:
        today = date.today().isoformat()
        vacation_list = set()
        for event in service.getEventsByDate(today+'T00:00:00-08:00', today+'T23:59:00-08:00'):
            if 'mixpanel' in event['creator']['email']:
                vacation_list.add(sf_team_map.get(event['creator']['email']))
    return list(vacation_list)

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

def _sanitize_text(text):
    return text.replace(u'\u201c', '"').lower()

def _sanitize_link(link):
    return link.replace('<', '').replace('>', '')

def status_check(data):
    message = data['text']
    if BOT_MENTION in message and 'status' in _sanitize_text(message):
        send_message('I am active! :blessed:')

def handoff_check(data):
    message = _sanitize_text(data['text'])
    if 'handoff' in message and re.match(r'[^@]+@[^@]+\.[^@]+', message):
        sender = data.get('user','No One')
        text = '<{at}{0}> Please send an email to support@mixpanel.com with a warm hand off to <{at}{1}>.'.format(sender, _choose_member(), at=at)
        send_message(text)

def alias_check(data):
    message = _sanitize_text(data['text'])
    if '@support' in message:
        sender, message = data.get('user', ''), data.get('text').replace('@support ','', 1).encode('ascii', 'ignore')
        teammention = ' '.join(['<{at}{0}>'.format(member, at=at) for member in support_org])
        send_message('<%(at)s%(sender)s>: "%(message)s"\n%(teammention)s' % {'at': at, 'sender': sender, 'message': message, 'teammention': teammention})

def deploy_subscribe(data):
    message = _sanitize_text(data['text'])
    if all (k in message for k in (BOT_MENTION.lower(), 'deploy subscribe')):
        if 'list' in message:
            out = ''
            for i, item in enumerate(subsribed_deploys):
                out += '%d: %s \n' % (i+1, item)
            if not out:
                send_message('No subscriptions currently exist')
            else:
                send_message(out)
        elif 'add' in message:
            subsribed_deploys.extend(re.findall('"([^"]*)"', message))
            send_message('deploy subscription added')
        elif 'remove' in message:
            try:
                del subsribed_deploys[int(message.split('remove')[-1])-1]
                send_message('deploy subscription removed')
            except:
                send_message('invalid input')

IMPACTFUL_DEPLOY = {'waiting': False}
def deploy_check(data):
    if data.get('username') == 'deploy':
        message = data['attachments'][0].get('text')
        if any (k in message for k in subsribed_deploys) and not IMPACTFUL_DEPLOY['waiting']:
            send_message('<!channel>: ' + _sanitize_link(message))
            IMPACTFUL_DEPLOY['waiting'] = True
        elif ('deploy' in message) and IMPACTFUL_DEPLOY['waiting']:
            send_message(_sanitize_link(message))
            IMPACTFUL_DEPLOY['waiting'] = False

def review_message(data):
    if data.get('channel') == active_room_id:
        status_check(data)
        handoff_check(data)
        alias_check(data)
        deploy_subscribe(data)
    elif data.get('channel') == MIXPANEL_ROOM:
        deploy_check(data)

if __name__ == '__main__':
    if slack.rtm_connect():
        while not stopped:
            slack.server.ping()
            if new_session:
                print 'sending responses to {}'.format(room)
                new_session = False
            for data in slack.rtm_read():
                if all (k in data for k in ('type', 'text')) and data['type'] == 'message':
                    try:
                        review_message(data)
                    except Exception as e:
                        temp_message = '\nfailed message:\n' + json.dumps(data) + '\n' + str(type(e)) + ': ' + str(e)
                        print temp_message
                        private_message(BOT_OWNERS, temp_message)
            sleep(5)
    else:
        raise Exception('connection failed')
