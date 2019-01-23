#Handles all server and statistics functions:
#   Checking total channels and players, etc
import discord
from discord.ext import commands

class Stats:
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def stats(self):
        members = self.client.get_all_members()
        numMembers = sum(1 for _ in members)
        await self.client.say('Number of members across all servers: {}'.format(numMembers))

def setup(client):
    client.add_cog(Stats(client))