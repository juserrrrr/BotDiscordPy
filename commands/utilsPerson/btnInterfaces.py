import discord
from discord import ui
from .utilsFunc import *
from .leagueVerification import *
from services.timbasService import timbasService
from discord import app_commands
import asyncio
import random


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
        modal = ModalLeagueVerification()
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

    if userRegistered is None and self.onlineMode == 1:
      return
    elif not userDiscord in self.confirmedUsers:
      await userDiscord.move_to(self.channelWaiting)
      self.confirmedUsers.append(userDiscord)
      self.viewBtn.amountBtn.label = f"{len(self.confirmedUsers)}/10"
      if len(self.confirmedUsers) >= 10:
        self.viewBtn.joinBtn.disabled = True
        if self.formate.value == 0:
          self.viewBtn.sortearBtn.disabled = False
          self.viewBtn.startBtn.disabled = True
        else:
          self.viewBtn.switchSideBtn.disabled = False
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
        self.viewBtn.switchSideBtn.disabled = True
        self.viewBtn.sortearBtn.disabled = True
      await interaction.response.edit_message(embed=self.embedMessage(self.confirmedUsers, self.onlineMode, self.formate), view=self.viewBtn)
    else:
      await interaction.response.send_message(embed=discord.Embed(description="Você não está confirmado.", color=interaction.guild.me.color), ephemeral=True, delete_after=3)


class BtnAmountCustomMatch(ui.Button):
  def __init__(self):
    super().__init__(label=f"0/10", style=discord.ButtonStyle.grey,
                     emoji="🧑🏻‍💻", disabled=True)

  async def callback(self, _: discord.Interaction):
    return


class BtnSortearCustomMatch(ui.Button):
  def __init__(self, confirmedUsers: list, embedMessageTeam, view: ui.View, onlineMode: app_commands.Choice[int], formate: app_commands.Choice[int]):
    super().__init__(label="Sortear", style=discord.ButtonStyle.primary, emoji="🎲")
    self.confirmedUsers = confirmedUsers
    self.embedMessageTeam = embedMessageTeam
    self.viewBtn = view
    self.blueTeam = None
    self.redTeam = None
    self.onlineMode = onlineMode
    self.formate = formate

  async def callback(self, interaction: discord.Interaction):
    if len(self.confirmedUsers) == 10:
      self.blueTeam, self.redTeam = drawTeam(self.confirmedUsers.copy())

      # Habilita o botão de start após o sorteio
      self.viewBtn.startBtn.disabled = False
      # Desabilita o botão de sair após o sorteio
      self.viewBtn.exitBtn.disabled = True

      await interaction.response.edit_message(
          embed=self.embedMessageTeam(
              self.blueTeam,
              self.redTeam,
              self.onlineMode,
              self.formate
          ),
          view=self.viewBtn
      )
    else:
      await interaction.response.send_message(
          embed=discord.Embed(description="É necessário ter 10 jogadores confirmados para sortear os times.",
                              color=interaction.guild.me.color),
          ephemeral=True,
          delete_after=3
      )


class BtnStartCustomMatch(ui.Button):
  def __init__(self, userCallCommand: discord.User, channelBlue: discord.VoiceChannel, channelRed: discord.VoiceChannel, confirmedUsers: list, embedMessageTeam, view: ui.View, onlineMode: app_commands.Choice[int], formate: app_commands.Choice[int]):
    super().__init__(label="Start", style=discord.ButtonStyle.success, emoji="▶", disabled=True)
    self.userCallCommand = userCallCommand
    self.channelBlue = channelBlue
    self.channelRed = channelRed
    self.confirmedUsers = confirmedUsers
    self.embedMessageTeam = embedMessageTeam
    self.viewBtn = view
    self.onlineMode = onlineMode
    self.formate = formate
    self.blueTeam = None
    self.redTeam = None

  async def callback(self, interaction: discord.Interaction):
    if (interaction.user == self.userCallCommand):
      if self.formate.value == 0 and (self.viewBtn.sortearBtn.blueTeam is None or self.viewBtn.sortearBtn.redTeam is None):
        await interaction.response.send_message(
            embed=discord.Embed(description="Você precisa sortear os times primeiro!",
                                color=interaction.guild.me.color),
            ephemeral=True,
            delete_after=3
        )
        return

      # Primeiro atualiza a mensagem
      self.viewBtn.startBtn.disabled = True
      self.viewBtn.exitBtn.disabled = True
      self.viewBtn.sortearBtn.disabled = True
      self.viewBtn.finishBtn.disabled = False

      # Remove o botão de trocar de lado e ajusta a posição do botão de finalizar
      if self.viewBtn.switchSideBtn in self.viewBtn.children:
        self.viewBtn.remove_item(self.viewBtn.switchSideBtn)

      if self.viewBtn.sortearBtn in self.viewBtn.children:
        self.viewBtn.remove_item(self.viewBtn.sortearBtn)

      if self.formate.value == 0:
        self.blueTeam = self.viewBtn.sortearBtn.blueTeam
        self.redTeam = self.viewBtn.sortearBtn.redTeam
      else:
        # No modo livre, divide os times igualmente
        half = len(self.confirmedUsers) // 2
        team1 = self.confirmedUsers[:half]
        team2 = self.confirmedUsers[half:]
        # Sorteia qual time vai para qual lado
        if random.randint(0, 1) == 0:
          self.blueTeam = team1
          self.redTeam = team2
        else:
          self.blueTeam = team2
          self.redTeam = team1

      embed = self.embedMessageTeam(
          self.blueTeam,
          self.redTeam,
          self.onlineMode,
          self.formate,
          started=True
      )

      # Responde à interação primeiro
      await interaction.response.edit_message(
          embed=embed,
          view=self.viewBtn
      )

      # Depois move os times
      await moveTeam(self.blueTeam, self.channelBlue)
      await moveTeam(self.redTeam, self.channelRed)
    else:
      await interaction.response.send_message(
          embed=discord.Embed(description="Somente o criador da personalizada pode executar esta ação.",
                              color=interaction.guild.me.color),
          ephemeral=True,
          delete_after=3
      )


class BtnSwitchSideCustomMatch(ui.Button):
  def __init__(self, channelBlue: discord.VoiceChannel, channelRed: discord.VoiceChannel, confirmedUsers: list, embedMessageTeam, view: ui.View, onlineMode: app_commands.Choice[int], formate: app_commands.Choice[int]):
    super().__init__(label="Trocar de lado", style=discord.ButtonStyle.primary, emoji="🔄")
    self.channelBlue = channelBlue
    self.channelRed = channelRed
    self.confirmedUsers = confirmedUsers
    self.embedMessageTeam = embedMessageTeam
    self.viewBtn = view
    self.onlineMode = onlineMode
    self.formate = formate

  async def callback(self, interaction: discord.Interaction):
    if len(self.confirmedUsers) != 10:
      await interaction.response.send_message(
          embed=discord.Embed(description="É necessário ter 10 jogadores para trocar de lado.",
                              color=interaction.guild.me.color),
          ephemeral=True,
          delete_after=3
      )
      return

    user = interaction.user
    if user not in self.confirmedUsers:
      await interaction.response.send_message(
          embed=discord.Embed(description="Você não está na partida.",
                              color=interaction.guild.me.color),
          ephemeral=True,
          delete_after=3
      )
      return

    # Encontrar a posição do usuário na lista
    userIndex = self.confirmedUsers.index(user)
    # Encontrar o usuário correspondente do outro lado
    if userIndex < 5:  # Está no time azul
      otherUserIndex = userIndex + 5  # Usuário correspondente no time vermelho
    else:  # Está no time vermelho
      otherUserIndex = userIndex - 5  # Usuário correspondente no time azul

    otherUser = self.confirmedUsers[otherUserIndex]

    # Trocar as posições
    self.confirmedUsers[userIndex], self.confirmedUsers[otherUserIndex] = self.confirmedUsers[otherUserIndex], self.confirmedUsers[userIndex]

    # Atualizar a mensagem
    await interaction.response.edit_message(
        embed=self.embedMessageTeam(
            self.confirmedUsers[:5],
            self.confirmedUsers[5:],
            self.onlineMode,
            self.formate
        ),
        view=self.viewBtn
    )


class BtnFinishCustomMatch(ui.Button):
  def __init__(self, userCallCommand: discord.User, embedMessageTeam, view: ui.View, onlineMode: app_commands.Choice[int], formate: app_commands.Choice[int]):
    super().__init__(label="Finalizar",
                     style=discord.ButtonStyle.red, emoji="🏁", disabled=True)
    self.userCallCommand = userCallCommand
    self.embedMessageTeam = embedMessageTeam
    self.viewBtn = view
    self.onlineMode = onlineMode
    self.formate = formate

  async def callback(self, interaction: discord.Interaction):
    if (interaction.user == self.userCallCommand):
      self.viewBtn.finishBtn.disabled = True
      self.viewBtn.startBtn.disabled = True
      self.viewBtn.exitBtn.disabled = True
      self.viewBtn.sortearBtn.disabled = True

      # Pega os times do start
      blueTeam = self.viewBtn.startBtn.blueTeam
      redTeam = self.viewBtn.startBtn.redTeam

      await interaction.response.edit_message(
          embed=self.embedMessageTeam(
              blueTeam,
              redTeam,
              self.onlineMode,
              self.formate,
              started=True,
              finished=True
          ),
          view=self.viewBtn
      )
    else:
      await interaction.response.send_message(
          embed=discord.Embed(description="Somente o criador da personalizada pode executar esta ação.",
                              color=interaction.guild.me.color),
          ephemeral=True,
          delete_after=3
      )
