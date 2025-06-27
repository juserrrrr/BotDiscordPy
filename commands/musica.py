import asyncio
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import logging

# Configura o logger para este cog
logger = logging.getLogger(__name__)

# Suprime mensagens de erro desnecessárias do yt-dlp no console
yt_dlp.utils.bug_reports_message = lambda *args, **kwargs: ''

# --- Configurações ---

# Configurações do yt-dlp para extrair o áudio com a melhor qualidade
YTDL_FORMAT_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

# Configurações do FFmpeg para streaming
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

# Instância do YoutubeDL com as configurações
ytdl = yt_dlp.YoutubeDL(YTDL_FORMAT_OPTIONS)


# --- Classes Auxiliares ---

class YTDLSource(discord.PCMVolumeTransformer):
    """Classe que representa uma fonte de áudio do YouTube para o discord.py."""

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title', 'Música desconhecida')
        self.url = data.get('webpage_url', '')
        self.duration = data.get('duration', 0)
        self.uploader = data.get('uploader', 'Desconhecido')
        self.thumbnail = data.get('thumbnail', None)
        self.next_song = asyncio.Event()

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if data is None:
            raise yt_dlp.utils.DownloadError("Não foi possível obter informações do vídeo/playlist.")

        if 'entries' in data:
            return [cls(discord.FFmpegPCMAudio(entry['url'], **FFMPEG_OPTIONS), data=entry) for entry in
                    data['entries'] if entry]

        return [cls(discord.FFmpegPCMAudio(data['url'], **FFMPEG_OPTIONS), data=data)]


class MusicQueue(asyncio.Queue):
    """Fila de música customizada para facilitar o acesso aos itens."""

    def __getitem__(self, item):
        return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()


# --- Cog Principal ---

class Musica(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.queues = {}  # {guild_id: MusicQueue}
        self.player_tasks = {}  # {guild_id: asyncio.Task}

    def get_queue(self, guild_id: int) -> MusicQueue:
        """Obtém a fila para um servidor, criando uma se não existir."""
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    async def cleanup(self, guild: discord.Guild):
        """Limpa os recursos de música para um servidor."""
        try:
            await guild.voice_client.disconnect()
        except (AttributeError, asyncio.CancelledError):
            pass

        if guild.id in self.player_tasks:
            self.player_tasks[guild.id].cancel()

        if guild.id in self.queues:
            self.queues[guild.id].clear()

        # Usar pop para remover com segurança
        self.player_tasks.pop(guild.id, None)
        self.queues.pop(guild.id, None)

    async def player_loop(self, interaction: discord.Interaction):
        """O loop principal que consome músicas da fila e as toca."""
        guild = interaction.guild

        while True:
            queue = self.get_queue(guild.id)
            try:
                player_source = await asyncio.wait_for(queue.get(), timeout=300)
            except asyncio.TimeoutError:
                logger.info(f"Fila vazia por 5 minutos no servidor {guild.name}. Desconectando.")
                await self.cleanup(guild)
                return

            guild.voice_client.play(player_source,
                                    after=lambda e: self.client.loop.call_soon_threadsafe(player_source.next_song.set()))

            embed = discord.Embed(
                title="▶️ Tocando Agora",
                description=f"[{player_source.title}]({player_source.url})",
                color=discord.Color.green()
            )
            if player_source.thumbnail:  # Adicionar thumbnail se disponível
                embed.set_thumbnail(url=player_source.thumbnail)
            if player_source.duration > 0:  # Adicionar duração se disponível
                embed.add_field(name="Duração",
                                value=f"{int(player_source.duration // 60)}:{int(player_source.duration % 60):02d}")
            embed.add_field(name="Canal", value=player_source.uploader)
            await interaction.channel.send(embed=embed)

            await player_source.next_song.wait()
            player_source.next_song.clear()

            if not guild.voice_client or not guild.voice_client.is_connected():
                logger.info(f"Player loop finalizado para o servidor {guild.name} (desconectado).")
                await self.cleanup(guild)
                break

    @app_commands.command(name="tocar", description="Toca uma música ou playlist do YouTube.")
    @app_commands.describe(busca="O nome, URL da música ou URL da playlist.")
    @app_commands.guild_only()
    async def tocar(self, interaction: discord.Interaction, *, busca: str):
        if not interaction.user.voice:
            await interaction.response.send_message("Você precisa estar em um canal de voz para usar este comando.",
                                                     ephemeral=True)
            return

        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        if not voice_client:
            voice_client = await voice_channel.connect()
        elif voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)

        await interaction.response.defer(thinking=True)

        try:
            sources = await YTDLSource.from_url(busca, loop=self.client.loop)
            queue = self.get_queue(interaction.guild.id)

            for source in sources:
                await queue.put(source)

            if len(sources) > 1:
                await interaction.followup.send(f"✅ Adicionado **{len(sources)}** músicas da playlist à fila!")
            else:
                await interaction.followup.send(f"✅ Adicionado à fila: **{sources[0].title}**")

            if interaction.guild.id not in self.player_tasks or self.player_tasks[interaction.guild.id].done():
                task = self.client.loop.create_task(self.player_loop(interaction))
                self.player_tasks[interaction.guild.id] = task

        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Erro de download do yt-dlp: {e}")
            await interaction.followup.send(
                f"❌ Ocorreu um erro ao buscar a música/playlist. Verifique o link ou o nome e tente novamente.")
        except Exception as e:
            logger.error(f"Erro inesperado no comando /tocar: {e}", exc_info=True)
            await interaction.followup.send(f"❌ Ocorreu um erro inesperado: `{e}`")

    @app_commands.command(name="fila", description="Mostra a fila de músicas atual.")
    @app_commands.guild_only()
    async def fila(self, interaction: discord.Interaction):
        queue = self.get_queue(interaction.guild.id)
        voice_client = interaction.guild.voice_client

        if len(queue) == 0 and (not voice_client or not voice_client.is_playing()):
            return await interaction.response.send_message("A fila está vazia.", ephemeral=True)

        embed = discord.Embed(title="🎵 Fila de Músicas", color=discord.Color.blue())

        if voice_client and voice_client.source:
            embed.add_field(name="Tocando Agora", value=f"**{voice_client.source.title}**", inline=False)

        if len(queue) > 0:
            description_list = []
            for i, song in enumerate(queue):
                if i < 10:  # Limita a exibição para as próximas 10 músicas
                    description_list.append(f"**{i+1}.** {song.title}")

            if description_list:
                embed.description = "\n".join(description_list)

            if len(queue) > 10:
                embed.set_footer(text=f"E mais {len(queue) - 10} música(s)...")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pular", description="Pula a música que está tocando.")
    @app_commands.guild_only()
    async def pular(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_playing():
            return await interaction.response.send_message("Não estou tocando nada no momento.", ephemeral=True)

        voice_client.stop()
        await interaction.response.send_message("⏭️ Música pulada!", ephemeral=True)

    @app_commands.command(name="parar", description="Para a música e limpa a fila.")
    @app_commands.guild_only()
    async def parar(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if not voice_client or not voice_client.is_playing():
            return await interaction.response.send_message("Não estou tocando nada no momento.", ephemeral=True)

        queue = self.get_queue(interaction.guild.id)
        queue.clear()
        voice_client.stop()
        await interaction.response.send_message("⏹️ Música parada e fila limpa!", ephemeral=True)

    @app_commands.command(name="sair", description="Desconecta o bot do canal de voz e limpa a fila.")
    @app_commands.guild_only()
    async def sair(self, interaction: discord.Interaction):
        await self.cleanup(interaction.guild)
        await interaction.response.send_message("👋 Desconectado. Até a próxima!", ephemeral=True)


async def setup(client: commands.Bot):
    await client.add_cog(Musica(client))