import discord
from discord import ui
from .utilsFunc import *
from .inputInterfaces import *
from services.timbasService import timbasService
from discord import app_commands


class BtnJoinCustomMatch(ui.Button):
  def __init__(self, channelWaiting: discord.VoiceChannel, confirmedUsers: list, embedMessage, onlineMode: app_commands.Choice[int], formate: app_commands.Choice[int], view: ui.View):
    super().__init__(label="Entrar", style=discord.ButtonStyle.green, emoji='✅')
    self.channelWaiting = channelWaiting
    self.confirmedUsers = confirmedUsers
    self.embedMessage = embedMessage
    self.viewBtn = view
    self.onlineMode = onlineMode
    self.formate = formate

  async def checkAndGetRegisterLeague(self, interaction: discord.Interaction):
    timbasApi = timbasService()
    user = interaction.user
    responseUser = timbasApi.getUserByDiscordId(user.id)
    if responseUser is not None:
      if not checkUserIsRegistered(responseUser):
        modal = ModalLeagueName()
        await interaction.response.send_modal(modal)
        await modal.wait()
        # Melhorar isso aqui depois.
        return modal.value.json() if modal.value is not None else None
      return responseUser.json()
    await interaction.response.send_message(
        content="Infelizmente a conexão com o servidor não foi estabelicida, tente novamente mais tarde.",
        ephemeral=True,
        delete_after=3
    )
    return None

  async def callback(self, interaction: discord.Interaction):
    userDiscord = interaction.user
    userRegistered = None
    if (userDiscord.voice == None):
      return await interaction.response.send_message(
          embed=discord.Embed(description="Você não esta em um canal de voz.",
                              color=interaction.guild.me.color),
          ephemeral=True,
          delete_after=3
      )
    if (self.onlineMode.value == 1):
      userRegistered = await self.checkAndGetRegisterLeague(interaction)

    if userRegistered is None and self.onlineMode.value == 1:
      return
    elif not userDiscord in self.confirmedUsers or True:
      await userDiscord.move_to(self.channelWaiting)
      self.confirmedUsers.append(userDiscord)
      self.viewBtn.amountBtn.label = f"{len(self.confirmedUsers)}/10"
      if len(self.confirmedUsers) == 10:
        self.viewBtn.joinBtn.disabled = True
        self.viewBtn.startBtn.disabled = False
      if (interaction.response.is_done()):
        await interaction.edit_original_response(
            embed=self.embedMessage(
                self.confirmedUsers, self.onlineMode, self.formate),
            view=self.viewBtn
        )
      else:
        await interaction.response.edit_message(
            embed=self.embedMessage(
                self.confirmedUsers, self.onlineMode, self.formate),
            view=self.viewBtn
        )
    else:
      await interaction.response.send_message(
          embed=discord.Embed(description="Você já está confirmado.",
                              color=interaction.guild.me.color),
          ephemeral=True,
          delete_after=3
      )


class BtnExitCustomMatch(ui.Button):
  def __init__(self, channelHome: discord.VoiceChannel, confirmedUsers: list, embedMessage, onlineMode: app_commands.Choice[int], formate: app_commands.Choice[int], view: ui.View):
    super().__init__(label="Sair", style=discord.ButtonStyle.red, emoji='🚪')
    self.channelHome = channelHome
    self.confirmedUsers = confirmedUsers
    self.embedMessage = embedMessage
    self.viewBtn = view
    self.onlineMode = onlineMode
    self.formate = formate

  async def callback(self, interaction: discord.Interaction):
    user = interaction.user
    if user in self.confirmedUsers:
      if (user.voice != None):
        await user.move_to(self.channelHome)
      self.confirmedUsers.remove(user)
      self.viewBtn.amountBtn.label = f"{len(self.confirmedUsers)}/10"
      if len(self.confirmedUsers) < 10:
        self.viewBtn.joinBtn.disabled = False
        self.viewBtn.startBtn.disabled = True
      await interaction.response.edit_message(embed=self.embedMessage(self.confirmedUsers, self.onlineMode, self.formate), view=self.viewBtn)
    else:
      await interaction.response.send_message(embed=discord.Embed(description="Você não está confirmado.", color=interaction.guild.me.color), ephemeral=True, delete_after=3)


class BtnAmountCustomMatch(ui.Button):
  def __init__(self):
    super().__init__(label=f"0/10", style=discord.ButtonStyle.grey,
                     emoji="🧑🏻‍💻", disabled=True)

  async def callback(self, _: discord.Interaction):
    return


class BtnStartCustomMatch(ui.Button):
  def __init__(self, userCallCommand: discord.User, channelBlue: discord.VoiceChannel, channelRed: discord.VoiceChannel, confirmedUsers: list, embedMessageTeam, view: ui.View):
    super().__init__(label="Start", style=discord.ButtonStyle.success, emoji="▶", disabled=True)
    self.userCallCommand = userCallCommand
    self.channelBlue = channelBlue
    self.channelRed = channelRed
    self.confirmedUsers = confirmedUsers
    self.embedMessageTeam = embedMessageTeam
    self.viewBtn = view

  async def callback(self, interaction: discord.Interaction):
    if (interaction.user == self.userCallCommand):
      self.viewBtn.startBtn.disabled = True
      self.viewBtn.exitBtn.disabled = True
      blueTeam, redTeam = drawTeam(self.confirmedUsers)
      textBlueTeam = blueTeam
      textRedTeam = redTeam
      await interaction.response.edit_message(
          embed=self.embedMessageTeam(textBlueTeam, textRedTeam),
          view=self.viewBtn
      )
      await moveTeam(blueTeam, self.channelBlue)
      await moveTeam(redTeam, self.channelRed)
    else:
      await interaction.response.send_message(embed=discord.Embed(description="Somente o criador da personalizada pode executar esta ação.", color=interaction.guild.me.color), ephemeral=True, delete_after=3)


class BtnSwitchSideCustomMatch(ui.Button):
  def __init__(self, channelBlue: discord.VoiceChannel, channelRed: discord.VoiceChannel, confirmedUsers: list, embedMessageTeam, view: ui.View):
    super().__init__(label="Trocar de lado", style=discord.ButtonStyle.primary, emoji="🔄")
    self.channelBlue = channelBlue
    self.channelRed = channelRed
    self.confirmedUsers = confirmedUsers
    self.embedMessageTeam = embedMessageTeam
    self.viewBtn = view

  async def callback(self, interaction: discord.Interaction):
    blueUsers = [
        user for user in self.confirmedUsers if user.voice.channel == self.channelBlue]
    redUsers = [
        user for user in self.confirmedUsers if user.voice.channel == self.channelRed]
    if (len(blueUsers) == 5 and len(redUsers) == 5):
      for user in blueUsers:
        await user.move_to(self.channelRed)
      for user in redUsers:
        await user.move_to(self.channelBlue)
      textBlueTeam = redUsers
      textRedTeam = blueUsers
      await interaction.response.edit_message(
          embed=self.embedMessageTeam(textBlueTeam, textRedTeam),
          view=self.viewBtn
      )
    else:
      await interaction.response.send_message(embed=discord.Embed(description="Os times não estão completos.", color=interaction.guild.me.color), ephemeral=True, delete_after=3)
