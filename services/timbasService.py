
import requests
import os

class timbasService():
  def __init__(self):
    self.session = requests.session()
    self.token = os.getenv("TOKEN_TIMBAS_API")
    self.header = {'Authorization':f'Bearer {self.token}'}
    self.url = "http://localhost:3000"

  def getUserByDiscordId(self,discordId:str):
    url = f"{self.url}/users/discord/{discordId}"
    try:
      response = self.session.get(url,headers=self.header, timeout=1)
      return response
    except Exception as exp:
      return None

  def createUser(self, data:dict):
    url = f"{self.url}/users"
    response = self.session.post(url, headers=self.header, data=data)
    return response
    