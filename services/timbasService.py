import requests
import os
import logging

logger = logging.getLogger(__name__)


class timbasService():
  def __init__(self):
    self.session = requests.session()
    self.url = os.getenv("TIMBAS_API_URL")
    self.bot_secret = os.getenv("BOT_SECRET")
    self._token = None

    if not self.url:
      raise ValueError("TIMBAS_API_URL não configurada no arquivo .env")
    if not self.bot_secret:
      raise ValueError("BOT_SECRET não configurado no arquivo .env")

    try:
      self._authenticate()
    except Exception as e:
      logger.warning(f"Autenticação inicial falhou, bot continuará sem token: {e}")

  def _authenticate(self):
    try:
      response = self.session.post(
        f"{self.url}/auth/bot",
        json={"secret": self.bot_secret},
        timeout=10,
      )
      response.raise_for_status()
      self._token = response.json().get("acessToken")
      logger.info("Bot autenticado com sucesso na API Timbas.")
    except Exception as e:
      logger.error(f"Falha ao autenticar bot na API: {e}")
      raise

  def _headers(self):
    return {"Authorization": f"Bearer {self._token}"}

  def _request(self, method: str, path: str, **kwargs):
    url = f"{self.url}{path}"
    if not self._token:
      self._authenticate()
    response = self.session.request(method, url, headers=self._headers(), **kwargs)
    if response.status_code == 401:
      logger.info("Token expirado, renovando...")
      self._authenticate()
      response = self.session.request(method, url, headers=self._headers(), **kwargs)
    return response

  # ─── Usuários ─────────────────────────────────────────────────────────────

  def getUserByDiscordId(self, discordId: str):
    try:
      return self._request("GET", f"/users/discord/{discordId}", timeout=5)
    except Exception:
      return None

  def createPlayer(self, data: dict):
    return self._request("POST", "/users/player", data=data)

  # ─── Servidor ─────────────────────────────────────────────────────────────

  def getWelcomeByServerId(self, serverId: str):
    return self._request("GET", f"/discordServer/welcomeMsg/{serverId}")

  # ─── Partidas ─────────────────────────────────────────────────────────────

  def createMatch(self, data: dict):
    return self._request("POST", "/leagueMatch", json=data)

  def updateMatchWinner(self, match_id: int, data: dict):
    return self._request("PATCH", f"/leagueMatch/{match_id}", json=data)

  # ─── Ranking ──────────────────────────────────────────────────────────────

  def getRanking(self, serverId: str):
    return self._request("GET", f"/leaderboard/{serverId}")

  # ─── LoL / Riot API proxy ─────────────────────────────────────────────────

  def getPlayerLol(self, gameName: str, tagLine: str):
    return self._request("GET", f"/riot/player/{gameName}/{tagLine}")

  def verifyIconLol(self, puuid: str, iconId: int):
    return self._request("POST", "/riot/verify-icon", json={"puuid": puuid, "iconId": iconId})

  def getAllChampionsLol(self):
    return self._request("GET", "/riot/champions")

  def getProfileIconUrlLol(self, iconId: int):
    response = self._request("GET", f"/riot/profile-icon/{iconId}")
    return response.json().get("url") if response.status_code == 200 else f"http://ddragon.leagueoflegends.com/cdn/img/profileicon/{iconId}.png"

  def getChampionIconUrlLol(self, championName: str):
    response = self._request("GET", f"/riot/champion-icon/{championName}")
    return response.json().get("url") if response.status_code == 200 else None
