import discord
from random import randint
from typing import List, Tuple

from services.timbasService import timbasService
from services.lolService import lolService


def generate_league_embed_text(blue_team: List[discord.User], red_team: List[discord.User], match_format: str, online_mode: str, winner: str = None) -> str:
    """Gera o texto formatado para o embed da partida de League of Legends."""
    half = 5

    format_str = f"Formato: {match_format}"
    online_mode_str = f"Modo: {online_mode}"
    map_name = "[League of Legends] - Summoner's Rift"

    blue_pad, red_pad = 18, 18
    if winner == "BLUE":
        blue_team_header = "TimeAzul 🏆"
        red_team_header = "TimeVermelho"
        blue_pad -= 2  # Compensa a largura do emoji
    elif winner == "RED":
        blue_team_header = "TimeAzul"
        red_team_header = "🏆 TimeVermelho"
        red_pad -= 2  # Compensa a largura do emoji
    else:
        blue_team_header = "TimeAzul"
        red_team_header = "TimeVermelho"

    lines = [
        f"{'   -----':<21}{'-*-':^3}{'-----   ':>21}",
        f"{'':<9}{'Partida personalizada ⚔️':^27}{'':>9}",
        f"{'':<3} {map_name:^39} {'':>3}",
        f"{format_str:<20}{'':^5}{online_mode_str:>20}",
        f"{blue_team_header:<{blue_pad}}{'< EQP >':^9}{red_team_header:>{red_pad}}",
        f"{'':<18}{'00     00':^9}{'':>18}",
        f"{'':<18}{'00:00':^9}{'':>18}",
    ]

    for i in range(half):
        blue_player = blue_team[i].name[:6] if i < len(blue_team) else "Vazio"
        red_player = red_team[i].name[:6] if i < len(red_team) else "Vazio"

        blue_str = f"{blue_player:<7}{'000':>3}{'00/00/00':>9}"
        red_str = f"{'00/00/00':<9}{'000':<3}{red_player:>7}"
        lines.append(f"{blue_str}{'<00K>':^7}{red_str}")

    lines.append(f"{'':<5}{'(No momento, apenas visualização)':^35}{'':>5}")
    return "\n".join(lines)


def draw_teams(players: List[discord.User]) -> Tuple[List[discord.User], List[discord.User]]:
    """Sorteia dois times a partir de uma lista de jogadores."""
    players_copy = players.copy()
    blue_team = []
    red_team = []
    while players_copy:
        blue_player = players_copy.pop(randint(0, len(players_copy) - 1))
        blue_team.append(blue_player)
        if players_copy:
            red_player = players_copy.pop(randint(0, len(players_copy) - 1))
            red_team.append(red_player)
    return blue_team, red_team


async def move_team_to_channel(team: List[discord.User], channel: discord.VoiceChannel):
    """Move todos os jogadores de um time para um canal de voz específico."""
    for user in team:
        if user.voice:
            await user.move_to(channel)


def clean_invalid_chars(text: str) -> str:
    """Remove caracteres inválidos e espaços em branco de uma string."""
    text = text.strip()
    text = text.replace('\u2066', '').replace('\u2069', '')
    return ''.join(c for c in text if c.isalnum() or c == '#')


def split_user_tag(name: str) -> List[str]:
    """Divide o nome de usuário e a tag."""
    cleaned_name = clean_invalid_chars(name)
    return cleaned_name.split('#')


def is_user_registered(response) -> bool:
    """Verifica se o usuário do Timbas tem uma conta do LoL associada."""
    return response.status_code == 200 and response.json().get('leaguePuuid') is not None


async def create_timbas_player(user: discord.User, league_data: dict):
    """Cria um novo jogador no serviço Timbas."""
    timbas = timbasService()
    payload = {
        'name': league_data.get('name'),
        'discordId': str(user.id),
        'leaguePuuid': str(league_data.get('puuid')),
    }
    return timbas.createPlayer(payload)


def get_player_data_from_league(summoner_data: dict, account_data: dict, rank_data: list) -> dict:
    """Extrai e formata os dados do jogador do LoL a partir das respostas da API."""
    solo_rank = next((r for r in rank_data if r.get('queueType') == 'RANKED_SOLO_5x5'), {})
    flex_rank = next((r for r in rank_data if r.get('queueType') == 'RANKED_FLEX_SR'), {})

    return {
        'name': account_data.get('gameName'),
        'profileIconId': summoner_data.get('profileIconId'),
        'puuid': account_data.get('puuid'),
        'level': summoner_data.get('summonerLevel'),
        'tierSolo': solo_rank.get('tier', 'Unranked'),
        'rankSolo': solo_rank.get('rank', ''),
        'tierFlex': flex_rank.get('tier', 'Unranked'),
        'rankFlex': flex_rank.get('rank', ''),
    }


def get_league_account_data(username: str):
    """Busca e retorna os dados de uma conta do League of Legends."""
    lol = lolService()
    name, tag = split_user_tag(username)
    
    account_response = lol.getAccount(name, tag)
    if account_response.status_code != 200:
        return None

    account_data = account_response.json()
    puuid = account_data.get('puuid')

    summoner_response = lol.getSummonerByPuuid(puuid)
    if summoner_response.status_code != 200:
        return None
    
    summoner_data = summoner_response.json()
    summoner_id = summoner_data.get('id')

    rank_response = lol.getRankedStats(summoner_id)
    rank_data = rank_response.json() if rank_response.status_code == 200 else []

    return get_player_data_from_league(summoner_data, account_data, rank_data)
