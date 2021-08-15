"""
@author Benjamin Pasternak
"""
import discord
import spacy
import re
from spacytextblob.spacytextblob import SpacyTextBlob
import pymongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import hashlib
from datetime import datetime

load_dotenv()  # loading the .env file which contains the public key and permissions int

nlp = spacy.load('en_core_web_lg')  # importing small model


# nlp.add_pipe('spacytextblob')

class MyClient(discord.Client):

    def __init__(self):
        self.con = MongoClient(os.getenv('MONGO_CONNECTION_STRING'))
        self.messages_collection = self.con["message_collection"]
        self.user_collection = self.con["user_collection"]
        self.secure_messages_collection = self.con["secure_messages_collection"]
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
        @param text: the text portion of message object
        @return: clean_text: processed cleaned text
        """

        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'<:\w*:\d*>', '', text)
        text = re.sub('\s\s+', ' ', text)
        text = re.sub('\n', '', text)
        print(text)

    async def on_message(self, message):
        """
        This function controls the user interface, user tracking logic and message logging.
        @param message: the message most recently entered
        @return: void
        """
        # message from bot don't respond else infinite loop
        if message.author.id == self.user.id:
            return

        print(f'got a message from {message.author}')  # hash it
        print(f'message body: {message.content}')  # mesure it
        # special messages
        if message.content[:6] == '~~help':
            await message.channel.send("```md\n# Instructions:\n1. ~~help :command is used to summon this instruction "
                                       "manual\n2. ~~user <username#0001> :command is used to get user stats\n3. "
                                       "~~sentiment <message> :classify how message\n4. ~~intent <message> :classify "
                                       "the message intent```")

        elif message.content[:6] == '~~user':
            await message.channel.send("Under development")

        elif message.content[:11] == '~~sentiment':
            await message.channel.send("Under development")

        elif message.content[:8] == '~~intent':
            await message.channel.send("Under development")
        # user tracking logic
        clean_message_content = await self.message_clean(message.content)



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
