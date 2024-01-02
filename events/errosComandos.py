import discord
from discord.ext import commands
from discord import app_commands

class ErrorHandler(commands.Cog):
    def __init__(self,client: commands.Bot):
      self.client = client
      client.tree.on_error = self.on_app_command_error

    async def on_app_command_error(self,interaction: discord.Interaction , error: app_commands.AppCommandError):
      message = ""
      if isinstance(error,app_commands.CheckFailure):
        if(interaction.command.name == "setavatar"):
          message = "Você não tem permissão para executar esse comando."
        elif(interaction.command.name == "desmutar"):
          message = "Você não esta mutado ou em um canal de voz."
        else:
          message = "Aconteceu um erro na validação"
          await interaction.guild.get_member(352240724693090305).send(f"{error}\n{type(error)}")  
      else:
        message = "Aconteceu um erro interno ao executar o comando, o mesmo já foi registrado."
        await interaction.guild.get_member(352240724693090305).send(f"{error}\n{type(error)}")  

      await interaction.response.send_message(embed=discord.Embed(description=message,color=interaction.guild.me.color),ephemeral=True,delete_after=4)

async def setup(client:commands.Bot):
  await client.add_cog(ErrorHandler(client=client))