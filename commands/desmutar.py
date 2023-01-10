import discord
from discord.ext import commands
from discord import app_commands

class Desmutar(commands.Cog):
    def __init__(self,client: commands.Bot):
        self.client = client
    
    def checkUser(interaction: discord.Interaction) -> bool:
      return not interaction.user.voice is None and interaction.user.voice.mute

    @app_commands.command(name = 'desmutar',description="Desmusta o proprio usuario que digitou o comando.")
    @app_commands.guild_only()
    @app_commands.check(checkUser)
    async def desmutar(self,interaction: discord.Interaction):
      await interaction.user.edit(mute=False)
      await interaction.response.send_message(embed=discord.Embed(description="Você foi desmutado.",color=interaction.guild.me.color),ephemeral=True,delete_after=4)
   
async def setup(client: commands.Bot):
    await client.add_cog(Desmutar(client))