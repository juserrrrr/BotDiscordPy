"""
Serviço responsável por operações relacionadas aos jogadores em partidas personalizadas.
Lida com validação de jogadores, movimentação em canais de voz e gerenciamento de contas Timbas.
"""
import discord
from typing import List, Optional, Dict


class PlayerService:
    """Gerencia toda a lógica de negócio relacionada aos jogadores."""

    @staticmethod
    def validate_player_in_voice(user: discord.User) -> tuple[bool, Optional[str]]:
        """
        Valida se um jogador está em um canal de voz.

        Retorna:
            tuple: (is_valid, error_message)
        """
        if not user.voice:
            return False, "Você precisa estar em um canal de voz."
        return True, None

    @staticmethod
    def validate_player_not_in_list(user: discord.User, confirmed_players: List[discord.User]) -> tuple[bool, Optional[str]]:
        """
        Valida se um jogador ainda não está na lista de jogadores confirmados.

        Retorna:
            tuple: (is_valid, error_message)
        """
        if user in confirmed_players:
            return False, "Você já está na lista."
        return True, None

    @staticmethod
    def validate_match_not_full(confirmed_players: List[discord.User], max_players: int = 10) -> tuple[bool, Optional[str]]:
        """
        Valida se a partida ainda tem espaço para mais jogadores.

        Retorna:
            tuple: (is_valid, error_message)
        """
        if len(confirmed_players) >= max_players:
            return False, "A partida já está cheia."
        return True, None

    @staticmethod
    async def move_player_to_channel(player: discord.User, channel: discord.VoiceChannel) -> bool:
        """
        Move um jogador para um canal de voz específico.

        Retorna:
            bool: True se bem-sucedido, False caso contrário
        """
        try:
            if isinstance(player, discord.Member) and player.voice:
                await player.move_to(channel)
                return True
        except Exception:
            pass
        return False

    @staticmethod
    async def move_team_to_channel(team: List[discord.User], channel: discord.VoiceChannel):
        """Move todos os jogadores de um time para um canal de voz específico."""
        for user in team:
            await PlayerService.move_player_to_channel(user, channel)

    @staticmethod
    async def restore_players_to_original_channels(
        confirmed_players: List[discord.User],
        original_channels: Dict[int, discord.VoiceChannel]
    ):
        """
        Restaura todos os jogadores para seus canais de voz originais.

        Args:
            confirmed_players: Lista de todos os jogadores na partida
            original_channels: Dicionário mapeando IDs de jogadores para seus canais originais
        """
        for player in confirmed_players:
            if player.voice and player.id in original_channels:
                original_channel = original_channels[player.id]
                await PlayerService.move_player_to_channel(player, original_channel)

    @staticmethod
    def store_original_channel(user: discord.User, original_channels: Dict[int, discord.VoiceChannel]):
        """Armazena o canal de voz original de um jogador."""
        if user.voice and user.voice.channel:
            original_channels[user.id] = user.voice.channel

    @staticmethod
    def remove_original_channel(user_id: int, original_channels: Dict[int, discord.VoiceChannel]):
        """Remove o canal original de um jogador do armazenamento."""
        if user_id in original_channels:
            del original_channels[user_id]

    @staticmethod
    def extract_users_from_team(team: List) -> List[discord.User]:
        """
        Extrai objetos User de uma lista de time (lida com dict e objetos User).

        Args:
            team: Lista que pode conter dict com chave 'user' ou objetos User diretamente

        Retorna:
            Lista de objetos discord.User
        """
        return [p['user'] if isinstance(p, dict) else p for p in team]

    @staticmethod
    def find_player_in_teams(user: discord.User, blue_team: List, red_team: List) -> Optional[dict]:
        """
        Encontra os dados de um jogador em qualquer um dos times.

        Retorna:
            Dict com dados do jogador se encontrado, None caso contrário
        """
        for p in blue_team:
            if isinstance(p, dict) and p['user'] == user:
                return p

        for p in red_team:
            if isinstance(p, dict) and p['user'] == user:
                return p

        return None

    @staticmethod
    def get_player_team_channel(
        user: discord.User,
        blue_team: List,
        red_team: List,
        blue_channel: discord.VoiceChannel,
        red_channel: discord.VoiceChannel
    ) -> Optional[discord.VoiceChannel]:
        """
        Obtém o canal de voz de um jogador baseado em seu time.

        Retorna:
            Canal de voz se o jogador estiver em um time, None caso contrário
        """
        blue_players = PlayerService.extract_users_from_team(blue_team)
        red_players = PlayerService.extract_users_from_team(red_team)

        if user in blue_players:
            return blue_channel
        elif user in red_players:
            return red_channel

        return None
