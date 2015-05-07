#/usr/bin/env python

from hipster import Hipster
from time import sleep
import random
import sys
import json
import signal
import traceback
import re

stopped = False
def terminate(signum, frame):
    global stopped
    stopped = True
signal.signal(signal.SIGTERM, terminate)
signal.signal(signal.SIGINT, terminate)

def send_message(text):
    hipchat.send_messages(room_id=room_id, message=text, message_format='text', sender=bot_name)

def get_member_list():
    '''
    Returns complete hipchat user list from a file. grabs fresh data once a day
    '''

    try:
        with open('member_info.json') as f:
            member_info = json.load(f)
    except:
        member_info = None
    # Get new userlist if one does not exist or if it is the first of the month
    if not member_info: # or datetime.date.today().day == 1: # UNDO WHEN DONE
        loaded_users = False
        while not loaded_users:
            response = hipchat.get_users_list()
            if response['status'] != 200:
                sleep(15)
                continue
            loaded_users = True
            users = response['data']['users']
        member_info = {}
        for user in users:
            user_id = user['user_id']
            member_info[user_id] = user
        return member_info

    with open('member_info.json', 'w') as f:
        json.dump(member_info, f)
    
    return member_info

def choose_member():
    '''
    Returns a member for the next handoff
    '''

    try:
        with open('handoff_list.json') as f:
            handoff_list = json.load(f)
    except:
        handoff_list = []

    if not handoff_list:
        handoff_list = [
            702888, # Alex Bensick
            940530, # Robert Ott
            999750, # Marco Junco
            1022218, # Diggory Rycroft
            1042299, # Jordan Nunez
            1082775, # Karl Moll
            1188518, # Cassie Gamm
            1261979, # Maddie Busacca
            1261981, # Arthur Cilley
            1306972, # Rahul Misra
            1306974, # Ryan Seams
            1355588, # Shriya Ravishankar
            1382051, # Hilary Stone
            1796575, # Christine Kim
            1861842, # Marina Milenkovic
        ]   

    picked = random.choice(handoff_list)
    handoff_list.remove(picked)

    with open('handoff_list.json', 'w') as f:
        json.dump(handoff_list, f)

    return picked


if __name__ == "__main__":

    debug = True 

    try:
        with open('config.json') as config_file:
            config = json.load(config_file)
            api_key = config['api_key']
            room_id = config['room_id']
    except Exception:
        sys.exit('Unable to load config file')

    hipchat = Hipster(api_key)
    bot_name = 'Support Bot'
    last_date = None

    if debug == True:
        room_id = 1447044 # send to the BotTest room
        at = "" # remove mention from the message
    else:
        at = "@"

    first_time = True
   
    while not stopped:
        try:
            messages = hipchat.get_messages(room_id=room_id, date='recent')
            for message in messages['data']['messages']:
                if last_date is not None and message['date'] > last_date:
                    message_text = message['message'].lower()
                    if "handoff" in message_text and re.match(r"[^@]+@[^@]+\.[^@]+", message_text):
                        chosen, members = choose_member(), get_member_list()
                        sender_name = json.dumps(message['from']['name'])
                        sender_mention_name = members[message['from']['user_id']]['mention_name']
                        text = '{at}{0} Please hand off to {1} ( {at}{2} ) '.format(sender_mention_name , members[chosen]['name'].split()[0], members[chosen]['mention_name'], at=at)
                        print "{0}: {1}".format(sender_name, message_text)
                        print text
                        send_message(text)

            last_date = message['date']
        except:
            if 'messages' in locals():
                print messages
            print traceback.format_exc()

        if first_time == True:
            send_message('My hand off funcionality is activate!')
            first_time = False

        sleep(10)
