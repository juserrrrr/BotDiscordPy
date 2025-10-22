import requests
import os


class lolService():
  def __init__(self):
    self.session = requests.session()
    self.token = os.getenv("TOKEN_LOL_API")
    self.header = {'X-Riot-Token': self.token}

  def getSummonerByPuuid(self, puuid: str):
    url = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    response = self.session.get(url, headers=self.header)
    return response

  def getAccount(self, gameName: str, tagline: str):
    url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagline}"
    response = self.session.get(url, headers=self.header)
    return response

  def getUrlProfileIcon(self, id: int):
    return f"http://ddragon.leagueoflegends.com/cdn/12.23.1/img/profileicon/{id}.png"

  def getRankedStats(self, idSumoner: int):
    url = f"https://br1.api.riotgames.com/lol/league/v4/entries/by-summoner/{idSumoner}"
    response = self.session.get(url, headers=self.header)
    return response

  def getLatestVersion(self):
    """Obtém a versão mais recente do Data Dragon."""
    url = "https://ddragon.leagueoflegends.com/api/versions.json"
    response = self.session.get(url)
    return response

  def getAllChampions(self, version: str = None):
    """Obtém todos os campeões do League of Legends via Data Dragon."""
    if not version:
      version_response = self.getLatestVersion()
      if version_response.status_code == 200:
        versions = version_response.json()
        version = versions[0]
      else:
        version = "15.20.1"  # Fallback para uma versão conhecida

    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/pt_BR/champion.json"
    response = self.session.get(url)
    return response

  def getChampionIcon(self, champion_name: str, version: str = None):
    """Retorna a URL do ícone de um campeão."""
    if not version:
      version_response = self.getLatestVersion()
      if version_response.status_code == 200:
        versions = version_response.json()
        version = versions[0]
      else:
        version = "15.20.1"

    return f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{champion_name}.png"
