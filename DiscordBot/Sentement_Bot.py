import re

import discord
from textblob import TextBlob


class MyClient(discord.Client):
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

        if re.match("^[a-zA-Z]+.*", message.content):

            wiki = TextBlob(message.content)
            temp = wiki.sentiment.polarity

            if message.author.id in self.dic:

                pol = self.dic[message.author.id][0]
                val = self.dic[message.author.id][1]

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

        if member.guild.roles is None and self.dic[message.author.id][0] <= -0.75:

            await message.channel.send('{0.author.mention} You are a salty motherfucker,'
                                       ' you know that?'.format(message))
            await member.add_roles(role)

        elif role in member.guild.roles and self.dic[message.author.id][0] >= 0.5:
            await message.channel.send("{0.author.mention} You're alright, "
                                       "keep up the good work amigo.".format(message))
            await member.remove_roles(role)
            await member.add_roles(role1)

        elif role1 in member.guild.roles and self.dic[message.author.id][0] <= -0.75:
            await message.channel.send('{0.author.mention} You are a salty mother fucker,'
                                       ' you know that?'.format(message))
            await member.remove_roles(role1)
            await member.add_roles(role)


client = MyClient()
client.run('Njg4MDk0MDMyMzUzNTU4NTQ4.XmvVRg.SqWdWcJjECZUEcCchvOzLualTag')