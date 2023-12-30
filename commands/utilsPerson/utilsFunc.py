import discord
from random import randint
from services.timbasService import timbasService
from services.lolService import lolService
from .confirmView import ConfirmView
import asyncio

def generateTextUsers(usersPersonList):
  string = ''
  tamanho = len(usersPersonList)
  for index, user in enumerate(usersPersonList):
    if index == (tamanho-1):
      string += f" {user.name}"
    else:
      string += f" {user.name} \n"
  return string


def drawTeam(confirmedPlayers):
  blueTeam = []
  redTeam = []
  while confirmedPlayers:
      value1 = randint(0, len(confirmedPlayers)-1)
      blueTeam.append(confirmedPlayers[value1])
      confirmedPlayers.pop(value1)
      value2 = randint(0, len(confirmedPlayers)-1)
      redTeam.append(confirmedPlayers[value2])
      confirmedPlayers.pop(value2)
  return (blueTeam, redTeam)

async def moveTeam(team, channel: discord.VoiceChannel):
  for user in team:
    await user.move_to(channel)

def splitUserTag(nameLeague):
  return nameLeague.split('#')

def checkUserIsRegistered(user:discord.User):
  timbas = timbasService()
  response = timbas.getUserByDiscordId(user.id)
  return response.status_code == 200

def checkUserIsLeagueId(data):
  fieldNameLeagueId = 'leagueId'  
  return fieldNameLeagueId in data

async def createUserOnTimbas(user:discord.User, leagueId):
  timbas = timbasService()
  response = timbas.createUser({
    'name': user.name,
    'discordId': user.id,
    'leagueId': leagueId,
  })
  return response


def checkUserLeagueExists(response):
  return response.status_code == 200


def getDataPlayerLeague(dataSummoner, dataRank):

  rankedSoloName = 'RANKED_SOLO_5x5'
  rankedFlexName = 'RANKED_FLEX_SR'
  
  rankedDadosSolo = None
  rankedDadosFlex = None

  for ranked in dataRank:
    if ranked.get('queueType') == rankedSoloName:
      rankedDadosSolo = ranked
    elif ranked.get('queueType') == rankedFlexName:
      rankedDadosFlex = ranked

  return {
    'name': dataSummoner.get('name'),
    'profileIconId': dataSummoner.get('profileIconId'),
    'level': dataSummoner.get('summonerLevel'),
    'tierSolo': (rankedDadosSolo or {}).get('tier', ''),
    'rankSolo': (rankedDadosSolo or {}).get('rank', 'Unranked'),
    'tierFlex': (rankedDadosFlex or {}).get('tier', ''),
    'rankFlex': (rankedDadosFlex or {}).get('rank', 'Unranked'),
  }

async def showUser(interaction: discord.Interaction, userName: str):
  apiLol = lolService()
  userSplit = splitUserTag(userName)
  responseAccount = apiLol.getAccount(userSplit[0],userSplit[1])
  if checkUserLeagueExists(responseAccount):
    responseSummoner = apiLol.getSummonerByPuuid(responseAccount.json().get('puuid'))
    responseRank = apiLol.getRankedStats(responseSummoner.json().get('id'))
    DataPlayer = getDataPlayerLeague(responseSummoner.json(), responseRank.json())
    viewConfirm = ConfirmView()
    #AJEITAR ESSE CÓDIGO DEPOIS
    await interaction.edit_original_response(
      content="",
      embed=discord.Embed(
        title = f"**{DataPlayer.get('name')}**, é você?",
        description = f"**Infomações sobre o jogador**",
        color = 0x00FF00
      ).add_field(
        name="Solo/Duo",
        value=f"**{DataPlayer.get('tierSolo')} {DataPlayer.get('rankSolo')}**"
      ).add_field(
        name="Flex",
        value=f"**{DataPlayer.get('tierFlex')} {DataPlayer.get('rankFlex')}**"
      ).add_field(
        name="Level",
        value=f"**{DataPlayer.get('level')}**"
      ).set_thumbnail(
        url = apiLol.getUrlProfileIcon(DataPlayer.get('profileIconId'))
      ),
      view=viewConfirm
    )
    #==============================
    await viewConfirm.wait()
    if viewConfirm.value:
      await createUserOnTimbas(interaction.user, responseSummoner.json().get('id'))
      await interaction.edit_original_response(
        content="",
        embed=discord.Embed(
          description = f"**Usuário registrado com sucesso.**",
          color = 0x00FF00
        ),
        view=None
      )
    else:
      await interaction.edit_original_response(
        content="",
        embed=discord.Embed(
          description = f"**Usuário não registrado.**",
          color = 0xFF0004
        ),
        view=None
      )
    await asyncio.sleep(2)
    await interaction.delete_original_response()
    return

  await interaction.edit_original_response(
    content="",
    embed=discord.Embed(
      description = f"**Usuário não encotrado, tente novamente.**",
      color = 0xFF0004
    )
  )





  