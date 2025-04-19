import discord
from random import randint
from services.timbasService import timbasService


def generateTextUsers(usersPersonList: list):
  string = ''
  tamanho = len(usersPersonList)
  for index, user in enumerate(usersPersonList):
    if index == (tamanho-1):
      string += f" {user.name}"
    else:
      string += f" {user.name} \n"
  return string


def generateTextUsersLeague(usersPersonList: list, formate, onlineMode):
  # 55 Carecteres do emebed
  half = 5
  blueTeam = usersPersonList[:half]
  redTeam = usersPersonList[half:]
  formateString = f"Formato: {'Aleatório' if formate.value == 0 else 'Livre'}"
  onlineModeString = f"Modo: {'Online' if onlineMode.value == 1 else 'Offline'}"
  mapName = "[League of Legends] - Summoner's rift"
  endString = ""
  endString += f"{'--------------------------':<26}{'-*-':^3}{'--------------------------':>26}\n"
  endString += f"{'':<13}{'Partida personalizada ⚔️':^27}{'':>13}\n"
  endString += f"{'':<8} {mapName:^39} {'':>8}\n"
  endString += f"{formateString:<23}{'':^9}{onlineModeString:>23}\n"
  endString += f"{'TimeAzul':<23}{'< EQP >':^9}{'TimeVermelho':>23}\n"
  endString += f"{'':<23}{'00     00':^9}{'':>23}\n"
  endString += f"{'':<23}{'00:00':^9}{'':>23}\n"

  for i in range(half):
    # 25 por lado
    blueString = f"{blueTeam[i].name[:11]:<12}{'000':>3}{'00/00/00':>9}" if len(
        blueTeam) > i else f"{'Vazio':<24}"
    redString = f"{'00/00/00':<9}{'000':<3}{redTeam[i].name[:11]:>12}" if len(
        redTeam) > i else f"{'Vazio':>24}"
    endString += f"{blueString}{'<00K>':^7}{redString}\n"
  return endString if len(endString) > 0 else "Nenhum jogador confirmado."


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
  fieldNameLeagueId = 'leaguePuuid'
  return fieldNameLeagueId in data


async def createUserOnTimbas(user: discord.User, userLeague):
  timbas = timbasService()
  response = timbas.createPlayer({
      'name': userLeague.get('name'),
      'discordId': str(user.id),
      'leaguePuuid': str(userLeague.get('puuid')),
  })
  return response


def checkUserLeagueExists(response):
  return response.status_code == 200


def getDataPlayerLeague(dataSummoner, dataAccount, dataRank):

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
      'name': dataAccount.get('gameName'),
      'profileIconId': dataSummoner.get('profileIconId'),
      'puuid': dataAccount.get('puuid'),
      'level': dataSummoner.get('summonerLevel'),
      'tierSolo': (rankedDadosSolo or {}).get('tier', ''),
      'rankSolo': (rankedDadosSolo or {}).get('rank', 'Unranked'),
      'tierFlex': (rankedDadosFlex or {}).get('tier', ''),
      'rankFlex': (rankedDadosFlex or {}).get('rank', 'Unranked'),
  }


def checkAndGetDataPlayerLeague(lolService, userName):
  userSplit = splitUserTag(userName)
  responseAccount = lolService.getAccount(userSplit[0], userSplit[1])
  if checkUserLeagueExists(responseAccount):
    responseSummoner = lolService.getSummonerByPuuid(
        responseAccount.json().get('puuid'))
    responseRank = lolService.getRankedStats(
        responseSummoner.json().get('id'))
    return getDataPlayerLeague(responseSummoner.json(), responseAccount.json(), responseRank.json())
  return None
