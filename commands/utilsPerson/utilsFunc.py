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
  # 45 Carecteres do emebed
  half = 5
  blueTeam = usersPersonList[:half]
  redTeam = usersPersonList[half:]
  formateString = f"Formato: {'Aleatório' if formate.value == 0 else 'Livre'}"
  onlineModeString = f"Modo: {'Online' if onlineMode.value == 1 else 'Offline'}"
  mapName = "[League of Legends] - Summoner's rift"
  endString = ""
  endString += f"{'   -----':<21}{'-*-':^3}{'-----   ':>21}\n"
  endString += f"{'':<9}{'Partida personalizada ⚔️':^27}{'':>9}\n"
  endString += f"{'':<3} {mapName:^39} {'':>3}\n"
  endString += f"{formateString:<20}{'':^5}{onlineModeString:>20}\n"
  endString += f"{'TimeAzul':<18}{'< EQP >':^9}{'TimeVermelho':>18}\n"
  endString += f"{'':<18}{'00     00':^9}{'':>18}\n"
  endString += f"{'':<18}{'00:00':^9}{'':>18}\n"

  for i in range(half):
    # 25 por lado
    blueString = f"{blueTeam[i].name[:6]:<7}{'000':>3}{'00/00/00':>9}" if len(
        blueTeam) > i else f"{'Vazio':<19}"
    redString = f"{'00/00/00':<9}{'000':<3}{redTeam[i].name[:6]:>7}" if len(
        redTeam) > i else f"{'Vazio':>19}"
    endString += f"{blueString}{'<00K>':^7}{redString}\n"
  endString += f"{'':<5}{'(No momento apenas visualização)':^35}{'':>5}\n"
  return endString


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


def cleanInvalidCharacters(text: str) -> str:
  # Remove espaços em branco no início e fim
  text = text.strip()
  # Remove caracteres Unicode invisíveis específicos
  text = text.replace('\u2066', '').replace('\u2069', '')
  # Remove caracteres especiais, mantendo apenas letras, números e #
  return ''.join(c for c in text if c.isalnum() or c == '#')


def splitUserTag(nameLeague):
  cleanedName = cleanInvalidCharacters(nameLeague)
  return cleanedName.split('#')


def checkUserIsRegistered(response):
  return response.status_code == 200 and response.json().get('leaguePuuid') is not None


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


# Trabalhar no balanceamento dos times com o MMR (Futuro)
def calculateMmrLol(rank: str) -> int:
  #Converte um rank do League of Legends em um valor MMR numérico
  rank_tiers = {
      'IRON': 0,
      'BRONZE': 400,
      'SILVER': 800,
      'GOLD': 1200,
      'PLATINUM': 1600,
      'EMERALD': 2000,
      'DIAMOND': 2400,
      'MASTER': 2800,
      'GRANDMASTER': 3200,
      'CHALLENGER': 3600
  }

  rank_divisions = {
      'IV': 0,
      'III': 100,
      'II': 200,
      'I': 300
  }

  # Separa o rank em tier e divisão
  tier = rank.split()[0].upper()
  division = rank.split()[1] if len(rank.split()) > 1 else 'IV'

  # Calcula o MMR base
  mmr = rank_tiers.get(tier, 0)

  # Adiciona o valor da divisão
  mmr += rank_divisions.get(division, 0)

  return mmr


def balanceTeamsLol(users: list) -> tuple:
  # Balanceia os times do League of Legends baseado no MMR dos jogadores
  if len(users) != 10:
    return None, None

  # Calcula o MMR de cada jogador
  users_with_mmr = []
  for user in users:
    # Vou precisar buscar os dados do usuário na API do lol e pegar o rank do usuário

    # Só estou assuimindo que o rank tá armazenado em user.rank
    mmr = calculateMmrLol(user.rank) if hasattr(user, 'rank') else 0
    users_with_mmr.append((user, mmr))

  # Ordena os jogadores por MMR
  users_with_mmr.sort(key=lambda x: x[1], reverse=True)

  # Inicializa os times
  team1 = []
  team2 = []
  team1_mmr = 0
  team2_mmr = 0

  # Distribui os jogadores alternadamente entre os times
  for i, (user, mmr) in enumerate(users_with_mmr):
    if i % 2 == 0:
      team1.append(user)
      team1_mmr += mmr
    else:
      team2.append(user)
      team2_mmr += mmr

  # Se a diferença de MMR for muito grande, tenta rebalancear
  while abs(team1_mmr - team2_mmr) > 200 and len(team1) > 0 and len(team2) > 0:
    # Encontra o jogador com MMR mais próximo da diferença
    best_swap = None
    best_diff = float('inf')

    for i, (user1, mmr1) in enumerate(users_with_mmr):
      if user1 in team1:
        for j, (user2, mmr2) in enumerate(users_with_mmr):
          if user2 in team2:
            new_diff = abs((team1_mmr - mmr1 + mmr2) -
                           (team2_mmr - mmr2 + mmr1))
            if new_diff < best_diff:
              best_diff = new_diff
              best_swap = (i, j)

    if best_swap is not None:
      i, j = best_swap
      user1, mmr1 = users_with_mmr[i]
      user2, mmr2 = users_with_mmr[j]

      # Faz a troca
      team1.remove(user1)
      team2.remove(user2)
      team1.append(user2)
      team2.append(user1)

      # Atualiza os MMRs
      team1_mmr = team1_mmr - mmr1 + mmr2
      team2_mmr = team2_mmr - mmr2 + mmr1
    else:
      break

  return team1, team2
