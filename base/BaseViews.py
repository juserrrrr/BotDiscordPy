from typing import Any
import discord
from discord import ui
from discord.interactions import Interaction
from discord.ui.item import Item


class BaseView(ui.View):

  async def on_error(self, interaction: Interaction, error: Exception, item: Item[Any]):
    ownerBot = interaction.guild.get_member(352240724693090305)

    await ownerBot.send(f'{error.args[0]}\n{type(error)}\n{item}')

    return await interaction.response.send_message(embed=discord.Embed(description="Aconteceu um erro interno ao executar a ação, o mesmo já foi registrado.",color=interaction.guild.me.color),ephemeral=True,delete_after=5)
