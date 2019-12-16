import praw
from urllib.parse import quote_plus
import requests



SCREDDIT = "testingground4bots"

FLAG_NA = "NA" #🇺🇸 
FLAG_EU = "EU" #🇪🇺
FLAG_KR = "KR" #🇰🇷

REGION_DEFAULT = "default"
REGION_NA = "NA"
REGION_US = "US"
REGION_EU = "EU"
REGION_KR = "KR"
REGIONS = [REGION_DEFAULT, REGION_NA, REGION_EU, REGION_KR]

RACE_ZERG = "Z"
RACE_PROTOSS = "P"
RACE_TERRAN = "T"
RACE_RANDOM = "R"

LIMIT_MAX = 10

API_RACE_ZERG = "Zerg"
API_RACE_PROTOSS = "Protoss"
API_RACE_TERRAN = "Terran"
API_RACE_RANDOM = "Random"
API_RACES = [API_RACE_ZERG, API_RACE_PROTOSS, API_RACE_TERRAN, API_RACE_RANDOM]

RACES = [RACE_ZERG, RACE_PROTOSS, RACE_TERRAN, RACE_RANDOM] + API_RACES

REDDIT_NEWLINE = "    \n"

RACE_DEFAULT = None

LIMIT_DEFAULT = 5   # default number of queries to be called

# FLAG_CN = "CN" #flag -- China cannot be accessed from the blizz api

def main():
    # auth
    reddit = praw.Reddit(
        user_agent="chappys_bot (by /u/ImAHappyChappy)",
        client_id="iL01bYVF2-4BjQ",
        client_secret="0zF-orkcPrnwKbxGcOTEkLAn8LM",
        username="ImAHappyChappy",
        password="Melbourne1212",
    )

# https://praw.readthedocs.io/en/latest/tutorials/reply_bot.html
    
    
    subreddit = reddit.subreddit(SCREDDIT)
    #for comment in subreddit.stream.comments(skip_existing=True):
    for comment in subreddit.stream.comments():
        print(comment.body)
        print(comment.body.split())

        #checks for any comments that contain !mmr
        if "!mmr" in comment.body.split():
            process_comment(comment)
       
        # else do nothing

    
    print("DONE")

# API KEYS
API_KEY_RACE = "race"
API_KEY_RANK = "rank"
API_KEY_REGION = "region"
API_KEY_MMR = "mmr"
API_KEY_CLAN = "clan"
API_KEY_USERNAME = "username"
API_KEY_BNET_ID = "bnet_id"


# we found a phrase containing mmr
# now process the comment and see if it's good for use
# Should be of the form !mmr <>
def process_comment(comment):
    comment_lst = comment.body.split()
    
    query_index = comment_lst.index("!mmr")     # index for where query starts
    query_lst = comment_lst[query_index+2:]     # +2 as we skip the !mmr and name

    in_limit = LIMIT_DEFAULT
    in_region = REGION_DEFAULT
    in_race = RACE_DEFAULT


    # TODO if something does not match the required format, give them an error message.

    # parse the current name
    in_name = comment_lst[query_index + 1]
    # parse the text 
    # input of form: !mmr <name> [region, limit, race]
    #       race, region and limit are in no particular order
    # puts curated inputs into in_<type> vars
    for i in query_lst[1:]:
        
        #  gets numeric input
        if i.isnumeric():
            in_limit = int(i)
            if in_limit > LIMIT_MAX:
                in_limit = LIMIT_MAX

        # check for region
        if i in REGIONS:
            print(i)
            in_region = i
        
        # checks for race
        if i in RACES:
            in_race = translateRaceIntoAPIForm(i)

    out_lst = call_api(in_name, in_limit, in_region, in_race)
    print(out_lst)

    out = format_reply(out_lst)
    print("final output:")
    print(out)
    #comment.reply(out)
    return


# formats the reply for the 
def format_reply(output_lst):
    print("Formatted reply!")
    out = ""
    out += f"Displaying top {len(output_lst)} results" + REDDIT_NEWLINE

    for person in output_lst:

        out += f"{person}" + REDDIT_NEWLINE

    return out

STATUS_OK = 200 #todo double check it's not 200

# calls the API
# examples:
# full:     <IDFI> Chappy (Chris): 5500 Z NA
# no clan:  ||||| (Chappy): 5500 Z NA
# id and bnet_id same:  Chappy: 5500 Z NA
def call_api(name, limit=LIMIT_DEFAULT, region=REGION_DEFAULT, race=RACE_DEFAULT):
    response = requests.get(f"http://sc2ladder.herokuapp.com/api/player?query={name}&limit={limit}")
    out_lst = []
    if response.status_code == STATUS_OK:
        for i in response.json():

            race = get_race(i[API_KEY_RACE])
            rank = i[API_KEY_RANK]
            mmr = i[API_KEY_MMR]
            clan = i[API_KEY_CLAN]
            username = strip_id(i[API_KEY_USERNAME])
            bnet_id = strip_id(i[API_KEY_BNET_ID])
            region = get_flag_for_region(i[API_KEY_REGION])

            out = ""
            if clan is not None:
                f"<{clan}>"

            out += f"{username}"

            # if bnet_id and username are the same, only display the username
            if bnet_id != username:
                out += f"({bnet_id})"

            out += f": {mmr} {race} {region}"
            out_lst += [out]

    print(out_lst)
    return out_lst


# Takes the region and returns the flag for the region
def get_flag_for_region(region):
    if region == REGION_US:
        return FLAG_NA
    if region == REGION_EU:
        return FLAG_EU
    if region == REGION_KR:
        return FLAG_KR


# helper. Transforms the API output race to the local version
# eg. Zerg -> Z
def get_race(race):
    if race == API_RACE_ZERG:
        return RACE_ZERG
    if API_RACE_PROTOSS:
        return RACE_PROTOSS
    if API_RACE_TERRAN:
        return RACE_TERRAN
    if API_RACE_RANDOM:
        return RACE_RANDOM
    return # should not reach this


# currently the ids are in the form - danny#1984
# simply removes the hash and numbers after the hash
# note - bnet_ids / player_ids cannot contain #
def strip_id(player_id):
    return player_id[:player_id.index("#")]


# changes the race into the format required for the API to read it
# eg. Z -> Zerg
# will only take input that is in RACES
# returns None if in the wrong format
def translateRaceIntoAPIForm(race):
    if race == RACE_ZERG:
        return API_RACE_ZERG

    if race == RACE_PROTOSS:
        return API_RACE_PROTOSS

    if race == RACE_TERRAN:
        return API_RACE_TERRAN

    if race == RACE_RANDOM:
        return RACE_RANDOM

    if race in API_RACES:
        return race

    return None # should not ever do this
    


"""



def process_submission(submission):
    # Ignore titles with more than 10 words as they probably are not simple
    # questions.
    if len(submission.title.split()) > 10:
        return

    normalized_title = submission.title.lower()
    for question_phrase in QUESTIONS:
        if question_phrase in normalized_title:
            url_title = quote_plus(submission.title)
            reply_text = REPLY_TEMPLATE.format(url_title)
            print("Replying to: {}".format(submission.title))
            submission.reply(reply_text)
            # A reply has been made so do not attempt to match other phrases.
            break
"""

if __name__ == "__main__":
    main()