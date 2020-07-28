import re
import discord
from textblob import TextBlob


class MyClient(discord.Client):
    # this keeps track of the users and their average message sentement 
    dic = {}

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return
        # We want the message content to begin with something valid 
        if re.match("^[a-zA-Z]+.*", message.content):
            # this converts the message into a number which indicates the sentement. 
            # Small numbers are negative, high numbers are positive,  == 0 are neurtral
            wiki = TextBlob(message.content)
            temp = wiki.sentiment.polarity
            
            # if the message author has spoken in the discord server before ... do
            if message.author.id in self.dic:
                # assigning pol and val to the average existing polarity and the scaling factor for frequency of messages
                # and difficulty becoming more or less positive 
                pol = self.dic[message.author.id][0]
                val = self.dic[message.author.id][1]
                
                # if message sentement is positive and scaling factor == 3
                if temp < 0 and self.dic[message.author.id][1] == 3:
                    newPol = (pol * val + temp) / val
                    self.dic[message.author.id][0] = newPol
                    print(self.dic)

                elif temp < 0 and self.dic[message.author.id][1] > 3:
                    self.dic[message.author.id][1] -= 1
                    val = self.dic[message.author.id][1]
                    newPol = (pol * val + temp) / val
                    self.dic[message.author.id][0] = newPol
                    print(self.dic)

                elif temp >= 0 and self.dic[message.author.id][1] < 25:
                    self.dic[message.author.id][1] += 1
                    val = self.dic[message.author.id][1]
                    newPol = (pol * val + temp) / val
                    self.dic[message.author.id][0] = newPol
                    print(self.dic)

                elif temp >= 0 and self.dic[message.author.id][1] == 25:
                    newPol = (pol * val + temp) / val
                    self.dic[message.author.id][0] = newPol
                    print(self.dic)
            
            # if author is not in the dict
            else:
                self.dic.update({message.author.id: [0.0, 25]})
                pol = self.dic[message.author.id][0]
                val = self.dic[message.author.id][1]
                if temp < 0:
                    newPol = (pol * val + temp) / val
                    self.dic[message.author.id][0] = newPol
                    print(self.dic)

                else:
                    newPol = (pol * val + temp) / val
                    self.dic[message.author.id][0] = newPol
                    print(self.dic)

        # this part assigns roles
        member = message.author
        role = discord.utils.get(member.guild.roles, name="salt_boi")
        role1 = discord.utils.get(member.guild.roles, name="good_boi")
        
        # if member does not already have role and average sentement is <=-0.75
        if member.guild.roles is None and self.dic[message.author.id][0] <= -0.75:

            await message.channel.send('{0.author.mention} You are a salty motherfucker,'
                                       ' you know that?'.format(message))
            await member.add_roles(role)
        # if user has bad role and is becoming a good boi
        elif role in member.guild.roles and self.dic[message.author.id][0] >= 0.5:
            await message.channel.send("{0.author.mention} You're alright, "
                                       "keep up the good work amigo.".format(message))
            await member.remove_roles(role)
            await member.add_roles(role1)
        # if user has good role but is becoming bad boi
        elif role1 in member.guild.roles and self.dic[message.author.id][0] <= -0.75:
            await message.channel.send('{0.author.mention} You are a salty mother fucker,'
                                       ' you know that?'.format(message))
            await member.remove_roles(role1)
            await member.add_roles(role)

# runs the client (will need to register a discord bot of your own and need your own discord number thing)
# Also this program can be run locally on a discord server that you own or hosted on heroku should you want it to run indefinitly 
client = MyClient()
client.run('Njg4MDk0MDMyMzUzNTU4NTQ4.XmvVRg.SqWdWcJjECZUEcCchvOzLualTag')
