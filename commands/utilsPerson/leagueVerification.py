import discord
from discord import ui
from .utilsFunc import *
from base.BaseModal import BaseModal
from services.lolService import lolService
from .verificationView import VerificationView
import asyncio
import random


class ModalLeagueVerification(BaseModal, title="Verificação de conta do League of Legends"):
  def __init__(self):
    super().__init__()
    self.value = None

  leagueName = ui.TextInput(
      label="Nick da sua conta(Necessário uma única vez)",
      min_length=3,
      max_length=24,
      placeholder="Ex: Timbas#BR1",
      custom_id="leagueName",
      required=True
  )

  async def getRandomIconId(self, currentIconId: int) -> int:
    # Lista de ícones disponíveis (você pode ajustar conforme necessário)
    availableIcons = list(range(1, 5))  # Exemplo: ícones de 1 a 29
    if currentIconId in availableIcons:
      availableIcons.remove(currentIconId)
    return random.choice(availableIcons)

  async def on_submit(self, interaction: discord.Interaction):
    if self.leagueName.value.count('#') != 1:
      return await interaction.response.send_message(content="Verifique seu nick e tente novamente.", ephemeral=True, delete_after=2)
    await interaction.response.send_message(content="Obrigado, aguarde um instante, enquanto acho sua conta.", ephemeral=True)

    leagueService = lolService()

    dataPlayer = checkAndGetDataPlayerLeague(
        leagueService, self.leagueName.value)
    if dataPlayer is None:
      await interaction.edit_original_response(content="Não foi possível encontrar sua conta, verifique se digitou corretamente.", embed=None, view=None)
      await asyncio.sleep(2)
      return await interaction.delete_original_response()
    else:
      # Verificar o ícone atual do usuário
      currentProfileIcon = leagueService.getSummonerByPuuid(
          dataPlayer.get('puuid'))
      currentIconId = currentProfileIcon.json().get('profileIconId')

      # Escolher um ícone aleatório diferente do atual
      verificationIconId = await self.getRandomIconId(currentIconId)
      verificationIconUrl = leagueService.getUrlProfileIcon(verificationIconId)

      viewVerification = VerificationView(
          leagueService, dataPlayer, verificationIconId)
      await interaction.edit_original_response(
          content="",
          embed=discord.Embed(
              title=f"**{dataPlayer.get('name', 'Jogador')}**, é você?",
              description=f"**Para confirmar que esta conta é sua, por favor:**\n1. Mude seu ícone de perfil para o ícone abaixo\n2. Clique no botão 'Verificar' após mudar o ícone",
              color=0x00FF00
          ).add_field(
              name="Solo/Duo",
              value=f"**{dataPlayer.get('tierSolo', 'Unranked')} {dataPlayer.get('rankSolo', '')}**"
          ).add_field(
              name="Flex",
              value=f"**{dataPlayer.get('tierFlex', 'Unranked')} {dataPlayer.get('rankFlex', '')}**"
          ).add_field(
              name="Level",
              value=f"**{dataPlayer.get('level', '0')}**"
          ).set_thumbnail(
              url=verificationIconUrl
          ),
          view=viewVerification
      )

      await viewVerification.wait()
      replyMessage = viewVerification.replyMessage

      await interaction.edit_original_response(
          content="",
          embed=discord.Embed(
              description=f"**{replyMessage}**",
              color=0xFF0004
          ),
          view=None
      )
      await asyncio.sleep(2)
      return await interaction.delete_original_response()
