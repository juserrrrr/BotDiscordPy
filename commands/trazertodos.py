import discord
from discord.ext import commands

class PullAll(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.command(name = 'pullall')
    async def pullall(self,ctx):
        channel_author = ctx.author.voice.channel
        
        for channel in ctx.guild.voice_channels:
          if not channel == channel_author and len(channel.members) > 0:
            for member in channel.members:
                    await member.move_to(channel_author)

def setup(client):
    client.add_cog(PullAll(client))