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

def get_member_list(member_ids):
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
	    if user_id in member_ids:
	        member_info[user_id] = user
	return member_info

def choose_member(remaining, members, member_ids):
	if not remaining:
		[remaining.append(x) for x in member_ids]
		members = get_member_list(member_ids)
	chosen = random.choice(remaining)
	remaining.remove(chosen)
	return chosen, members


if __name__ == "__main__":
	debug = True 

	try:
		with open('config.json') as config_file:
			config = json.load(config_file)
	except Exception:
		sys.exit('Unable to load config file')

	hipchat = Hipster(config['api_key'])
	bot_name = 'Support Bot'
	last_date = None

	if debug == True:
		room_id = 1447044
	else:
		room_id = config['room_id']

	member_ids = set([
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
	])

	members = {}
	remaining = []
   
	while not stopped:
	    try:
	        messages = hipchat.get_messages(room_id=room_id, date='recent')
	        for message in messages['data']['messages']:
	            if last_date is not None and message['date'] > last_date:
	                message_text = message['message'].lower()
	                if "handoff" in message_text and re.match(r"[^@]+@[^@]+\.[^@]+", message_text):
						chosen, members = choose_member(remaining,members, member_ids)
						text = 'Please hand off to {1} ( @{0} ) '.format(members[chosen]['mention_name'], members[chosen]['name'].split()[0])
						print text
						send_message(text)

	        last_date = message['date']
	    except:
	        if 'messages' in locals():
	            print messages
	        print traceback.format_exc()
	    sleep(20)
