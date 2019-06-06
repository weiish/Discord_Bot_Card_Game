import discord
import random
import asyncio
import time
import json
from discord.ext import commands

class Fishing:
    def __init__(self, client):
        self.client = client
        self.sql = client.cogs['SQL']
        self.player = client.cogs['Player']
        self.cards = client.cogs['Cards']
        self.loaded_emojis = True
        with open('emoji.json', 'r') as in_f:
            self.emojis = json.load(in_f)
        
    async def load_emojis(self):
        emojis = self.client.get_all_emojis()
        #print(emojis)
        self.emojis = []
        for emoji in emojis:
            self.emojis.append(emoji)
        self.loaded_emojis = True

    async def get_random_emoji(self):
        maxNum = len(self.emojis)
        return self.emojis[random.randint(0,maxNum-1)]

    @commands.command(pass_context=True, aliases=['f'])
    async def fish(self, ctx, maxTime=30):
        if not self.loaded_emojis:
            await self.load_emojis()
        author = ctx.message.author
        maxTime = 5
        maxEventTime = 10
        startTime = time.time()
        timeElapsed = 0
        message = await self.client.say("{} casts out their line...".format(author.name))
        await self.client.add_reaction(message, '⬅')
        await self.client.add_reaction(message, '➡')
        await self.client.add_reaction(message, '⬆')
        await self.client.add_reaction(message, '⬇')
        
        while timeElapsed < maxTime:
            waitTime = min(maxEventTime * random.random() + 1, maxTime-timeElapsed)
            await asyncio.sleep(waitTime)
            timeElapsed = time.time() - startTime
            if timeElapsed >= maxTime:
                randomEvent = 6 #Ending event
            else:
                randomEvent = random.randint(1, 6)
            if randomEvent == 5:
                await self.client.edit_message(message, new_content="{} casts out their line... you feel nothing".format(author.name))
            elif randomEvent == 6:
                emoji = await self.get_random_emoji()
                await self.client.edit_message(message, new_content="{} casts out their line... you feel a solid bite! Quick, react with {}!".format(author.name, emoji))                                
                res = await self.client.wait_for_reaction(message=message, emoji=emoji,user=author,timeout=10)
                if not res:
                    await self.client.edit_message(message, new_content="{} casts out their line... you feel a solid bite! Quick, react with {}! ... it got away".format(author.name, emoji))
                    break
                else:
                    await self.client.edit_message(message, new_content="Congratulations {}! You caught **something**".format(author.name))
                    #await self.cards.get_random_card(ctx)
                    break
            else:
                if randomEvent == 1:
                    emoji = '⬅'
                    direction = "LEFT"
                elif randomEvent == 2:
                    emoji = '➡'
                    direction = "RIGHT"
                elif randomEvent == 3:
                    emoji = '⬆'
                    direction = "UP"
                elif randomEvent == 4:
                    emoji = '⬇'
                    direction = "DOWN"
                await self.client.edit_message(message, new_content="{} casts out their line... the line pulls **{}**!".format(author.name, direction))
                res = await self.client.wait_for_reaction(emoji=emoji,user=author,timeout=5)
                if not res:
                    await self.client.edit_message(message, new_content="{} casts out their line... the line pulls **{}**! ... it got away".format(author.name, direction))
                    break
                else:
                    await self.client.edit_message(message, new_content="{} casts out their line...".format(author.name))

def setup(client):
    client.add_cog(Fishing(client))