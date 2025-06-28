Este comando é responsável por criar e gerenciar partidas personalizadas de League of Legends.
Ele lida com a criação de canais de voz, gerenciamento de jogadores e o ciclo de vida da partida.

import discord
from discord import app_commands
from discord.ext import commands
import asyncio

from .utilsPerson.ui import CustomMatchView, ConfirmChannelCreationView
from .utilsPerson.helpers import generate_league_embed_text

class CriarPerson(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    async def manage_voice_channels(self, interaction: discord.Interaction):
        """Verifica e cria os canais de voz necessários para a partida."""
        guild = interaction.guild
        required_channels = {"| 🕘 | AGUARDANDO", "LADO [ |🔵| ]", "LADO [ |🔴| ]"}
        existing_channels = {channel.name for channel in guild.voice_channels}
        missing_channels = required_channels - existing_channels

        if not missing_channels:
            return True, {name: discord.utils.get(guild.voice_channels, name=name) for name in required_channels}

        view = ConfirmChannelCreationView()
        await interaction.response.send_message(
            "Canais de voz para a partida não encontrados. Deseja criá-los?",
            view=view,
            ephemeral=True
        )
        await view.wait()

        if view.result:
            await interaction.edit_original_response(content="Criando canais...", view=None)
            category = discord.utils.get(guild.categories, name="🆚 Personalizada")
            if not category:
                category = await guild.create_category("🆚 Personalizada")
            
            created_channels = {}
            for name in required_channels:
                channel = await guild.create_voice_channel(name, category=category)
                created_channels[name] = channel
            return True, created_channels
        else:
            await interaction.edit_original_response(content="Criação de canais cancelada.", view=None)
            return False, None

    @app_commands.command(name='criarperson', description="Cria uma partida personalizada de League of Legends.")
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
        match_format="Define como os times serão formados."
    )
    async def criar_personalizada(self, interaction: discord.Interaction, online_mode: app_commands.Choice[int], match_format: app_commands.Choice[int]):
        """Ponto de entrada para o comando de criação de partida."""
        if match_format.value == 2: # Balanceado
            await interaction.response.send_message(
                "O modo de jogo Balanceado ainda está em desenvolvimento.",
                ephemeral=True
            )
            return

        success, channels = await self.manage_voice_channels(interaction)
        if not success:
            return

        waiting_channel = channels["| 🕘 | AGUARDANDO"]
        blue_channel = channels["LADO [ |🔵| ]"]
        red_channel = channels["LADO [ |🔴| ]"]

        initial_embed_text = generate_league_embed_text([], match_format.name, online_mode.name)
        embed = discord.Embed(
            description=f"```\n{initial_embed_text}```",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Aguardando jogadores...")
        embed.set_image(url="attachment://timbasQueue.png")

        view = CustomMatchView(
            creator=interaction.user,
            waiting_channel=waiting_channel,
            blue_channel=blue_channel,
            red_channel=red_channel,
            online_mode=online_mode,
            match_format=match_format
        )

        await interaction.response.send_message(
            embed=embed,
            view=view,
            file=discord.File('./images/timbasQueue.png')
        )

async def setup(client):
    await client.add_cog(CriarPerson(client))