"""
@author Benjamin Pasternak
"""
import discord
import spacy
import re
import emoji
from spacytextblob.spacytextblob import SpacyTextBlob
import pymongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import hashlib
import urllib
from datetime import datetime

load_dotenv()  # loading the .env file which contains the public key and permissions int

nlp = spacy.load('en_core_web_lg')  # importing small model
nlp.add_pipe('spacytextblob')


# nlp.add_pipe('spacytextblob')

class MyClient(discord.Client):
    def assemble_URI(self):
        return f'mongodb+srv://{urllib.parse.quote_plus(os.getenv("USER_NAME"))}:{urllib.parse.quote_plus(os.getenv("PASS"))}{os.getenv("LATTER_URI")}'
    def __init__(self):
        self.con = MongoClient(self.assemble_URI())
        self.db = self.con["discord_test"]
        self.messages_collection = self.db["message_collection"]
        self.user_collection = self.db["user_collection"]
        self.secure_messages_collection = self.db["secure_messages_collection"]
        super().__init__()  # init is inherited from discord.Client, so you need to make sure that
        # you are not overwriting this inherited constructor by calling super. oop for ya ...

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print(self.con['test_server'])
        print(self.messages_collection)
        print('------')

    async def message_clean(self, text: str) -> str:
        """
        This function is for cleaning the text strings input for processing by sentiment analysis
        found https://stackoverflow.com/questions/33404752/removing-emojis-from-a-string-in-python helpful
        @param text: the text portion of message object
        @return: clean_text: processed cleaned text
        """
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'<:\w*:\d*>', '', text)  # custom emoji remover
        text = re.sub(emoji.get_emoji_regexp(), r"", text)  # global emoji remover
        text = re.sub(r'@[^\s]+', '', text)  # removing @someone in @ messages
        text = re.sub(r'\s\s+', ' ', text)
        text = re.sub(r'\n', '', text)
        return text

    async def user_update(self, author, message):
        pass

    async def on_message(self, message):
        """
        This function controls the user interface, user tracking logic and message logging.
        @param message: the message most recently entered
        @return: void
        """
        # message from bot don't respond else infinite loop
        if message.author.id == self.user.id:
            return

        user_hash = hashlib.sha1(str(message.author).encode()).hexdigest()
        clean_message_content = await self.message_clean(message.content)
        doc = nlp(clean_message_content)

        print(f'got a message from {message.author}')  # hash it
        print(f'message body: {message.content}')  # mesure it
        # special messages
        if message.content[:6] == '~~help':
            await message.channel.send("```md\n# Instructions:\n1. ~~help :command is used to summon this instruction "
                                       "manual\n2. ~~user <username#0001> :command is used to get user stats\n3. "
                                       "~~sentiment <message> :classify how message\n4. ~~intent <message> :classify "
                                       "the message intent```")
            return
        elif message.content[:6] == '~~user':
            if message.content[6] != ' ':
                await message.channel.send("Malformed query: try adding a space after ~~user")
            else:
                user_data = self.user_collection.find_one({"user_hash": hashlib.sha1(str(message.content[7:].strip()).encode()).hexdigest()})
                print(message.content[7:].strip())
                await message.channel.send(f'{message.content[7:].strip()} has Average polarity: {user_data["user_polarity_avg"]} and average subjectivity: {user_data["user_subjectivity_avg"]}')

            # check for @ mentions in the message instead of names and stuff
            return
        elif message.content[:11] == '~~sentiment':
            await message.channel.send("Under development")
            return
        elif message.content[:8] == '~~intent':
            await message.channel.send("Under development")
            return
        # user tracking logic
        if len(clean_message_content) == 0:
            return
        # print(doc._.polarity)
        # print(doc._.subjectivity)
        # await message.channel.send(
        #     f"this message's polarity = {doc._.polarity}, the subjectivity = {doc._.subjectivity}")

        #  if user not in database create entry
        # user_hash = hashlib.sha1(str(message.author).encode()).hexdigest()
        user_data = self.user_collection.find_one({"user_hash": user_hash})
        if user_data is None:  # create new user entry
            # info on cumulative averages https://math.stackexchange.com/questions/106700/incremental-averageing pls
            # note that ints in python are 32bit and therefore will roll over at 2^31 - 1 messages... likely not an
            # issue but perhaps it needs attention when if it causes bot to crash...
            new_user = {
                "user_hash": user_hash,
                "message_count": 1,
                "user_polarity_avg": doc._.polarity,
                "user_subjectivity_avg": doc._.subjectivity
            }
            self.user_collection.update_one({"user_hash": new_user["user_hash"]}, {"$set": new_user}, upsert=True)
        elif user_data is not None:
            user_update = {
                "user_hash": user_hash,
                "message_count": (user_data["message_count"]+1),
                "user_polarity_avg": (user_data["user_polarity_avg"]+(doc._.polarity-user_data["user_polarity_avg"])/user_data["message_count"]+1),
                "user_subjectivity_avg": (user_data["user_subjectivity_avg"]+(doc._.polarity-user_data["user_subjectivity_avg"])/user_data["message_count"]+1)
            }
            self.user_collection.update_one({"user_hash": user_data["user_hash"]}, {"$set": user_update}, upsert=True)




# seperate object to be imbedded in message ...
# print(message.mentions[0].activities)
# print(message.mentions[0].joined_at)
# print(message.mentions[0].guild)  # not nessesary?
# print(message.mentions[0]._user)  # hash it
if __name__ == "__main__":
    client = MyClient()
    client.run(os.getenv('PUBLIC_KEY'))

# discord_client = discord.Client()
#
#
# def get_database():
#     """
#     This function gets the database
#     @return: Returns the mongo client
#     """
#     mongo_client = MongoClient(os.getenv('MONGO_CONNECTION_STRING'))
#     return mongo_client['test_server']
#
#
# @discord_client.event
# async def on_ready():
#     """
#     Function prints bot info when logged in and ready.
#     @return: void
#     """
#     print(f'logged in {discord_client.user} has connected to Discord!')
#
#
# @discord_client.event
# async def on_message(message):
#     if message.author == discord_client.user:
#         return
#     records = db_users.find({})
#     print(records[0])
#     # await message.channel.send("poof")
#
#
# if __name__ == "__main__":
#     db = get_database()
#     db_users = db['users']
#     discord_client.run(os.getenv('PUBLIC_KEY'))
