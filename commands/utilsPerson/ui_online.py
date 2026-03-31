"""
View de partida ONLINE - delega todo o estado para o backend via API.
O modo OFFLINE continua usando CustomMatchView (ui.py) com estado em memória.
"""
import discord
from discord import ui, app_commands
from typing import List, Optional
import asyncio
import logging
import os

from base.BaseViews import BaseView
from .helpers import generate_league_embed_text
from .services.player_service import PlayerService
from services.timbasService import timbasService

logger = logging.getLogger(__name__)

WEB_URL = os.getenv("WEB_URL", "http://localhost:3000")

MATCH_FORMAT_MAP = {0: "ALEATORIO", 1: "LIVRE", 3: "ALEATORIO_COMPLETO"}
FORMAT_NAME_MAP  = {0: "Aleatório", 1: "Livre", 3: "Aleatório Completo"}


class OnlineLobbyView(BaseView):
    """
    View para partidas ONLINE.
    Toda a lógica de estado (confirmados, times, sorteio) fica no backend.
    O Discord apenas envia ações e reflete o estado recebido via API.
    """

    def __init__(
        self,
        creator: discord.User,
        lobby_id: str,
        match_format: app_commands.Choice[int],
        waiting_channel: Optional[discord.VoiceChannel] = None,
        blue_channel: Optional[discord.VoiceChannel] = None,
        red_channel: Optional[discord.VoiceChannel] = None,
        debug: bool = False,
    ):
        super().__init__(timeout=None)
        self.creator = creator
        self.lobby_id = lobby_id
        self.match_format = match_format
        self.waiting_channel = waiting_channel
        self.blue_channel = blue_channel
        self.red_channel = red_channel
        self.debug = debug
        self.original_voice_channels = {}

        # Cache local apenas para mover jogadores no Discord (não é estado de jogo)
        self._discord_users: dict[str, discord.User] = {}

        self._started = False
        self._finished = False
        self.message: Optional[discord.Message] = None
        self._sse_task: Optional[asyncio.Task] = None

        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if not self._started:
            self.add_item(OnlineJoinButton(self))
            self.add_item(OnlineLeaveButton(self))
            self.add_item(OnlineDrawButton(self))
            self.add_item(OnlineStartButton(self))
        self.add_item(OnlineFinishButton(self))

    def start_sse_listener(self, message: discord.Message):
        """Start background SSE listener to keep embed in sync with backend state."""
        self.message = message
        self._sse_task = asyncio.create_task(self._listen_sse())

    async def _listen_sse(self):
        import aiohttp
        import json as _json
        url = f"{os.getenv('TIMBAS_API_URL')}/leagueMatch/{self.lobby_id}/events"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3600)) as resp:
                    async for line in resp.content:
                        decoded = line.decode('utf-8').strip()
                        if not decoded.startswith('data:'):
                            continue
                        try:
                            data = _json.loads(decoded[5:].strip())
                            event_type = data.get('type')
                            payload = data.get('payload', {})
                            if event_type in ('player_joined', 'player_left', 'teams_drawn', 'match_started', 'match_finished', 'state'):
                                await self._update_embed_direct(payload)
                            if event_type in ('match_finished', 'match_expired') or payload.get('status') in ('FINISHED', 'EXPIRED'):
                                break
                        except Exception as e:
                            logger.error(f"SSE parse error: {e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"SSE listener error for lobby {self.lobby_id}: {e}")

    async def _update_embed_direct(self, lobby: dict):
        """Update the Discord message embed directly (used by SSE listener)."""
        if not self.message:
            return
        embed = self._build_embed(lobby)
        self._started = lobby.get("status") == "STARTED"
        self._finished = lobby.get("status") in ("FINISHED", "EXPIRED")
        self.update_buttons()
        try:
            await self.message.edit(embed=embed, view=self)
        except Exception as e:
            logger.error(f"Failed to edit message from SSE: {e}")

    def _build_embed(self, lobby: dict) -> discord.Embed:
        """Build a Discord Embed from lobby data dict."""
        status = lobby.get("status", "WAITING")
        players = lobby.get("queuePlayers", lobby.get("players", []))
        teams = lobby.get("Teams", [])
        blue_team = []
        red_team = []
        for team in teams:
            if team.get("id") == lobby.get("teamBlueId"):
                blue_team = team.get("players", [])
            elif team.get("id") == lobby.get("teamRedId"):
                red_team = team.get("players", [])
        show_details = bool(blue_team or red_team)
        format_name = FORMAT_NAME_MAP.get(self.match_format.value, "Aleatório")

        def player_to_embed(p):
            u = p.get("user", p) if isinstance(p, dict) else {}
            pos = p.get("position") if isinstance(p, dict) else None
            class _U:
                name = (u.get("name", "?") if isinstance(u, dict) else str(u))[:12]
            if pos:
                return {"user": _U(), "position": pos}
            return _U()

        if blue_team or red_team:
            # Times já sorteados — mostra a divisão real
            blue_display = [player_to_embed(p) for p in blue_team]
            red_display  = [player_to_embed(p) for p in red_team]
        else:
            # Ainda na fila — distribui visualmente: 1-5 no azul, 6-10 no vermelho
            blue_display = [player_to_embed(p) for p in players[:5]]
            red_display  = [player_to_embed(p) for p in players[5:10]]

        winner_side = None
        if status == "FINISHED":
            winner_id = lobby.get("winnerId")
            blue_id = lobby.get("teamBlueId")
            winner_side = "BLUE" if winner_id == blue_id else "RED"

        text = generate_league_embed_text(
            blue_team=blue_display, red_team=red_display,
            match_format=format_name, online_mode="Online",
            show_details=show_details, winner=winner_side,
        )
        footer_map = {
            "WAITING":  f"Aguardando jogadores... {len(players)}/10",
            "STARTED":  "Partida em andamento! 🎮",
            "FINISHED": "Partida finalizada! 🏁",
            "EXPIRED":  "Lobby expirado.",
        }
        embed = discord.Embed(description=f"```{text}```", color=discord.Color.blue())
        embed.set_footer(text=footer_map.get(status, ""))
        embed.set_image(url="attachment://timbasQueueGif.gif")
        web_url = f"{WEB_URL}/dashboard/match/{self.lobby_id}"
        embed.add_field(name="\u200b", value=f"[Acompanhe pelo site]({web_url})", inline=False)
        return embed

    async def refresh_embed(self, interaction: discord.Interaction):
        """Busca estado atual do backend e atualiza o embed."""
        try:
            timbas = timbasService()
            response = await asyncio.to_thread(timbas.getLobby, self.lobby_id)
            if response and response.status_code == 200:
                lobby = response.json()
                if self.message is None:
                    self.message = interaction.message
                await self._update_embed_from_lobby(interaction, lobby)
        except Exception as e:
            logger.error(f"Erro ao atualizar embed do lobby: {e}")

    async def _update_embed_from_lobby(self, interaction: discord.Interaction, lobby: dict):
        """Monta e edita o embed com base nos dados do lobby vindos da API."""
        status = lobby.get("status", "WAITING")
        self._started = status == "STARTED"
        self._finished = status in ("FINISHED", "EXPIRED")
        self.update_buttons()
        embed = self._build_embed(lobby)
        try:
            await interaction.message.edit(embed=embed, view=self)
        except Exception:
            pass


# ─── Botões ──────────────────────────────────────────────────────────────────

class OnlineJoinButton(ui.Button):
    def __init__(self, lobby_view: OnlineLobbyView):
        super().__init__(label="Entrar", style=discord.ButtonStyle.green, emoji="✅", disabled=lobby_view._started or lobby_view._finished)
        self.lobby_view = lobby_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user

        is_valid, error_msg = PlayerService.validate_player_in_voice(user)
        if not is_valid:
            msg = await interaction.followup.send(error_msg, ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()
            return

        timbas = timbasService()
        # Tenta criar conta se não existir
        user_resp = await asyncio.to_thread(timbas.getUserByDiscordId, str(user.id))
        if not user_resp or user_resp.status_code != 200:
            create_resp = await asyncio.to_thread(timbas.createPlayer, {"discordId": str(user.id), "name": user.name})
            if not create_resp or create_resp.status_code != 201:
                msg = await interaction.followup.send("❌ Erro ao criar conta Timbas. Tente novamente.", ephemeral=True)
                await asyncio.sleep(5)
                await msg.delete()
                return

        avatar_hash = user.avatar.key if user.avatar else ""
        payload = {"discordId": str(user.id), "name": user.name, "avatar": avatar_hash}
        response = await asyncio.to_thread(timbas.joinLobby, self.lobby_view.lobby_id, payload)

        if response and response.status_code == 201:
            # Armazena user discord para mover de canal depois
            self.lobby_view._discord_users[str(user.id)] = user
            PlayerService.store_original_channel(user, self.lobby_view.original_voice_channels)
            await PlayerService.move_player_to_channel(user, self.lobby_view.waiting_channel)
            await self.lobby_view.refresh_embed(interaction)
            msg = await interaction.followup.send("✅ Você entrou na partida!", ephemeral=True)
            await asyncio.sleep(3)
            await msg.delete()
        else:
            error = response.json().get("message", "Erro desconhecido") if response else "Sem resposta da API"
            msg = await interaction.followup.send(f"❌ {error}", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()


class OnlineLeaveButton(ui.Button):
    def __init__(self, lobby_view: OnlineLobbyView):
        super().__init__(label="Sair", style=discord.ButtonStyle.red, emoji="🚪", disabled=lobby_view._started or lobby_view._finished)
        self.lobby_view = lobby_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user
        timbas = timbasService()
        response = await asyncio.to_thread(timbas.leaveLobby, self.lobby_view.lobby_id, str(user.id))

        if response and response.status_code in (200, 201):
            if user.voice and user.id in self.lobby_view.original_voice_channels:
                original_channel = self.lobby_view.original_voice_channels[user.id]
                await PlayerService.move_player_to_channel(user, original_channel)
                PlayerService.remove_original_channel(user.id, self.lobby_view.original_voice_channels)
            await self.lobby_view.refresh_embed(interaction)
            msg = await interaction.followup.send("🚪 Você saiu da partida.", ephemeral=True)
            await asyncio.sleep(3)
            await msg.delete()
        else:
            error = response.json().get("message", "Erro") if response else "Sem resposta da API"
            msg = await interaction.followup.send(f"❌ {error}", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()


class OnlineDrawButton(ui.Button):
    def __init__(self, lobby_view: OnlineLobbyView):
        disabled = lobby_view._started or lobby_view._finished or lobby_view.match_format.value == 1  # Livre não sorteia
        super().__init__(label="Sortear", style=discord.ButtonStyle.primary, emoji="🎲", disabled=disabled)
        self.lobby_view = lobby_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if interaction.user != self.lobby_view.creator:
            msg = await interaction.followup.send("❌ Apenas o criador pode sortear.", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()
            return

        timbas = timbasService()
        response = await asyncio.to_thread(timbas.drawLobby, self.lobby_view.lobby_id, str(self.lobby_view.creator.id))

        if response and response.status_code in (200, 201):
            await self.lobby_view.refresh_embed(interaction)
            msg = await interaction.followup.send("🎲 Times sorteados!", ephemeral=True)
            await asyncio.sleep(3)
            await msg.delete()
        else:
            error = response.json().get("message", "Erro") if response else "Sem resposta da API"
            msg = await interaction.followup.send(f"❌ {error}", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()


class OnlineStartButton(ui.Button):
    def __init__(self, lobby_view: OnlineLobbyView):
        super().__init__(label="Iniciar", style=discord.ButtonStyle.success, emoji="▶", disabled=lobby_view._started or lobby_view._finished)
        self.lobby_view = lobby_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if interaction.user != self.lobby_view.creator:
            msg = await interaction.followup.send("❌ Apenas o criador pode iniciar.", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()
            return

        timbas = timbasService()
        response = await asyncio.to_thread(timbas.startLobby, self.lobby_view.lobby_id, str(self.lobby_view.creator.id))

        if response and response.status_code in (200, 201):
            lobby = response.json()
            # Move jogadores para os canais dos times (lógica exclusiva do Discord)
            if not self.lobby_view.debug and self.lobby_view.blue_channel and self.lobby_view.red_channel:
                blue_team = lobby.get("blueTeam", [])
                red_team  = lobby.get("redTeam", [])
                for p in blue_team:
                    discord_user = self.lobby_view._discord_users.get(p.get("discordId"))
                    if discord_user:
                        await PlayerService.move_player_to_channel(discord_user, self.lobby_view.blue_channel)
                for p in red_team:
                    discord_user = self.lobby_view._discord_users.get(p.get("discordId"))
                    if discord_user:
                        await PlayerService.move_player_to_channel(discord_user, self.lobby_view.red_channel)

            await self.lobby_view.refresh_embed(interaction)
            msg = await interaction.followup.send("▶ Partida iniciada!", ephemeral=True)
            await asyncio.sleep(3)
            await msg.delete()
        else:
            error = response.json().get("message", "Erro") if response else "Sem resposta da API"
            msg = await interaction.followup.send(f"❌ {error}", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()


class OnlineFinishButton(ui.Button):
    def __init__(self, lobby_view: OnlineLobbyView):
        super().__init__(label="Finalizar", style=discord.ButtonStyle.danger, emoji="🏁", disabled=lobby_view._finished)
        self.lobby_view = lobby_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if interaction.user != self.lobby_view.creator:
            msg = await interaction.followup.send("❌ Apenas o criador pode finalizar.", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()
            return

        view = OnlineWinnerSelectView(self.lobby_view, interaction.message)
        msg = await interaction.followup.send("🏆 Quem venceu a partida?", view=view, ephemeral=True, wait=True)
        view.message = msg


class OnlineWinnerSelectView(BaseView):
    def __init__(self, lobby_view: OnlineLobbyView, original_message: discord.Message):
        super().__init__(timeout=120)
        self.lobby_view = lobby_view
        self.original_message = original_message
        self.message = None
        self.add_item(OnlineWinnerSelect(self))


class OnlineWinnerSelect(ui.Select):
    def __init__(self, winner_view: OnlineWinnerSelectView):
        self.winner_view = winner_view
        options = [
            discord.SelectOption(label="Time Azul", value="BLUE", emoji="🔵"),
            discord.SelectOption(label="Time Vermelho", value="RED", emoji="🔴"),
        ]
        super().__init__(placeholder="Selecione o time vencedor...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if interaction.user != self.winner_view.lobby_view.creator:
            await interaction.followup.send("❌ Apenas o criador pode selecionar o vencedor.", ephemeral=True)
            return

        winner = self.values[0]  # "BLUE" or "RED"
        timbas = timbasService()
        response = await asyncio.to_thread(
            timbas.finishLobby,
            self.winner_view.lobby_view.lobby_id,
            str(self.winner_view.lobby_view.creator.id),
            winner
        )

        if response and response.status_code in (200, 201):
            # Restaura canais de voz originais
            if not self.winner_view.lobby_view.debug:
                all_players = list(self.winner_view.lobby_view._discord_users.values())
                await PlayerService.restore_players_to_original_channels(
                    all_players,
                    self.winner_view.lobby_view.original_voice_channels
                )

            await self.winner_view.lobby_view.refresh_embed(interaction)
            self.winner_view.lobby_view._finished = True
            self.winner_view.lobby_view.update_buttons()

            try:
                await interaction.delete_original_response()
            except Exception:
                pass
        else:
            error = response.json().get("message", "Erro") if response else "Sem resposta da API"
            await interaction.followup.send(f"❌ {error}", ephemeral=True)
