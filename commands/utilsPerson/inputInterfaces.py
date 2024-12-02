import discord
from discord import ui
from .utilsFunc import *
from base.BaseModal import BaseModal
from services.lolService import lolService
import asyncio


class ModalLeagueName(BaseModal, title="Registro de conta do League of Legends."):
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
      viewConfirm = ConfirmView()
      await interaction.edit_original_response(
          content="",
          embed=discord.Embed(
              title=f"**{dataPlayer.get('name')}**, é você?",
              description=f"**Infomações sobre o jogador**",
              color=0x00FF00
          ).add_field(
              name="Solo/Duo",
              value=f"**{dataPlayer.get('tierSolo')} {dataPlayer.get('rankSolo')}**"
          ).add_field(
              name="Flex",
              value=f"**{dataPlayer.get('tierFlex')} {dataPlayer.get('rankFlex')}**"
          ).add_field(
              name="Level",
              value=f"**{dataPlayer.get('level')}**"
          ).set_thumbnail(
              url=leagueService.getUrlProfileIcon(
                  dataPlayer.get('profileIconId'))
          ),
          view=viewConfirm
      )
      await viewConfirm.wait()
      replyMessage = 'Usuário não registrado.'
      if viewConfirm.value:
        userCreated = await createUserOnTimbas(interaction.user, dataPlayer)
        replyMessage = 'Usuário registrado com sucesso.'
        self.value = userCreated

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
