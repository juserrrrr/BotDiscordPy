import requests
import dotenv
import os

class ApiLol():
    def __init__(self):
      self.session = requests.session()
      self.token = os.getenv("TOKEN_LOL_API")
      self.header = {'X-Riot-Token':self.token}

    def suitingString(self,string:str):
      return string.lower().replace(" ","")

    def getSummonerName(self,name:str):
      name = self.suitingString(name)
      url = f"https://br1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{name}"
      response = self.session.get(url,headers=self.header)
      return response

    def getUrlProfileIcon(self,id:int):
      return f"http://ddragon.leagueoflegends.com/cdn/12.23.1/img/profileicon/{id}.png"

    def getRankedStats(self,idSumoner:int):
      url = f"https://br1.api.riotgames.com/lol/league/v4/entries/by-summoner/{idSumoner}"
      response = self.session.get(url,headers=self.header)
      return response

        
