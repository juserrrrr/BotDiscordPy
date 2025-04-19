import discord
from discord import ui
from .utilsFunc import createUserOnTimbas


class VerificationView(ui.View):
  def __init__(self, leagueService, dataPlayer, verificationIconId):
    super().__init__()
    self.value = None
    self.leagueService = leagueService
    self.dataPlayer = dataPlayer
    self.verificationIconId = verificationIconId
    self.replyMessage = 'Usuário não registrado.'

  @discord.ui.button(label='Verificar', style=discord.ButtonStyle.green)
  async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):

    # Responder à interação primeiro
    await interaction.response.defer()

    self.value = True
    # Verificar se o usuário mudou o ícone
    currentProfileIcon = self.leagueService.getSummonerByPuuid(
        self.dataPlayer.get('puuid'))
    if currentProfileIcon.json().get('profileIconId') == self.verificationIconId:
      userCreated = await createUserOnTimbas(interaction.user, self.dataPlayer)
      if userCreated.status_code != 201:
        self.replyMessage = 'Erro ao registrar usuário. Tente novamente mais tarde.'
        self.value = False
      else:
        self.replyMessage = 'Usuário registrado com sucesso.'
        self.value = userCreated
    else:
      self.replyMessage = 'Você não mudou o ícone de perfil. Por favor, tente novamente.'

    self.stop()

  @discord.ui.button(label='Cancelar', style=discord.ButtonStyle.red)
  async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
    self.value = False
    self.stop()
