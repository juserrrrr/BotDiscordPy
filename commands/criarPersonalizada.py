import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os

from .utilsPerson.ui import CustomMatchView, ConfirmChannelCreationView
from .utilsPerson.ui_online import OnlineLobbyView
from .utilsPerson.helpers import generate_league_embed_text
from services.timbasService import timbasService

WEB_URL = os.getenv("WEB_URL", "http://localhost:3000")

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

class CriarPerson(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    async def manage_channels(self, interaction: discord.Interaction):
        """Verifica e cria os canais de voz e texto necessários para a partida."""
        guild = interaction.guild
        required_voice_channels = {"| 🕘 | AGUARDANDO", "LADO [ |🔵| ]", "LADO [ |🔴| ]"}
        required_text_channel = "custom_game"

        existing_voice_channels = {channel.name for channel in guild.voice_channels}
        existing_text_channel = discord.utils.get(guild.text_channels, name=required_text_channel)

        missing_voice_channels = required_voice_channels - existing_voice_channels
        missing_text_channel = existing_text_channel is None

        # Se tudo já existe, retorna os canais
        if not missing_voice_channels and not missing_text_channel:
            voice_channels = {name: discord.utils.get(guild.voice_channels, name=name) for name in required_voice_channels}
            # Não precisa responder aqui, apenas retornar
            return True, voice_channels, existing_text_channel

        # Pergunta se deseja criar os canais faltantes
        view = ConfirmChannelCreationView()
        await interaction.response.send_message(
            "Canais para a partida não encontrados. Deseja criá-los?",
            view=view,
            ephemeral=True
        )
        await view.wait()

        if view.result:
            await interaction.edit_original_response(content="Criando canais...", view=None)

            # Buscar a categoria (pode ter variações no nome)
            category = None
            for cat in guild.categories:
                if "personalizada" in cat.name.lower():
                    category = cat
                    break

            if not category:
                category = await guild.create_category("🆚 Personalizada")

            # Criar canais de voz
            created_voice_channels = {}
            for name in required_voice_channels:
                # Verificar se o canal já existe e se está na categoria correta
                existing_channel = discord.utils.get(guild.voice_channels, name=name)
                if existing_channel and existing_channel.category == category:
                    created_voice_channels[name] = existing_channel
                elif name in missing_voice_channels:
                    channel = await guild.create_voice_channel(name, category=category)
                    created_voice_channels[name] = channel
                else:
                    created_voice_channels[name] = existing_channel

            # Criar canal de texto se não existir
            if missing_text_channel:
                # Configurar permissões: apenas o bot pode enviar mensagens
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(send_messages=False, read_messages=True),
                    guild.me: discord.PermissionOverwrite(send_messages=True, read_messages=True)
                }
                text_channel = await guild.create_text_channel(
                    required_text_channel,
                    category=category,
                    overwrites=overwrites,
                    topic="📋 Canal exclusivo para exibição de partidas personalizadas"
                )
            else:
                text_channel = existing_text_channel

            # Apaga a mensagem "Criando canais..." após 5 segundos
            await interaction.edit_original_response(content="Canais criados com sucesso!", view=None)
            # Agenda a deleção da mensagem
            import asyncio
            await asyncio.sleep(5)
            try:
                await interaction.delete_original_response()
            except:
                pass  # Ignora se a mensagem já foi deletada

            return True, created_voice_channels, text_channel
        else:
            await interaction.edit_original_response(content="Criação de canais cancelada.", view=None)
            return False, None, None

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
            app_commands.Choice(name="Balanceado", value=2),
            app_commands.Choice(name="Aleatório Completo", value=3)
        ]
    )
    @app_commands.describe(
        online_mode="Define se a partida terá registro de estatísticas (Online) ou não (Offline).",
        match_format="Define como os times serão formados. 'Aleatório Completo' sorteia jogadores + posições.",
        debug="Ativa o modo de debug com 10 jogadores falsos (apenas para o dono do servidor)."
    )
    async def criar_personalizada(self, interaction: discord.Interaction, online_mode: app_commands.Choice[int], match_format: app_commands.Choice[int], debug: bool = False):
        """Ponto de entrada para o comando de criação de partida."""
        if debug and interaction.user.id != interaction.guild.owner_id:
            return await interaction.response.send_message("Você não tem permissão para usar o modo de debug.", ephemeral=True)

        if match_format.value == 2: # Balanceado
            await interaction.response.send_message(
                "O modo de jogo Balanceado ainda está em desenvolvimento.",
                ephemeral=True,
                delete_after=5
            )
            return

        success, voice_channels, text_channel = await self.manage_channels(interaction)
        if not success:
            return

        waiting_channel = voice_channels["| 🕘 | AGUARDANDO"]
        blue_channel    = voice_channels["LADO [ |🔵| ]"]
        red_channel     = voice_channels["LADO [ |🔴| ]"]

        # ── Se ainda não respondeu, defer ──────────────────────────────────────
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        # Modo Online -> Cria lobby no backend, usa OnlineLobbyView
        if online_mode.value == 1:
            try:
                timbas = timbasService()
                MATCH_FORMAT_MAP = {0: "ALEATORIO", 1: "LIVRE", 3: "ALEATORIO_COMPLETO"}
                payload = {
                    "discordServerId": str(interaction.guild.id),
                    "creatorDiscordId": str(interaction.user.id),
                    "matchFormat": MATCH_FORMAT_MAP.get(match_format.value, "ALEATORIO"),
                }
                response = await asyncio.to_thread(timbas.createLobby, payload)
                if not response or response.status_code != 201:
                    error = response.json().get("message", "Erro") if response else "Sem resposta da API"
                    msg = await interaction.followup.send(f"❌ Erro ao criar partida no servidor: {error}", ephemeral=True, wait=True)
                    await asyncio.sleep(5)
                    await msg.delete()
                    return

                lobby_data = response.json()
                lobby_id = lobby_data["id"]

                view = OnlineLobbyView(
                    creator=interaction.user,
                    lobby_id=lobby_id,
                    match_format=match_format,
                    waiting_channel=waiting_channel,
                    blue_channel=blue_channel,
                    red_channel=red_channel,
                    debug=debug,
                )

                initial_embed_text = generate_league_embed_text(
                    blue_team=[], red_team=[],
                    match_format=match_format.name,
                    online_mode=online_mode.name
                )
                embed = discord.Embed(description=f"```{initial_embed_text}```", color=discord.Color.blue())
                embed.set_footer(text="Aguardando jogadores... 0/10")
                embed.set_image(url="attachment://timbasQueueGif.gif")

                web_url = f"{WEB_URL}/dashboard/match/{lobby_id}"
                embed.add_field(name="\u200b", value=f"[Acompanhe pelo site]({web_url})", inline=False)

                lobby_message = await text_channel.send(embed=embed, view=view, file=discord.File('./images/timbasQueueGif.gif'))
                view.start_sse_listener(lobby_message)

                message = await interaction.followup.send(
                    f"✅ Partida criada! Veja em {text_channel.mention}\n🌐 Ao vivo: {web_url}",
                    ephemeral=True, wait=True
                )
                await asyncio.sleep(8)
                try:
                    await message.delete()
                except:
                    pass

            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Erro ao criar lobby online: {e}")
                msg = await interaction.followup.send("❌ Erro inesperado ao criar a partida. Tente novamente.", ephemeral=True, wait=True)
                await asyncio.sleep(5)
                await msg.delete()
            return

        # Modo Offline -> Lógica original no bot (CustomMatchView)
        view = CustomMatchView(
            creator=interaction.user,
            waiting_channel=waiting_channel,
            blue_channel=blue_channel,
            red_channel=red_channel,
            online_mode=online_mode,
            match_format=match_format,
            debug=debug
        )

        if debug:
            default_discord_ids = [
                "919276824578646068", "352240724693090305", "373887997826957312",
                "1089165750993948774", "209825857815052288", "343492133644140544",
                "191630723935895553", "214397364163706880", "430165932963266561",
                "635277051439611914"
            ]
            confirmed_players = []
            for i, p_id in enumerate(default_discord_ids):
                try:
                    user_obj = await self.client.fetch_user(int(p_id))
                    confirmed_players.append(user_obj)
                except (discord.NotFound, ValueError):
                    confirmed_players.append(MockUser(name=f"TestPlayer{i+1}", id=int(p_id)))

            view.confirmed_players = confirmed_players
            view.update_buttons()

        blue_display = view.blue_team if view.blue_team else view.confirmed_players[:5]
        red_display  = view.red_team  if view.red_team  else view.confirmed_players[5:]

        initial_embed_text = generate_league_embed_text(
            blue_team=blue_display, red_team=red_display,
            match_format=match_format.name, online_mode=online_mode.name
        )
        embed = discord.Embed(description=f"```{initial_embed_text}```", color=discord.Color.blue())
        embed.set_footer(text="Aguardando jogadores...")
        embed.set_image(url="attachment://timbasQueueGif.gif")

        await text_channel.send(embed=embed, view=view, file=discord.File('./images/timbasQueueGif.gif'))

        message = await interaction.followup.send(
            f"Partida criada com sucesso! Veja em {text_channel.mention}",
            ephemeral=True, wait=True
        )
        await asyncio.sleep(5)
        try:
            await message.delete()
        except:
            pass

async def setup(client):
    await client.add_cog(CriarPerson(client))