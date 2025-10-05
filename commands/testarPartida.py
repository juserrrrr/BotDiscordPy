import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import string

from services.timbasService import timbasService

from .utilsPerson.ui import CustomMatchView
from .utilsPerson.helpers import generate_league_embed_text

# Mock classes for testing, similar to those in criarPersonalizada.py
class MockVoice:
    def __init__(self):
        self.channel = "mock_channel"

class MockUser:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.voice = MockVoice()

    async def move_to(self, channel):
        pass

class TestarPartida(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name='testarpartida', description="Cria uma partida personalizada de League of Legends para testes.")
    @app_commands.guild_only()
    @app_commands.rename(online_mode="modo", match_format="formato")
    @app_commands.choices(
        online_mode=[
            app_commands.Choice(name="Online", value=1),
            app_commands.Choice(name="Offline", value=0)
        ],
        match_format=[
            app_commands.Choice(name="Aleatório", value=0),
            app_commands.Choice(name="Livre", value=1),
            app_commands.Choice(name="Balanceado", value=2)
        ]
    )
    @app_commands.describe(
        online_mode="Define se a partida terá registro de estatísticas (Online) ou não (Offline).",
        match_format="Define como os times serão formados.",
        use_default_players="Usa os IDs de Discord pré-definidos para os jogadores (para testes).",
        debug="Ativa o modo de debug (apenas para o dono do servidor)."
    )
    async def testar_partida(
        self,
        interaction: discord.Interaction,
        online_mode: app_commands.Choice[int],
        match_format: app_commands.Choice[int],
        use_default_players: bool = False,
        debug: bool = False
    ):
        """Cria uma partida personalizada para testes com IDs de Discord específicos."""
        await interaction.response.defer(ephemeral=True)

        async def delete_message_after_delay(msg):
            await asyncio.sleep(5)
            await msg.delete()

        if debug and interaction.user.id != interaction.guild.owner_id:
            message = await interaction.followup.send("Você não tem permissão para usar o modo de debug.", ephemeral=True)
            asyncio.create_task(delete_message_after_delay(message))
            return

        if match_format.value == 2: # Balanceado
            message = await interaction.followup.send(
                "O modo de jogo Balanceado ainda está em desenvolvimento.",
                ephemeral=True
            )
            asyncio.create_task(delete_message_after_delay(message))
            return

        if not use_default_players:
            message = await interaction.followup.send("Para testar a partida, por favor, defina 'use_default_players' como True.", ephemeral=True)
            asyncio.create_task(delete_message_after_delay(message))
            return

        # Hardcoded Discord IDs provided by the user
        default_discord_ids = [
            "919276824578646068", "352240724693090305", "373887997826957312",
            "1089165750993948774", "209825857815052288", "343492133644140544",
            "191630723935895553", "214397364163706880", "430165932963266561",
            "635277051439611914"
        ]
        player_ids = default_discord_ids


        confirmed_players = []
        for i, p_id in enumerate(player_ids):
            try:
                user_obj = await self.client.fetch_user(int(p_id))
                confirmed_players.append(user_obj)
            except (discord.NotFound, ValueError):
                confirmed_players.append(MockUser(name=f"TestPlayer{i+1}", id=int(p_id)))

        if online_mode.value == 1:
            timbas = timbasService()

            # Gerar riotMatchId aleatório
            random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=9))
            riot_match_id = f"TB_{random_string}"

            payload = {
                "ServerDiscordId": str(interaction.guild.id),
                "riotMatchId": riot_match_id,
                "teamBlue": {
                    "players": [{ "discordId": str(p.id) } for p in confirmed_players[:5]]
                },
                "teamRed": {
                    "players": [{ "discordId": str(p.id) } for p in confirmed_players[5:]]
                }
            }
            response = timbas.createMatch(payload)

            if response.status_code == 201:
                message = await interaction.followup.send(f"Partida de teste criada com sucesso! riotMatchId: {riot_match_id}", ephemeral=True)
                asyncio.create_task(delete_message_after_delay(message))
            else:
                message = await interaction.followup.send(f"Erro ao criar partida de teste na API: {response.text}", ephemeral=True)
                asyncio.create_task(delete_message_after_delay(message))
        else:
            message = await interaction.followup.send("Modo Offline selecionado. Nenhuma chamada à API de criação de partida foi feita.", ephemeral=True)
            asyncio.create_task(delete_message_after_delay(message))

async def setup(client):
    await client.add_cog(TestarPartida(client))