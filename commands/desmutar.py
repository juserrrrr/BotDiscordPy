import discord
from discord.ext import commands
from discord import app_commands

class Desmutar(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @app_commands.command(name = 'desmutar',description="Desmusta o proprio usuario que digitou o comando.")
    @app_commands.guild_only()
    async def desmutar(self,interaction: discord.Interaction):
      if not interaction.user.voice is None and interaction.user.voice.mute:
        await interaction.user.edit(mute=False)
        description_text = "Você foi desmutado."
      else:
        description_text = "Você não está em um canal de voz ou não está mutado."

      embed_message = discord.Embed(
        title = f"🎅 │ **{interaction.guild.name}**    ",
        description = f"**{description_text}**",
        color = 0xFF0004
      )
      embed_message.set_thumbnail(url = interaction.guild.icon.replace(format="png").url)
      await interaction.response.send_message(embed=embed_message,ephemeral=True,delete_after=4)

    @desmutar.error
    async def on_desmutar_error(self,interaction: discord.Interaction, error: app_commands.AppCommandError):
      print(f"Aconteceu um erro no servidor [{interaction.guild.name}]\nErro: {error}")
      await interaction.response.send_message(embed=discord.Embed(description="Aconteceu um erro interno!",color=interaction.guild.me.color),ephemeral=True,delete_after=4)
           
async def setup(client):
    await client.add_cog(Desmutar(client))