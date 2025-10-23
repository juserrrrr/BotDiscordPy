"""
Serviço responsável por operações relacionadas às partidas.
Lida com validação de partidas, integração com API e gerenciamento de estado da partida.
"""
import discord
import random
import string
from typing import List, Tuple, Optional, Dict
from discord import app_commands

from services.timbasService import timbasService
from ..helpers import draw_teams, draw_teams_with_positions_and_champions


class MatchService:
    """Gerencia toda a lógica de negócio relacionada às partidas."""

    @staticmethod
    def validate_teams_drawn(
        match_format_value: int,
        blue_team: List,
        red_team: List
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida se os times precisam ser sorteados e se já foram sorteados.

        Args:
            match_format_value: Valor do formato da partida (0=Aleatório, 1=Livre, 3=Aleatório Completo)
            blue_team: Lista do time azul
            red_team: Lista do time vermelho

        Retorna:
            tuple: (is_valid, error_message)
        """
        # Modos aleatórios (0 e 3) precisam sortear antes
        if match_format_value in [0, 3] and not (blue_team and red_team):
            return False, "Sorteie os times primeiro."
        return True, None

    @staticmethod
    def validate_ready_players(
        match_format_value: int,
        ready_players: List[discord.User],
        required_ready: int = 6
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida se jogadores suficientes estão prontos (para modo Aleatório Completo).

        Args:
            match_format_value: Valor do formato da partida
            ready_players: Lista de jogadores prontos
            required_ready: Número mínimo de jogadores prontos requerido

        Retorna:
            tuple: (is_valid, error_message)
        """
        if match_format_value == 3:  # Aleatório Completo
            ready_count = len(ready_players)
            if ready_count < required_ready:
                return False, f"Aguarde pelo menos 6 jogadores estarem prontos para iniciar. ({ready_count}/{required_ready})"
        return True, None

    @staticmethod
    def validate_match_can_start(confirmed_players: List[discord.User]) -> Tuple[bool, Optional[str]]:
        """
        Valida se uma partida tem jogadores suficientes para iniciar.

        Retorna:
            tuple: (is_valid, error_message)
        """
        if len(confirmed_players) < 10:
            return False, "É necessário ter 10 jogadores para iniciar a partida."
        return True, None

    @staticmethod
    def perform_draw(
        match_format_value: int,
        confirmed_players: List[discord.User]
    ) -> Tuple[List, List, bool]:
        """
        Realiza o sorteio de times baseado no formato da partida.

        Args:
            match_format_value: Valor do formato da partida
            confirmed_players: Lista de jogadores confirmados

        Retorna:
            tuple: (blue_team, red_team, show_details)
        """
        if match_format_value == 3:  # Aleatório Completo
            blue_team, red_team = draw_teams_with_positions_and_champions(confirmed_players)
            return blue_team, red_team, True
        else:  # Aleatório normal
            blue_team, red_team = draw_teams(confirmed_players)
            return blue_team, red_team, False

    @staticmethod
    def prepare_free_mode_teams(confirmed_players: List[discord.User]) -> Tuple[List, List]:
        """
        Prepara times para o modo Livre (divide jogadores ao meio).

        Retorna:
            tuple: (blue_team, red_team)
        """
        half = len(confirmed_players) // 2
        blue_team = confirmed_players[:half]
        red_team = confirmed_players[half:]
        return blue_team, red_team

    @staticmethod
    def build_player_payload(player_data) -> Dict:
        """
        Constrói o payload de dados do jogador para envio à API.

        Args:
            player_data: Pode ser um dict (com user e position) ou um objeto User

        Retorna:
            Dicionário com dados do jogador para API
        """
        if isinstance(player_data, dict):
            # Modo Aleatório Completo - inclui posição
            return {
                "discordId": str(player_data['user'].id),
                "position": player_data.get('position')
            }
        else:
            # Outros modos - apenas discordId
            return {
                "discordId": str(player_data.id)
            }

    @staticmethod
    def build_match_payload(
        guild_id: int,
        match_type: int,
        blue_team: List,
        red_team: List
    ) -> Dict:
        """
        Constrói o payload completo da partida para envio à API.

        Args:
            guild_id: ID do servidor Discord
            match_type: Valor do formato da partida
            blue_team: Lista do time azul
            red_team: Lista do time vermelho

        Retorna:
            Dicionário com dados completos da partida para API
        """
        # Gera ID aleatório da partida riot
        random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=9))
        riot_match_id = f"TB_{random_string}"

        return {
            "ServerDiscordId": str(guild_id),
            "riotMatchId": riot_match_id,
            "matchType": match_type,
            "teamBlue": {
                "players": [MatchService.build_player_payload(p) for p in blue_team]
            },
            "teamRed": {
                "players": [MatchService.build_player_payload(p) for p in red_team]
            }
        }

    @staticmethod
    async def create_match_in_api(
        guild_id: int,
        match_type: int,
        blue_team: List,
        red_team: List
    ) -> Tuple[bool, Optional[str], Optional[int], Optional[int], Optional[int]]:
        """
        Cria uma partida na API Timbas.

        Retorna:
            tuple: (success, error_message, match_id, blue_team_id, red_team_id)
        """
        timbas = timbasService()
        payload = MatchService.build_match_payload(guild_id, match_type, blue_team, red_team)

        response = timbas.createMatch(payload)

        if response.status_code == 201:
            match_data = response.json()
            match_id = match_data.get('id')
            blue_team_id = match_data.get('teamBlueId')
            red_team_id = match_data.get('teamRedId')

            if not match_id or not blue_team_id or not red_team_id:
                return False, "Erro: A resposta da API não continha os IDs necessários.", None, None, None

            return True, None, match_id, blue_team_id, red_team_id
        else:
            return False, f"Erro ao criar a partida na API: {response.text}", None, None, None

    @staticmethod
    async def update_match_winner(match_id: int, winner_team_id: int) -> Tuple[bool, Optional[str]]:
        """
        Atualiza o vencedor da partida na API Timbas.

        Retorna:
            tuple: (success, error_message)
        """
        timbas = timbasService()
        payload = {"winnerId": winner_team_id}
        response = timbas.updateMatchWinner(match_id, payload)

        if response.status_code == 200:
            return True, None
        else:
            return False, f"Erro ao finalizar a partida: {response.text}"

    @staticmethod
    def get_winner_side(winner_team_id: int, blue_team_id: int, red_team_id: int) -> str:
        """
        Determina qual lado venceu baseado nos IDs dos times.

        Retorna:
            'BLUE' ou 'RED'
        """
        return 'BLUE' if winner_team_id == blue_team_id else 'RED'

    @staticmethod
    def get_winner_label(winner_side: str) -> str:
        """
        Obtém um rótulo legível do vencedor.

        Retorna:
            'Azul' ou 'Vermelho'
        """
        return "Azul" if winner_side == 'BLUE' else "Vermelho"
