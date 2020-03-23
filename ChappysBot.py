import praw
from urllib.parse import quote_plus
import requests
import time
import config


'''
ChappysBot reads through starcraft reddit and finds phrases that contain the !mmr command.
Creates a comment in reply with the top names sorted by matchmaking.
Similar in function to the !mmr bot on twitch.

Example Phrases:
!mmr Chappy NA 3    -> Returns top 3 results containing the name "Chappy" on the NA server
!mmr Chappy EU      -> Returns top 5 results containing "Chappy" in EU
!mmr Chappy 2       -> Returns top 2 results containing "Chappy"
!mmr Chappy         -> Returns top 5 results containing "Chappy"

eg. !mmr Chappy 8
Displaying top 8 results:
🇺🇸 Chappy: 5525 Z
🇺🇸 Chappy: 5459 Z
🇰🇷 Chappy: 5182 Z
🇺🇸 Chappy: 4865 P
🇺🇸 chappy: 4832 Z
🇺🇸 chappy: 4549 P
🇺🇸 Chappy: 4517 P
🇺🇸 Chappy: 4407 P
'''

SCREDDIT = "starcraft"
ATZ		= "allthingszerg"
#TESTINGGROUNDS = "testingground4bots"
SUBREDDITS = [SCREDDIT, ATZ]	# the subs that I want ot post to.


FLAG_NA = "🇺🇸" #"NA"
FLAG_EU = "🇪🇺" #"EU"
FLAG_KR = "🇰🇷" #"KR"
# FLAG_CN = "CN" #flag -- China cannot be accessed from the blizz api

REGION_DEFAULT = "default"
REGION_NA = "na"
REGION_US = "us"
REGION_AMERICA = "am"
REGION_AMERICAS = [REGION_NA, REGION_US, REGION_AMERICA]   # all americas region
REGION_EU = "eu"
REGION_KR = "kr"
REGIONS = [REGION_DEFAULT, REGION_EU, REGION_KR] + REGION_AMERICAS

RACE_ZERG = "z"
RACE_TERRAN = "t"
RACE_PROTOSS = "p"
RACE_RANDOM = "r"


API_RACE_ZERG = "zerg"
API_RACE_TERRAN = "terran"
API_RACE_PROTOSS = "protoss"
API_RACE_RANDOM = "random"
API_RACES = [API_RACE_ZERG, API_RACE_PROTOSS, API_RACE_TERRAN, API_RACE_RANDOM]

ZERG = [RACE_ZERG, API_RACE_ZERG]
PROTOSS = [RACE_PROTOSS, API_RACE_PROTOSS]
TERRAN = [RACE_TERRAN, API_RACE_TERRAN]
RANDOM = [RACE_RANDOM, API_RACE_RANDOM]

RACES = [RACE_ZERG, RACE_PROTOSS, RACE_TERRAN, RACE_RANDOM] + API_RACES

LIMIT_MAX = 10
REDDIT_NEWLINE = "    \n"   # reddit newlines are retarded. Need 4 spaces first
RACE_DEFAULT = None
LIMIT_DEFAULT = 5   # default number of queries to be called


def main():
    # auth
    reddit = praw.Reddit(
        user_agent=config.USER_AGENT,
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
        username=config.USERNAME,
        password=config.PASSWORD, 
    )

# https://praw.readthedocs.io/en/latest/tutorials/reply_bot.html
    
    #for comment in reddit.multireddit(SUBREDDITS).stream.comments():
    subreddit = reddit.subreddit(SCREDDIT)
    #for comment in subreddit.stream.comments(skip_existing=True):
    #for comment in reddit.multireddit(SCREDDIT, ATZ).stream.comments(skip_existing=True):
    for comment in subreddit.stream.comments():
        print(comment.body)
        print(comment.body.split())

        # don't reply to self
        skip = False
        if comment.author.name == config.USERNAME:
            skip = True

        # don't reply to a comment I've already replied to
        print("########")
        for i in comment.replies:
            print(i.author.name)
    
        for i in comment.replies:
            if i.author.name == MY_ACCOUNT:
                skip = True
                break

        if skip:
            print("skipping comment")
            continue

        # checks for any comments that contain !mmr
        if "!mmr" in comment.body.lower().split():
            process_comment(comment)
       
        # else do nothing

# KEYS for interacting with api
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
    comment_lst = comment.body.lower().split()
        
    query_index = comment_lst.index("!mmr")     # index for where query starts
    query_lst = comment_lst[query_index+2:]     # +2 as we skip the !mmr and name

    in_limit = LIMIT_DEFAULT
    in_region = REGION_DEFAULT
    in_race = RACE_DEFAULT

    # ERROR requests:
    # if !mmr w/ no text following
    # if the name is not made up of only alpha characters
    if (comment_lst[query_index:]) == []:
        comment.reply(format_error_reply(ERROR_NO_INPUT))
        return

    # parse the current name
    in_name = comment_lst[query_index + 1]
    if not in_name.isalpha():
        comment.reply(format_error_reply(ERROR_NON_NUMERICAL))
        return
    
    # parse the text 
    # input of form: !mmr <name> [region, limit, race]
    #       race, region and limit are in no particular order
    # puts curated inputs into in_<type> vars
    for i in query_lst[0:]:
        print(f"i = {i}")
        #  gets numeric input
        if i.isnumeric():
            in_limit = int(i)
            if in_limit > LIMIT_MAX:
                in_limit = LIMIT_MAX

        # check for region
        elif i in REGIONS:
            print(i)
            in_region = i
        
        # checks for race
        elif i in RACES:
            in_race = translateRaceIntoAPIForm(i)

        else: break

    out_lst = process_request(in_name, in_limit, in_region, in_race)
    print(out_lst)

    out = format_reply(out_lst, in_name)
    print("final output:")
    print(out)
    comment.reply(out)
    return

ERROR_NO_INPUT = "no_input"
ERROR_NON_NUMERICAL = "non_num"

# for formatting error replys
def format_error_reply(error_type):
    if error_type == ERROR_NO_INPUT:
        out = f"Error no input!"
        out += REDDIT_NEWLINE
        out = f"Please enter a command in the form !mmr <name> <opt:limit> <opt:region> <opt:>"
        out += REDDIT_NEWLINE
        out += f"eg. !mmr Chappy 3 NA Z"
    elif errror_type == ERROR_NON_NUMERICAL:
        out = f"Error. Blizzard names can't have numbers or non alphabetic characters"
        out += REDDIT_NEWLINE
        out = f"Please enter a command in the form !mmr <name> <opt:limit> <opt:region> <opt:race>"
        out += REDDIT_NEWLINE
        out += f"eg. !mmr Chappy 3 NA Z"

    return out



# Formats the message for reddit comment output
# eg. 
# Displaying top 2 results:
# Chappy: 5500 Z
# Chappy (chris): 5450 Z
# Not here? Check out this link for a complete list.
def format_reply(output_lst, input_name):
    print("Formatted reply!")
    out = ""
    out += f"Displaying top {len(output_lst)} results:" + REDDIT_NEWLINE

    for person in output_lst:
        out += f"{person}" + REDDIT_NEWLINE
    out += REDDIT_NEWLINE + f"Not here? Check out [this link](https://sc2ladder.herokuapp.com/search?query={input_name}) for a complete list."
    return out

STATUS_OK = 200 

# Takes a request, calls the API and returns a formatted list
# Returns a list with a formatted output line per element in the list
#   eg. ['🇺🇸  Lolebiv (danny): 5608 Z', '🇺🇸  ViBE: 5387 Z', '🇺🇸  JPMcD (VIBE): 3357 Z']
# Input eg. process_request("chappy", 5, "NA", "Zerg") 
# Has some diff outputs below
# standard:     <IDFI> Chappy (Chris): 5500 Z NA
# no clan:      ||||| (Chappy): 5500 Z NA
# id and bnet_id same:  Chappy: 5500 Z NA
def process_request(name, limit=LIMIT_DEFAULT, in_region=REGION_DEFAULT, in_race=RACE_DEFAULT):

    response = sc2_ladder_adapter(name)

    out_lst = []

    curr_limit = 0 # the number of outputs so far.

    if response.status_code == STATUS_OK:
        for i in response.json():
            #print(i)
            # stop processing when you see the limit
            if curr_limit == limit:
                print(f"limit={limit} reached")
                break

            # filter out race and region if specified
            race = get_race(i[API_KEY_RACE].lower())
            print(race)
            print(i[API_KEY_RACE])
            if in_race != RACE_DEFAULT and not (check_race_equality(in_race, race)):
                print(f"diffRace in_race={in_race} / {race})")
                continue

            region = i[API_KEY_REGION].lower()
            region_display = get_flag_for_region(region)

            if in_region != REGION_DEFAULT and not (check_region_equality(in_region, region)):
                print(f"diffRegion in_region={in_region} / {region})")
                continue

            region_flag = get_flag_for_region(i[API_KEY_REGION])
            rank = i[API_KEY_RANK]
            mmr = i[API_KEY_MMR]
            clan = i[API_KEY_CLAN]
            username = (i[API_KEY_USERNAME])
            print(i[API_KEY_BNET_ID])
            if i[API_KEY_BNET_ID] is None:
            	username = bnet_id
            else:
            	bnet_id = strip_id(i[API_KEY_BNET_ID])
            
            # output string
            out = f"{region_display.upper()}  "
            if clan is not None:
                f"<{clan}>"
            
            out += f"{username}"
            # if bnet_id and username are the same, only display the username
            if bnet_id != username:
                out += f" ({bnet_id})"

            out += f": {mmr} {race.upper()}"
            out_lst += [out]

            curr_limit += 1
    else:
        print("Could not reach site. No response")

    print(out_lst)
    return out_lst

# Adapter for sc2_ladder
# Returns a response of form request
def sc2_ladder_adapter(query):
    start_time=time.time()
    response = requests.get(f"http://sc2ladder.herokuapp.com/api/player?query={query}")
    print("Time to call and process API--- %s seconds ---" % (time.time() - start_time))
    return response

# Checks if the region for region0 and region1 are equivalent
# Slightly different definition of regions so this is useful
def check_region_equality(region0, region1):
    if (region0 in REGION_AMERICAS) and (region1 in REGION_AMERICAS):
        return True
    if region0 == REGION_EU and region1 == REGION_EU:
        return True
    if region0 == REGION_KR and region1 == REGION_KR:
        return True
    return False

# Checks if the race for race0 and race1 are equivalent
# multiple definitions for each, so this is useful.
def check_race_equality(race0, race1):
    if (race0 in ZERG and race1 in ZERG):
        return True
    if (race0 in PROTOSS and race1 in PROTOSS):
        return True
    if (race0 in TERRAN and race1 in TERRAN):
        return True
    if (race0 in RANDOM and race1 in RANDOM):
        return True
    return False

# Takes the region and returns the flag for the region
# returns the string code for the flag of the given region
# returns None if region is not accepted
def get_flag_for_region(region):
    if region in REGION_AMERICAS:
        return FLAG_NA
    if region == REGION_EU:
        return FLAG_EU
    if region == REGION_KR:
        return FLAG_KR

    return None # should not reach


# helper. Transforms the API output race to the local version
# eg. zerg -> z
def get_race(race):
	if race == API_RACE_ZERG:
		return RACE_ZERG
	if race == API_RACE_PROTOSS:
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
    
if __name__ == "__main__":
    main()
