import requests
import dotenv
import os

class ApiLol():
    def __init__(self):
      self.session = requests.session()
      self.token = os.getenv("TOKEN_LOL_API")
      self.header = {'X-Riot-Token':self.token}

    def getSummonerByPuuid(self,puuid:str):
      url = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
      response = self.session.get(url,headers=self.header)
      return response

    def getAccount(self,gameName:str, tagline:str):
      url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{gameName}/{tagline}"
      response = self.session.get(url,headers=self.header)
      return response
    

    def getUrlProfileIcon(self,id:int):
      return f"http://ddragon.leagueoflegends.com/cdn/12.23.1/img/profileicon/{id}.png"

    def getRankedStats(self,idSumoner:int):
      url = f"https://br1.api.riotgames.com/lol/league/v4/entries/by-summoner/{idSumoner}"
      response = self.session.get(url,headers=self.header)
      return response

        
