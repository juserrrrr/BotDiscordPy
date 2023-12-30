import discord
from discord import ui
from .utilsFunc import *

class ModalLeagueName(ui.Modal, title="Registro de conta do League of Legends."):

    
    leagueName = ui.TextInput(
        label="Nick da sua conta(Necessário uma única vez)",
        min_length=3,
        max_length=24,
        placeholder="Ex: Timbas#BR1",
        custom_id="leagueName",
        required=True
        )


    async def on_submit(self, interaction: discord.Interaction):
      await interaction.response.send_message(content="Obrigado, aguarde um instante, enquanto acho sua conta.", ephemeral=True)
      await showUser(interaction, self.leagueName.value)

