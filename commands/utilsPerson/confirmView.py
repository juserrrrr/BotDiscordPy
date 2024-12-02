import discord
from discord import ui


class ConfirmView(ui.View):
  def __init__(self):
    super().__init__()
    self.value = None

  @ui.button(label='Confirmar', style=discord.ButtonStyle.green)
  async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
    self.value = True
    self.stop()

  @ui.button(label='Cancelar', style=discord.ButtonStyle.red)
  async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
    self.value = False
    self.stop()
