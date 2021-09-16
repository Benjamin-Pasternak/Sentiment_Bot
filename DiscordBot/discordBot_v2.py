"""
@author Benjamin Pasternak
"""
import discord
import spacy
import emoji
import preprocessor as p
from spacytextblob.spacytextblob import SpacyTextBlob
import pymongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import hashlib
import urllib
from datetime import datetime, date
from transformers import DistilBertTokenizerFast
from transformers import TFDistilBertForSequenceClassification
import tensorflow_datasets as tfds
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
import random
import numpy as np

random.seed(42)
p.set_options(p.OPT.MENTION, p.OPT.URL, p.OPT.NUMBER, p.OPT.SMILEY)  # this is for message cleaning
load_dotenv()  # loading the .env file which contains the public key and permissions int
nlp = spacy.load('en_core_web_lg')  # importing small model
nlp.add_pipe('spacytextblob')


# nlp.add_pipe('spacytextblob')

class MyClient(discord.Client):
    def assemble_URI(self):
        """
        This function assembles the URI for the mongodb database from environment variables
        @return: the mongo URI
        """
        return f'mongodb+srv://{urllib.parse.quote_plus(os.getenv("USER_NAME"))}:{urllib.parse.quote_plus(os.getenv("PASS"))}{os.getenv("LATTER_URI")}'
        # return f'mongodb://{urllib.parse.quote_plus(os.getenv("1"))}:{urllib.parse.quote_plus(os.getenv("2"))}{os.getenv("3")}'

    def __init__(self):
        self.con = MongoClient(self.assemble_URI())
        self.db = self.con["discord_test"]
        self.messages_collection = self.db["message_collection"]
        self.user_collection = self.db["user_collection"]
        self.secure_messages_collection = self.db["secure_messages_collection"]
        self.tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')
        self.loaded_model = TFDistilBertForSequenceClassification.from_pretrained('../jupyter_notebooks/new_BERT_model')
        super().__init__()  # init is inherited from discord.Client, so you need to make sure that
        # you are not overwriting this inherited constructor by calling super. oop for ya ...

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print(self.con['test_server'])
        print(self.messages_collection)
        print('-' * 20)

    async def measure_tone(self, text: str) -> str:
        """
        This function uses DistilBert that has been tuned to output the tone of input text.
        @param text: the user's cleaned message
        @return: the tone prediction
        """
        predict_input = self.tokenizer.encode(text,
                                              truncation=True,
                                              padding=True,
                                              return_tensors="tf")
        tf_output = self.loaded_model.predict(predict_input)[0]
        tf_prediction = tf.nn.softmax(tf_output, axis=1)
        labels = [0, 1, 2, 3, 4, 5]
        label = tf.argmax(tf_prediction, axis=1)
        label = label.numpy()
        return labels[label[0]]

    async def plot_personality(self, record, channel, user):
        # very unlikely that 2 plots with the same name will be generated at the same time
        filename = f'./pics/{random.randint(1, 10000000)}.png'
        labels = np.array(['anger', 'fear', 'joy', 'love', 'sadness', 'surprise'])
        stats = [
            record['anger_count'],
            record['fear_count'],
            record['joy_count'],
            record['love_count'],
            record['sadness_count'],
            record['surprise_count']
        ]
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
        fig = plt.figure()
        # figure_scale = sum(stats)+100
        ax = fig.add_subplot(111, polar=True)
        ax.plot(angles, stats, 'o-', linewidth=2)
        ax.fill(angles, stats, alpha=0.25)
        ax.set_thetagrids(angles * 180 / np.pi, labels)
        ax.set_title(f'Personality Report For {user}')
        ax.grid(True)
        fig.savefig(filename)
        image = discord.File(filename)
        await channel.send(file=image)
        os.remove(filename)  # don't wanna eat up storage space on computer so delete after send
        return

    async def message_clean(self, text: str) -> str:
        return emoji.demojize(p.clean(text), delimiters=('', '')).replace('_', ' ')

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
        mapping = {
            0: 'anger',
            1: 'fear',
            2: 'joy',
            3: 'love',
            4: 'sadness',
            5: 'surprise'
        }
        tone = mapping[await self.measure_tone(clean_message_content)]
        print('-'*30)
        print(f'got a message from {message.author}')  # hash it
        print(f'message body: {message.content}')  # measure it
        print('-' * 30)
        # special messages
        if message.content[:6] == '~~help':
            image = discord.File('./pics/howtouse.png')
            await message.channel.send(file=image)
            return

        elif message.content[:13] == '~~personality':
            if len(message.mentions) == 0:
                return
            else:
                key = hashlib.sha1(str(message.mentions[0]._user).encode()).hexdigest()
                # print(message.mentions[0]._user)  #Intransigent Iconoclast#9091
                user_data = self.user_collection.find_one({"user_hash": key})
                if user_data is not None:
                    await self.plot_personality(user_data, message.channel, message.mentions[0]._user)
                return

        elif message.content[:10] == '~~polarity':
            if len(message.mentions) == 0:
                return
            else:
                key = hashlib.sha1(str(message.mentions[0]._user).encode()).hexdigest()
                # print(message.mentions[0]._user)  #Intransigent Iconoclast#9091
                user_data = self.user_collection.find_one({"user_hash": key})
                if user_data is not None:
                    await message.channel.send(
                        f'{message.mentions[0]._user} average positivity = {user_data["user_polarity_avg"]} and their average subjectivity = {user_data["user_subjectivity_avg"]}.')
                return

        # updateing user collection
        user_data = self.user_collection.find_one({"user_hash": user_hash})  # finds person with username
        if user_data is None:  # create new user entry
            # info on cumulative averages https://math.stackexchange.com/questions/106700/incremental-averageing pls
            # note that ints in python are 32bit and therefore will roll over at 2^31 - 1 messages... likely not an
            # issue but perhaps it needs attention when and if it causes bot to crash...
            new_user = {
                "user_hash": user_hash,
                "message_count": 1,
                "user_polarity_avg": doc._.polarity,
                "user_subjectivity_avg": doc._.subjectivity,
                'datetime_collected': datetime.now(),
                'anger_count': 0 if tone != 'anger' else 1,
                'fear_count': 0 if tone != 'fear' else 1,
                'joy_count': 0 if tone != 'joy' else 1,
                'love_count': 0 if tone != 'love' else 1,
                'sadness_count': 0 if tone != 'sadness' else 1,
                'surprise_count': 0 if tone != 'surprise' else 1,

            }
            self.user_collection.update_one({"user_hash": new_user["user_hash"]}, {"$set": new_user}, upsert=True)
        elif user_data is not None:
            # time_difference = (datetime.datetime.fromisoformat(user_data['datetime_collected'])-datetime.now(
            # )).total_seconds()

            user_update = {
                "user_hash": user_hash,
                "message_count": (user_data["message_count"] + 1),
                "user_polarity_avg": (
                        user_data["user_polarity_avg"] + (doc._.polarity - user_data["user_polarity_avg"]) /
                        user_data["message_count"] + 1),
                "user_subjectivity_avg": (
                        user_data["user_subjectivity_avg"] + (doc._.polarity - user_data["user_subjectivity_avg"]) /
                        user_data["message_count"] + 1),
                'anger_count': user_data['anger_count'] if tone != 'anger' else user_data['anger_count'] + 1,
                'fear_count': user_data['fear_count'] if tone != 'fear' else user_data['fear_count'] + 1,
                'joy_count': user_data['joy_count'] if tone != 'joy' else user_data['joy_count'] + 1,
                'love_count': user_data['love_count'] if tone != 'love' else user_data['love_count'] + 1,
                'sadness_count': user_data['sadness_count'] if tone != 'sadness' else user_data['sadness_count'] + 1,
                'surprise_count': user_data['surprise_count'] if tone != 'surprise' else user_data[
                                                                                             'surprise_count'] + 1,
            }
            self.user_collection.update_one({"user_hash": user_data["user_hash"]}, {"$set": user_update}, upsert=True)

        # now we'd like to update the other collection with each message and a time stamp for aggregation
        message_record = {
            'user_hash': user_hash,
            'datetime_created': datetime.now(),
            'tone': tone,
            'polarity': doc._.polarity,
            'subjectivity': doc._.subjectivity,
            'message_clean': clean_message_content,
            'message_original': message.content
        }
        self.messages_collection.insert_one(message_record)


# seperate object to be imbedded in message ...
# print(message.mentions[0].activities)
# print(message.mentions[0].joined_at)
# print(message.mentions[0].guild)  # not nessesary?
# print(message.mentions[0]._user)  # hash it
if __name__ == "__main__":
    client = MyClient()
    client.run(os.getenv('PUBLIC_KEY'))
