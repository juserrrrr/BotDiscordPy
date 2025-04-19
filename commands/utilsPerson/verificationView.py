import discord
from discord import ui


class VerificationView(ui.View):
  def __init__(self):
    super().__init__()
    self.value = None

  @ui.button(label='Verificar', style=discord.ButtonStyle.green)
  async def verify(self, interaction: discord.Interaction):
    self.value = True
    self.stop()

  @ui.button(label='Cancelar', style=discord.ButtonStyle.red)
  async def cancel(self, interaction: discord.Interaction):
    self.value = False
    self.stop()
