import discord
from discord import ui
from .utilsFunc import *
from .inputInterfaces import *


class BtnJoinCustomMatch(ui.Button):
    def __init__(self,channelWaiting: discord.VoiceChannel , confirmedUsers: list, embedMessage, view: ui.View):
      super().__init__(label="Entrar", style=discord.ButtonStyle.green, emoji='✅')
      self.channelWaiting = channelWaiting
      self.confirmedUsers = confirmedUsers
      self.embedMessage = embedMessage
      self.viewBtn = view

    async def requestLeagueName(self, interaction: discord.Interaction):
      modal = ModalLeagueName()
      await interaction.response.send_modal(modal)
      await modal.wait()

    async def callback(self, interaction: discord.Interaction):
      user = await interaction.user
      
      if(checkUserIsRegistered(user) == False):
        await self.requestLeagueName(interaction)
      if (user.voice == None):
        await interaction.response.send_message(
          embed=discord.Embed(description="Você não esta em um canal de voz.",
                              color=interaction.guild.me.color),
          ephemeral=True,
          delete_after=3
        )

      elif not user in self.confirmedUsers:
        await user.move_to(self.channelWaiting)
        self.confirmedUsers.append(user)
        self.viewBtn.amountBtn.label = f"{len(self.confirmedUsers)}/10"
        if len(self.confirmedUsers) == 10:
            self.viewBtn.joinBtn.disabled = True
            self.viewBtn.startBtn.disabled = False
        if (interaction.response.is_done()):
          await interaction.edit_original_response(
            embed=self.embedMessage(generateTextUsers(self.confirmedUsers)),
            view=self.viewBtn
        ) 
        else:
          await interaction.response.edit_message(
            embed=self.embedMessage(generateTextUsers(self.confirmedUsers)),
            view=self.viewBtn
          )
      else:
        await interaction.response.send_message(
          embed=discord.Embed(description="Você já esta confirmado.",
                              color=interaction.guild.me.color),
          ephemeral=True,
          delete_after=3
        )

class BtnExitCustomMatch(ui.Button):
    def __init__(self, channelHome: discord.VoiceChannel, confirmedUsers: list, embedMessage, view:ui.View):
        super().__init__(label="Sair", style=discord.ButtonStyle.red, emoji='🚪')
        self.channelHome = channelHome
        self.confirmedUsers = confirmedUsers
        self.embedMessage = embedMessage
        self.viewBtn = view

    async def callback(self, interaction: discord.Interaction):
      user = interaction.user
      if user in self.confirmedUsers:
        if(user.voice != None):
          await user.move_to(self.channelHome)
        self.confirmedUsers.remove(user)
        self.viewBtn.amountBtn.label = f"{len(self.confirmedUsers)}/10"
        if len(self.confirmedUsers) < 10:
            self.viewBtn.joinBtn.disabled = False
            self.viewBtn.startBtn.disabled = True
        await interaction.response.edit_message(embed=self.embedMessage(generateTextUsers(self.confirmedUsers)), view=self.viewBtn)
      else:
        await interaction.response.send_message(embed=discord.Embed(description="Você não está confirmado.", color=interaction.guild.me.color), ephemeral=True, delete_after=3)

class BtnAmountCustomMatch(ui.Button):
    def __init__(self):
        super().__init__(label=f"0/10", style=discord.ButtonStyle.grey, emoji="🧑🏻‍💻",disabled=True)

    async def callback(self, interaction: discord.Interaction):
      return

class BtnStartCustomMatch(ui.Button):
    def __init__(self,userCallCommand:discord.User ,channelBlue: discord.VoiceChannel, channelRed: discord.VoiceChannel, confirmedUsers: list, embedMessageTeam, view:ui.View):
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
        textBlueTeam = generateTextUsers(blueTeam)
        textRedTeam = generateTextUsers(redTeam)
        await interaction.response.edit_message(
          embed=self.embedMessageTeam(textBlueTeam, textRedTeam), 
          view=self.viewBtn
        )
        await moveTeam(blueTeam, self.channelBlue)
        await moveTeam(redTeam, self.channelRed)
      else:
        await interaction.response.send_message(embed=discord.Embed(description="Somente o criador da personalizada pode executar esta ação.", color=interaction.guild.me.color), ephemeral=True, delete_after=3)


