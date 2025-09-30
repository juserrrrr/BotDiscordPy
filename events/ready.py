import discord
from discord.ext import commands, tasks
import logging
from itertools import cycle

logger = logging.getLogger(__name__)

class Ready(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.activities = None
        self.presence_update.start()

    def cog_unload(self):
        """Garante que a tarefa seja cancelada quando o cog for descarregado."""
        self.presence_update.cancel()

    @tasks.loop(seconds=20)
    async def presence_update(self):
        """Cicla entre as presenças do bot a cada 20 segundos."""
        next_activity_gen = next(self.activities)
        # Se o item no ciclo for uma função (para obter dados dinâmicos), chame-a
        activity = next_activity_gen() if callable(next_activity_gen) else next_activity_gen
        await self.client.change_presence(activity=activity)

    @presence_update.before_loop
    async def before_presence_update(self):
        """Executa antes do loop iniciar. Espera o bot estar pronto."""
        await self.client.wait_until_ready()
        # Inicializa o ciclo de atividades aqui para garantir que self.client.users esteja populado
        self.activities = cycle([
            discord.Streaming(name="v0.7", url="https://www.twitch.tv/juserrrrr"),
            lambda: discord.Streaming(name=f"{len(self.client.users)} membros", url="https://www.twitch.tv/juserrrrr")
        ])

    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()
        logger.info(f"Entrei como o bot {self.client.user.name} e estou presente em {len(self.client.guilds)} {'servidor.' if len(self.client.guilds) == 1 else 'servidores.'}")

async def setup(client: commands.Bot):
    await client.add_cog(Ready(client))