import discord
from discord.ext import commands
from discord import app_commands

class TrazerTodos(commands.Cog):
    def __init__(self,client: commands.Bot):
        self.client = client
    
    @app_commands.command(name = 'puxartodos',description="Puxa todos os usuários até o seu canal.")
    @app_commands.guild_only()
    async def trazerTodos(self,interaction: discord.Interaction):

      afkChannel = interaction.guild.afk_channel
      authorChannel = interaction.user.voice.channel
      for channel in interaction.guild.voice_channels:
        if not channel == authorChannel and len(channel.members) > 0 or channel == afkChannel:
          for member in channel.members:
            await member.move_to(authorChannel)
      await interaction.response.send_message(embed=discord.Embed(description="Comando executado com sucesso!",color=interaction.guild.me.color),ephemeral=True,delete_after=4)

async def setup(client: commands.Bot):
    await client.add_cog(TrazerTodos(client))