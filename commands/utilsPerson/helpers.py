import discord
import json
import os
from random import randint
from typing import List, Tuple

from services.timbasService import timbasService
from services.lolService import lolService


def load_champions_by_role():
    """Carrega o dicionário de campeões por posição do arquivo JSON."""
    json_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'champions_by_role.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback para um dicionário vazio se o arquivo não existir
        return {
            "Top": [],
            "Jungle": [],
            "Mid": [],
            "ADC": [],
            "Suporte": []
        }


# Carrega os campeões por posição do JSON
CHAMPIONS_BY_ROLE = load_champions_by_role()


def generate_league_embed_text(blue_team, red_team, match_format: str, online_mode: str, winner: str = None, show_details: bool = False) -> str:
    """
    Gera o texto formatado para o embed da partida de League of Legends.
    blue_team e red_team podem ser List[discord.User] ou List[dict] com {user, position, champion}
    """
    half = 5

    # Abreviar nomes longos para caber no layout
    format_abbrev = {
        'Aleatório': 'Aleatório',
        'Livre': 'Livre',
        'Balanceado': 'Balanceado',
        'Aleatório Completo': 'Aleat. Completo'
    }
    mode_abbrev = {
        'Online': 'Online',
        'Offline': 'Offline'
    }

    format_str = f"Fmt: {format_abbrev.get(match_format, match_format[:10])}"
    online_mode_str = f"Modo: {mode_abbrev.get(online_mode, online_mode[:8])}"
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
        f"{format_str:<22}{'':^1}{online_mode_str:>22}",
        f"{blue_team_header:<{blue_pad}}{'< EQP >':^9}{red_team_header:>{red_pad}}",
        f"{'':<18}{'00     00':^9}{'':>18}",
        f"{'':<18}{'00:00':^9}{'':>18}",
    ]

    for i in range(half):
        # Verifica se é dict (com posição e campeão) ou User simples
        if i < len(blue_team):
            if isinstance(blue_team[i], dict):
                blue_player = blue_team[i]['user'].name[:12]
                blue_position = blue_team[i].get('position', '')[:3] if show_details else ''
                blue_champion = blue_team[i].get('champion', '')[:10] if show_details else ''
            else:
                blue_player = blue_team[i].name[:12]
                blue_position = ''
                blue_champion = ''
        else:
            blue_player = "Vazio"
            blue_position = ''
            blue_champion = ''

        if i < len(red_team):
            if isinstance(red_team[i], dict):
                red_player = red_team[i]['user'].name[:12]
                red_position = red_team[i].get('position', '')[:3] if show_details else ''
                red_champion = red_team[i].get('champion', '')[:10] if show_details else ''
            else:
                red_player = red_team[i].name[:12]
                red_position = ''
                red_champion = ''
        else:
            red_player = "Vazio"
            red_position = ''
            red_champion = ''

        if show_details and (blue_position or blue_champion or red_position or red_champion):
            # Formato com posição e campeão - mais legível
            # Abreviações de posição
            pos_abbrev = {
                'Top': 'TOP',
                'Jungle': 'JG',
                'Mid': 'MID',
                'ADC': 'ADC',
                'Suporte': 'SUP'
            }
            blue_pos_short = pos_abbrev.get(blue_position, blue_position[:3].upper())
            red_pos_short = pos_abbrev.get(red_position, red_position[:3].upper())

            # Linha com jogador e posição
            blue_str = f"[{blue_pos_short}] {blue_player:<12}"
            red_str = f"{red_player:>12} [{red_pos_short}]"
            lines.append(f"{blue_str:<19}{' VS ':^7}{red_str:>19}")

            # Linha com campeão
            blue_champ_str = f"  → {blue_champion:<10}"
            red_champ_str = f"{red_champion:>10} ←"
            lines.append(f"{blue_champ_str:<19}{'':^7}{red_champ_str:>19}")
        else:
            # Formato simples - só nome com VS no meio
            blue_str = f"{blue_player:<12}"
            red_str = f"{red_player:>12}"
            lines.append(f"{blue_str:<19}{' VS ':^7}{red_str:>19}")

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
        if isinstance(user, discord.Member) and user.voice:
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
    """Verifica se o usuário do Timbas tem uma conta associada."""
    return response.status_code == 200


async def create_timbas_player(user: discord.User, league_data: dict = None):
    """Cria um novo jogador no serviço Timbas."""
    timbas = timbasService()
    payload = {
        'discordId': str(user.id),
        'name': user.name, 
    }
    if league_data:
        payload['name'] = league_data.get('name')
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


def draw_positions() -> List[str]:
    """Sorteia as 5 posições do League of Legends de forma aleatória."""
    positions = ["Top", "Jungle", "Mid", "ADC", "Suporte"]
    shuffled_positions = positions.copy()
    from random import shuffle
    shuffle(shuffled_positions)
    return shuffled_positions


def get_all_champions_list():
    """Obtém a lista de todos os campeões do League of Legends."""
    lol = lolService()
    response = lol.getAllChampions()

    if response.status_code == 200:
        data = response.json()
        champions = list(data['data'].keys())
        return champions
    return []


def draw_random_champions(num_champions: int = 10) -> List[str]:
    """Sorteia uma lista de campeões aleatórios."""
    champions = get_all_champions_list()

    if not champions:
        return []

    from random import sample
    num_to_draw = min(num_champions, len(champions))
    return sample(champions, num_to_draw)


def draw_champion_for_position(position: str, used_champions: set) -> str:
    """
    Sorteia um campeão específico para a posição, evitando campeões já usados.
    """
    from random import choice

    available_champions = [champ for champ in CHAMPIONS_BY_ROLE.get(position, []) if champ not in used_champions]

    if not available_champions:
        # Se todos os campeões da posição foram usados, busca em todas as posições
        all_champions = []
        for champs in CHAMPIONS_BY_ROLE.values():
            all_champions.extend(champs)
        available_champions = [champ for champ in all_champions if champ not in used_champions]

    if available_champions:
        return choice(available_champions)

    return "Random"


def draw_teams_with_positions_and_champions(players: List[discord.User]) -> Tuple[List[dict], List[dict]]:
    """
    Sorteia dois times com posições e campeões aleatórios específicos para cada posição.
    Retorna: (blue_team, red_team)
    Cada time é uma lista de dicionários com: {user, position, champion}
    Os jogadores são ordenados na ordem: Top → Jungle → Mid → ADC → Suporte
    """
    players_copy = players.copy()
    blue_team = []
    red_team = []

    # Sortear posições para ambos os times
    blue_positions = draw_positions()
    red_positions = draw_positions()

    # Conjunto para rastrear campeões já sorteados (para evitar duplicatas)
    used_champions = set()

    position_index = 0

    while players_copy:
        # Time Azul
        blue_player = players_copy.pop(randint(0, len(players_copy) - 1))
        blue_position = blue_positions[position_index] if position_index < len(blue_positions) else 'Fill'
        blue_champion = draw_champion_for_position(blue_position, used_champions)
        used_champions.add(blue_champion)

        blue_team.append({
            'user': blue_player,
            'position': blue_position,
            'champion': blue_champion
        })

        # Time Vermelho
        if players_copy:
            red_player = players_copy.pop(randint(0, len(players_copy) - 1))
            red_position = red_positions[position_index] if position_index < len(red_positions) else 'Fill'
            red_champion = draw_champion_for_position(red_position, used_champions)
            used_champions.add(red_champion)

            red_team.append({
                'user': red_player,
                'position': red_position,
                'champion': red_champion
            })

        position_index += 1

    # Ordenar os times pela ordem das posições: Top → Jungle → Mid → ADC → Suporte
    position_order = {"Top": 0, "Jungle": 1, "Mid": 2, "ADC": 3, "Suporte": 4}
    blue_team.sort(key=lambda player: position_order.get(player['position'], 999))
    red_team.sort(key=lambda player: position_order.get(player['position'], 999))

    return blue_team, red_team
