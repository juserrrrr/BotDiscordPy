import discord
from discord import ui
from discord.interactions import Interaction

class BaseModal(ui.Modal):


  async def on_error(self, interaction: Interaction, error: Exception):
    ownerBot = interaction.guild.get_member(352240724693090305)

    await ownerBot.send(f'MODAL ERRO\n{error}\n{type(error)}')

    return await interaction.response.send_message(embed=discord.Embed(description="Aconteceu um erro interno ao executar a ação, o mesmo já foi registrado.",color=interaction.guild.me.color),ephemeral=True,delete_after=4)