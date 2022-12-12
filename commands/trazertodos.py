import discord
from discord.ext import commands
from discord import app_commands

class PullAll(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @app_commands.command(name = 'puxartodos')
    @commands.has_role(785650860125978635)
    async def pullall(self,interaction: discord.Interaction):
        channel_author = interaction.user.voice.channel
        for channel in interaction.guild.voice_channels:
          if not channel == channel_author and len(channel.members) > 0:
            for member in channel.members:
                await member.move_to(channel_author)
        await interaction.response.send_message(embed=discord.Embed(description="Comando executado com sucesso!",color=interaction.guild.me.color),ephemeral=True,delete_after=4)

async def setup(client):
    await client.add_cog(PullAll(client))