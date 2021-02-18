import re
import time
import datetime
import praw

#THIS SCRIPT WILL SEARCH SUBREDDIT_TARGETS BY HOT
#SEARCH FOR WORDS AND COUNT THEM
#THEN SEND A MESSAGE TO USERNAME

#---------------------------------/setup/---------------------------------------
reddit = praw.Reddit(client_id="",
                    client_secret="",
                    user_agent="",
                    username="",
                    password="")

USERNAME = ["UnbanCatgirls", "lucky_124"]           # will send message to these users

MY_SUBREDDIT = ""                                   # will post results with links
                                                    #to this subreddit as a text post
                                                    #leave blank till ready

SUBREDDIT_TARGETS = ["asxbets", "ASX", "ASX_Bets"]

WORDS = ["LKE", "TNT", "PEN", "XST", "ASX", "rocket", "moon", "mooning"]

REGEX_MATCH_STR = "[.| |,|s|?]"                     # Will match " {WORD}"+ any of these(. ,s?)

CASE_SENSITIVE_MATCH = True                         # if this is true it will match
                                                    #words as defined in WORDS
                                                    #if this is false it will match
                                                    #UPPERCASE to UPPERCASE
                                                    #and turn everything else into lowercase
                                                    #including the post and match

POST_TIME_LIMIT = (datetime.datetime.today()
                - datetime.timedelta(days=1))    # will only match post within
                                                    #24 hours of posting
                                                    #can be swapped with these keywords
                                                    #days #seconds
                                                    #microseconds #milliseconds
                                                    #minute #hours
                                                    #weeks

MESSAGE_FORMAT = "KEYWORD : {} / {}\n\n"            # this is the message format with
                                                    #the 1st {} being the word
                                                    #and 2ed {} being Appearences



SUBREDDIT_SEARCH_LIMIT = 100                        # MAX = 100 sorts by hot

APPEARANCE_LIMIT = 5                                # if the word has appeared less then x times
                                                    #it wont be included in the message

MESSAGE_RATE_LIMIT = 2                              # in seconds
                                                    #you may have to send more then 1 message
                                                    #due to reddit message character limit (MAX==10000)
                                                    #the api may limit you due to sending to quick
                                                    #60 * 60 * 24 = 86400 secs == 1 day

TIME_BETWEEN_SCANS = (60*60)*24                     # in seconds
                                                    #time to wait before scaning SUBREDDIT_TARGETS
                                                    #and sending a message to the user

LINKS_IN_MESSAGE = False                            # if true will add a link to where
                                                    #the comment was found
                                                    #WARNING BIG MESSAGES!


#---------------------------------/setup/---------------------------------------


class word_search():
    def __init__(self, inWord):
        self.Appearences = 0
        self.SWord = inWord
        self.AppearenceLocations = []

    def __lt__(self, other):  # less then overload
        return self.Appearences < other.Appearences


def BuildMessage(word_searchArray):
    """
        if LINKS_IN_MESSAGE is True links
        will be included in the message
        RETURNS ARRAY OF STRINGS

    """
    #sort word_searchArray by Appearences
    word_searchArray.sort()

    #setup message to send to user
    MESSAGE = []
    if LINKS_IN_MESSAGE:
        #builds messages with links
        for word in word_searchArray:
            if word.Appearences < APPEARANCE_LIMIT:
                continue
            tmpString = MESSAGE_FORMAT.format(
                word.SWord, word.Appearences)  # title
            MESSAGE.append(tmpString)
            for post in word.AppearenceLocations:
                timeFromUTC = datetime.datetime.utcfromtimestamp(
                    post.created_utc).ctime()           # get time message was made
                tmpPost = post.body.replace("\n", " ")  # format message

                # remove all links in post
                tmpPost = re.sub(r"\[.+\]", "", tmpPost)
                tmpString = "[{}]({})\n\nDate :{} word : {} subreddit : {}\n\n\n\n".format(
                    tmpPost, post.permalink, timeFromUTC, word.SWord, post.subreddit.display_name)  # comments
                MESSAGE.append(tmpString)
    else:  # builds message without links
        for word in word_searchArray:
            if word.Appearences < APPEARANCE_LIMIT:
                continue  # skip anything that did not appear enough
            tmpString = MESSAGE_FORMAT.format(
                word.SWord, word.Appearences)  # "KEYWORD: {} / {}\n\n"
            MESSAGE.append(tmpString)

    #words are sorted by low to high
    #so strings will appeneded in the wrong order
    #so we reverse it here
    MESSAGE.reverse()

    #split messages into blocks to deal with redditAPI TOO_LONG messages(max:10000)
    MSG_BLOCK = []
    CURRENT_LINE = ""
    for msg in MESSAGE:
        if len(CURRENT_LINE) + len(msg) > 10000:  # build messages
            MSG_BLOCK.append(CURRENT_LINE)
            CURRENT_LINE = ""
        CURRENT_LINE += msg+"\n"
        if msg == MESSAGE[len(MESSAGE)-1]:  # append any leftover
            MSG_BLOCK.append(CURRENT_LINE)

    #send all msg blocks
    if len(MSG_BLOCK) > 1:  # reverse the order to see top down list in Inbox
        MSG_BLOCK.reverse()

    return MSG_BLOCK


def PostToSubreddit(word_searchArray):
    """
        Post the results of the word_searchArray
        to subreddit
    """
    #reverse the word search so we get post and comments top down
    word_searchArray.reverse()

    MESSAGE = []

    #builds messages with links
    for word in word_searchArray:
        if word.Appearences < APPEARANCE_LIMIT:
            continue
        tmpString = MESSAGE_FORMAT.format(
            word.SWord, word.Appearences)  # title
        MESSAGE.append(tmpString)
        for post in word.AppearenceLocations:
            timeFromUTC = datetime.datetime.utcfromtimestamp(
                post.created_utc).ctime()           # get time message was made
            tmpPost = post.body.replace("\n", " ")  # format message

            # remove all links in post
            tmpPost = re.sub(r"\[.+\]", "", tmpPost)
            tmpString = "[{}]({})\n\nKEYWORD : {} DATE : {} SUBREDDIT : {}\n\n\n\n".format(
                tmpPost, post.permalink, word.SWord, timeFromUTC, post.subreddit.display_name)  # comments
            MESSAGE.append(tmpString)

    #get the current date for the title of the post
    now = datetime.datetime.now().ctime()

    #split MESSAGE into blocks to deal with redditAPI TOO_LONG post(max:40000)
    MSG_BLOCK = ""
    CURRENT_LINE = ""
    MSG_CUT_OFF = 0
    for msg in MESSAGE:
        MSG_CUT_OFF += 1
        if len(CURRENT_LINE) + len(msg) > 40000:  # build post
            MSG_BLOCK = CURRENT_LINE
            break
        CURRENT_LINE += msg
        if msg == MESSAGE[len(MESSAGE)-1]:  # if the line is less then 40000
            MSG_BLOCK = (CURRENT_LINE)  # then set the block

    #cut off the title and comments we all ready posted
    MESSAGE = MESSAGE[MSG_CUT_OFF:len(MESSAGE)]
    #post the title and get the submission object to post reply to
    LAST_POST = reddit.subreddit(MY_SUBREDDIT).submit(now, MSG_BLOCK)

    #split the message into smaller blocks to reply to post
    MSG_BLOCK = []
    CURRENT_LINE = ""
    for msg in MESSAGE:
        if len(CURRENT_LINE) + len(msg) > 10000:  # build post
            MSG_BLOCK.append(CURRENT_LINE)
            CURRENT_LINE = ""
        CURRENT_LINE += msg
        if msg == MESSAGE[len(MESSAGE)-1]:  # append any leftover
            MSG_BLOCK.append(CURRENT_LINE)

    for block in MSG_BLOCK:
        LAST_POST.reply(block)


def SearchSubredditForKeyWords():
    """ 
        Will search the target subreddits for keywords
        and count how much times it has appeared
        RETURNS ARRAY OF word_search
    """

    #setup helper classes
    word_searchArray = []
    for word in WORDS:
        t = word_search(word)
        word_searchArray.append(t)

    #get all post containing words we would like to track
    for target in SUBREDDIT_TARGETS:  # search target subreddits
        # search target subreddits by hot
        for submission in reddit.subreddit(target).hot(limit=SUBREDDIT_SEARCH_LIMIT):
            for post in submission.comments.list():  # search each comment
                if not hasattr(post, "body"):  # check if comment is real
                    continue
                if post.created_utc < POST_TIME_LIMIT.timestamp():  # if post was not created within
                    continue  # the time limit it will be ignored
                for search in word_searchArray:
                    #check if comment contains any word we are searching
                    #will match " {WORD}(. ,S?)"
                    searchResult = []
                    if CASE_SENSITIVE_MATCH == False:#check if word is all uppercase for stock tickers
                        if search.SWord.isupper():  # case INSENSITIVE match
                            searchResult = re.findall(
                                " "+search.SWord+REGEX_MATCH_STR, post.body)
                        else:  # case INSENSITIVE match
                            searchResult = re.findall(
                                " "+search.SWord.lower()+REGEX_MATCH_STR, post.body.lower())
                    else:  # case SENSITIVE match
                        searchResult = re.findall(
                            " "+search.SWord+REGEX_MATCH_STR, post.body)

                    if len(searchResult) > 0:  # update the word search if match is found
                        search.AppearenceLocations.append(post)
                        search.Appearences += 1
    return word_searchArray


def GetAndSend():
    """
        search all reddit targets
        setup a message and send it to Users
        RETURN word_searchArray
    """
    #get the words/appearences
    word_searchArray = SearchSubredditForKeyWords()
    #build the message with the word_searchArray
    #so we can send it to the user
    MESSAGE = BuildMessage(word_searchArray)
    #send the messages to the user with the title of the message
    #as the current date
    now = datetime.datetime.now().ctime()
    for user in USERNAME:  # send to multiple people
        for i, msg in enumerate(MESSAGE):
            reddit.redditor(user).message(
                "{}: {}/{}".format(now, i+1, len(MESSAGE)), msg)
            # this is needed so you dont spam the api
            time.sleep(MESSAGE_RATE_LIMIT)

    #this will be used if MY_SUBREDDIT is set
    return word_searchArray


while True:
    print("Searching subreddits")
    wordsearchResults = GetAndSend()
    print("Done!")
    if MY_SUBREDDIT != "":
        print("Posting results to subreddit")
        PostToSubreddit(wordsearchResults)

    time.sleep(TIME_BETWEEN_SCANS)
