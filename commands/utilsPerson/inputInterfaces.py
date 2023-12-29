import discord
from discord import ui
from .utilsFunc import *

class ModalLeagueName(ui.Modal, title="Informação importante para o sistema :)"):

    leagueName = ui.TextInput(
        label="Digite o nome da sua conta",
        min_length=3,
        max_length=16,
        placeholder="Ex: Timbas#BR1",
        custom_id="leagueName",
        )


    async def on_submit(self, interaction: discord.Interaction):
      await interaction.response.send_message(content="Obrigado, aguarde um instante, enquanto verifico.", ephemeral=True)
      await showUser(interaction, self.leagueName.value)

