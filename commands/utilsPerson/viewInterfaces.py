from .selectInterfaces import createEssentialChannels
from .btnInterfaces import *
from base.BaseViews import BaseView
from discord import app_commands
import asyncio
import discord


class ViewActionConfirm(BaseView):
  def __init__(self, channels):
    super().__init__()
    self.future = asyncio.Future()
    self.add_item(createEssentialChannels(channels, self.future))


class ViewBtnInterface(BaseView):
  def __init__(
      self,
      userCallCommand: discord.User | discord.Member,
      channelWaiting: discord.VoiceChannel,
      channelBlue: discord.VoiceChannel,
      channelRed: discord.VoiceChannel,
      confirmedUsers: list,
      embedMessageConfirm,
      embedMessageTeam,
      onlineMode: app_commands.Choice[int],
      formate: app_commands.Choice[int]
  ):
    super().__init__()
    self.onlineMode = onlineMode
    self.formate = formate

    self.joinBtn = BtnJoinCustomMatch(
        channelWaiting, confirmedUsers, embedMessageConfirm, onlineMode, formate, self
    )
    self.exitBtn = BtnExitCustomMatch(
        channelWaiting, confirmedUsers, embedMessageConfirm, onlineMode, formate, self
    )
    self.amountBtn = BtnAmountCustomMatch()
    self.sortearBtn = BtnSortearCustomMatch(
        confirmedUsers, embedMessageTeam, self, onlineMode, formate
    )
    self.startBtn = BtnStartCustomMatch(
        userCallCommand, channelBlue, channelRed, confirmedUsers, embedMessageTeam, self, onlineMode, formate
    )
    self.finishBtn = BtnFinishCustomMatch(
        userCallCommand, embedMessageTeam, self, onlineMode, formate
    )
    self.switchSideBtn = BtnSwitchSideCustomMatch(
        channelBlue, channelRed, confirmedUsers, embedMessageTeam, self, onlineMode, formate
    )
    self.add_item(self.joinBtn)
    self.add_item(self.exitBtn)
    self.add_item(self.amountBtn)
    self.add_item(self.startBtn)
    self.add_item(self.finishBtn)
    if formate.value == 1:
      self.switchSideBtn.disabled = True
      self.add_item(self.switchSideBtn)
    if formate.value == 0:
      self.sortearBtn.disabled = True
      self.add_item(self.sortearBtn)
