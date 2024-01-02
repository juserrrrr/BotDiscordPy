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

def checkUserIsRegistered(response):
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

def checkAndGetDataPlayerLeague(lolService, userName):
  userSplit = splitUserTag(userName)
  responseAccount = lolService.getAccount(userSplit[0],userSplit[1])
  if checkUserLeagueExists(responseAccount):
    responseSummoner = lolService.getSummonerByPuuid(responseAccount.json().get('puuid'))
    responseRank = lolService.getRankedStats(responseSummoner.json().get('id'))
    return getDataPlayerLeague(responseSummoner.json(), responseRank.json())
  return None





  