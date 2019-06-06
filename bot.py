import discord
import random
import json
import os
import config
from discord.ext import commands

client = commands.Bot(command_prefix = '!')
os.chdir(config.localfolder)

@client.event
async def on_reaction_add(reaction, user):
    channel = reaction.message.channel
    print('{} has added {} to the message: {}'.format(user.name, reaction.emoji, reaction.message.content))
     
@client.event
async def on_ready():
    print('Bot is ready.')
    await client.change_presence(game=discord.Game(name='!help'),status=discord.Status.online)

@client.command(pass_context=True, aliases=['lo'])
async def logout(ctx):
    if not ctx.message.author.id == config.owner_id:
        await client.say("Command limited to owner")
        return
    try:
        await client.say("Disconnecting SQL")
        client.cogs['SQL'].disconnect()
        await client.say("Logging out - Bye!")
        await client.logout()
    except:
        await client.say("Error logging out")
    
@client.command(pass_context=True, aliases=['flo'])
async def forcelogout(ctx):
    if not ctx.message.author.id == config.owner_id:
        await client.say("Command limited to owner")
        return
    await client.say("Logging out - Bye!")
    await client.logout()

extensions = ['statistics', 'sql', 'characters', 'player', 'cards', 'decks', 'tripletriad', 'fishing']
if __name__ == '__main__':
    for extension in extensions:
        try:
            client.load_extension(extension)
            print('Loaded extension: {}'.format(extension))
        except Exception as error:
            print('{} cannot be loaded. [{}]'.format(extension, error))

if __name__ == '__main__':
    import config 
    client.run(config.TOKEN)