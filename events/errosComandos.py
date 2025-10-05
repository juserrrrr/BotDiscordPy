import discord
from discord.ext import commands
from discord import app_commands
import traceback
import asyncio

class ErrorHandler(commands.Cog):
  def __init__(self, client: commands.Bot):
    self.client = client
    client.tree.on_error = self.on_app_command_error

  async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
    owner_id = 352240724693090305
    owner = self.client.get_user(owner_id) or await self.client.fetch_user(owner_id)

    if owner:
        error_trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        error_message = (
            f"Um erro de comando ocorreu em '{interaction.guild.name}':\n"
            f"Comando: `/{interaction.command.name if interaction.command else 'N/A'}`\n"
            f"Usuário: `{interaction.user}` (ID: {interaction.user.id})\n"
            f"Timestamp: <t:{int(interaction.created_at.timestamp())}:F>\n"
            f"```py\n{error_trace[:1800]}\n```"
        )
        await owner.send(error_message)

    user_message = "Aconteceu um erro interno ao executar o comando, o mesmo já foi registrado."

    if isinstance(error, app_commands.CommandOnCooldown):
        user_message = f"Este comando está em tempo de recarga. Tente novamente em {error.retry_after:.2f} segundos."
    elif isinstance(error, app_commands.MissingPermissions):
        user_message = "Você não tem permissão para usar este comando."
    elif isinstance(error, app_commands.CheckFailure):
        if (interaction.command.name == "setavatar"):
            user_message = "Você não tem permissão para executar esse comando."
        elif (interaction.command.name == "desmutar"):
            user_message = "Você não esta mutado ou em um canal de voz."
        else:
            user_message = "Você não atende aos pré-requisitos para usar este comando."

    embed = discord.Embed(
        description=user_message,
        color=discord.Color.red()
    )

    if interaction.response.is_done():
        msg = await interaction.followup.send(embed=embed, ephemeral=True)
        await asyncio.sleep(10)
        await msg.delete()
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=10)


async def setup(client: commands.Bot):
  await client.add_cog(ErrorHandler(client=client))