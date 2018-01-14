#!/usr/bin/env python
from __future__ import absolute_import, division, print_function
import os
import sys
import time
import re
from slackclient import SlackClient
import numpy as np
import requests
import json
from collections import defaultdict


# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# bot's user ID in Slack: value is assigned after the bot starts up
bot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+)>(.*)"

#annafacts_file = "annafacts.txt"
#f = open(annafacts_file, 'r')
#anna_facts = [x.strip() for x in f]
#f.close()

#def refresh_annafacts_file():
#    f = open(annafacts_file,'w')
#    f.write("\n".join(anna_facts))
#    f.close()

def parse_bot_commands(slack_events, users):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            if (event['channel'][0]=='D'):
                return event["text"], event["channel"], event['user']
            #if it's a direct mention of the bot...
            user_id, message = parse_direct_mention(event["text"])
            if user_id == bot_id:
                return message, event["channel"], event['user']
    return None, None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def make_giphy_request(tag):
    tag.replace(" ","%20")
    r = requests.get("https://api.giphy.com/v1/gifs/random?"
                     +"key=28ExUIB2LwN8tjGAEXqTOToRlqTpy8G5"
                     +"&rating=g"
                     +"&tag="+tag.replace(" ","%20"))
    if (r.status_code != 200):
        reply = "Oops..got status code "+str(r.status_code)+". Halp." 
    else:
        c = json.loads(r.content)
        if (len(c['data']) == 0):
            reply = "Hmm. Got no Giphy hits with that tag. Try 'cat'"
        else:
            reply = c['data']['fixed_height_downsampled_url'].replace("200_d","200") 
    return reply

def handle_command(command, channel, sender):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean."

    # Finds and executes the given command, filling in response
    #response = None
    # This is where you start to implement more commands!
    #if (command.lower() == "print all annafacts"):
    #    response = "\n".join([str(x[0])+") "+x[1]
    #                          for x in enumerate(anna_facts)])
    #elif (command.lower().startswith("add annafact: ")):
    #    try:
    #        annafact = command[14:]
    #        anna_facts.append(annafact+" (added by "+sender+")") 
    #        refresh_annafacts_file()
    #        response  = "Anna fact '"+annafact+"' added!"
    #    except Exception as e:
    #        response = "Error: "+str(sys.exc_info()[0])
    #elif (command.lower().startswith("remove annafact ")):
    #    try:
    #        idx = int(command[16:])
    #        del anna_facts[idx]
    #        response = "Anna fact "+str(idx)+" removed."
    #        refresh_annafacts_file()
    #    except Exception as e:
    #        response = "Error: "+str(sys.exc_info()[0])
    #else:
    response = make_giphy_request(command)

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

def get_users():
    response = slack_client.api_call("users.list")
    users = dict([(x['id'], x['name']) for x in response['members']])
    return users

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        bot_id = slack_client.api_call("auth.test")["user_id"]
        users = get_users()
        user_counts = defaultdict(lambda: 0)

        while True:
            command, channel, senderid =\
                parse_bot_commands(slack_client.rtm_read(), users)
            if command:
                user_counts[senderid] += 1
                print(users[senderid],"sent",command,"on channel",channel)
                handle_command(command, channel, users[senderid])
                #post to 'log' channel for debugging
                slack_client.api_call(
                    "chat.postMessage",
                    channel="G8SM3BYUV",
                    text=users[senderid]+" sent "+command+" on channel "+channel)

                if (user_counts[senderid]%5 == 0):
                    slack_client.api_call(
                        "chat.postMessage",
                        channel=channel,
                        text=users[senderid]+" you have sent "
                             +str(user_counts[senderid])+" messages to me."
                             +" No judgement.")

            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
