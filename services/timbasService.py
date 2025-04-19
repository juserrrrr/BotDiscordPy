import requests
import os


class timbasService():
  def __init__(self):
    self.session = requests.session()
    self.token = os.getenv("TOKEN_TIMBAS_API")
    self.header = {'Authorization': f'Bearer {self.token}'}
    self.url = os.getenv("TIMBAS_API_URL")
    if not self.url:
      raise ValueError("TIMBAS_API_URL não configurada no arquivo .env")

  def getUserByDiscordId(self, discordId: str):
    url = f"{self.url}/users/discord/{discordId}"
    try:
      response = self.session.get(url, headers=self.header, timeout=1)
      return response
    except Exception as exp:
      return None

  def createPlayer(self, data: dict):
    url = f"{self.url}/users/player"
    response = self.session.post(url, headers=self.header, data=data)
    return response

  def getWelcomeByServerId(self, serverId: str):
    url = f"{self.url}/discordServer/welcomeMsg/{serverId}"
    response = self.session.get(url, headers=self.header)
    return response
