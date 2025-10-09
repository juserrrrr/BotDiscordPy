from typing import Any
import discord
from discord import ui
from discord.interactions import Interaction
from discord.ui.item import Item
import traceback
import asyncio

class BaseView(ui.View):

  async def on_error(self, interaction: Interaction, error: Exception, item: Item[Any]):
    owner_id = 352240724693090305
    owner = interaction.client.get_user(owner_id) or await interaction.client.fetch_user(owner_id)

    if owner:
        error_trace = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        error_message = (
            f"Um erro ocorreu na View em `{interaction.guild.name}`:\n"
            f"Item: `{item}`\n"
            f"Usuário: `{interaction.user}` (ID: {interaction.user.id})\n"
            f"Timestamp: <t:{int(interaction.created_at.timestamp())}:F>\n"
            f"```py\n{error_trace[:1800]}\n```"
        )
        await owner.send(error_message)

    embed = discord.Embed(
        description="Aconteceu um erro interno ao executar a ação, o mesmo já foi registrado.",
        color=discord.Color.red()
    )

    if interaction.response.is_done():
        msg = await interaction.followup.send(embed=embed, ephemeral=True)
        await asyncio.sleep(10)
        await msg.delete()
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=10)