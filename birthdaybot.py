from __future__ import absolute_import, division, print_function
import os
import time
import re
from slackclient import SlackClient
import numpy as np
import requests
import json


# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# bot's user ID in Slack: value is assigned after the bot starts up
bot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
MENTION_REGEX = "^<@(|[WU].+)>(.*)"


anna_facts = [
    "Anna has genetic immunity to Norovirus",
    "Anna likes Trollhunter",
    "Anna is fluent in English, Russian AND Spanish",
    "Anna's sysadminning skillz are entirely self-taught",
    "Anna has a cat named Samson Shcherbina",
    "Anna knows how to shoot a crossbow",
    "Anna is way cooler than you'll ever know",
]


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            #if it's a DM...
            if (event['channel'][0]=='D'):
                return event["text"], event["channel"]
            #if it's a direct mention of the bot...
            user_id, message = parse_direct_mention(event["text"])
            if user_id == bot_id:
                return message, event["channel"]
    return None, None

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
            reply = c['data']['fixed_height_downsampled_url'] 
    return reply

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    # Default response is help text for the user
    default_response = "Not sure what you mean."

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if ("anna" in command or "Anna" in command):
        response = np.random.choice(anna_facts) 
    else:
        response = make_giphy_request(command)

    # Sends the response back to the channel
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=response or default_response
    )

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        bot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")
