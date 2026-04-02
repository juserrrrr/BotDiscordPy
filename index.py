import os
import asyncio
import logging
import sys
from collections import defaultdict
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Configura o logging para fornecer um feedback melhor durante o desenvolvimento e em produção.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class MyBot(commands.Bot):
    def __init__(self):
        # Define as intents que seu bot precisa. Use intents específicas para melhor performance e segurança.
        intents = discord.Intents.default()
        intents.message_content = True  # Only if you need to read message content
        intents.guilds = True
        intents.members = True
        intents.presences = True
        intents.voice_states = True
        # Remove intents you don't need to reduce attack surface
        intents.typing = False

        # Inicializa o bot. Nenhum prefixo é necessário para bots que usam apenas slash commands.
        super().__init__(
            command_prefix=None,
            intents=intents,
            help_command=None,
            case_insensitive=True,
        )

        # Rate limiting per user (commands per minute)
        self.user_commands = defaultdict(list)
        self.rate_limit = 10  # commands per minute per user
        self.rate_window = 60  # seconds

    def check_rate_limit(self, user_id: int) -> bool:
        """Check if user has exceeded rate limit."""
        now = datetime.now()
        self.user_commands[user_id] = [
            cmd_time for cmd_time in self.user_commands[user_id]
            if now - cmd_time < timedelta(seconds=self.rate_window)
        ]
        if len(self.user_commands[user_id]) >= self.rate_limit:
            return False
        self.user_commands[user_id].append(now)
        return True

    async def load_extensions_from_dir(self, directory: str):
        """Carrega todas as extensões de um determinado diretório."""
        for filename in os.listdir(directory):
            # Ignora arquivos que não são python e arquivos especiais como __init__.py
            if filename.endswith('.py') and not filename.startswith('__'):
                extension_name = f"{directory}.{filename[:-3]}"
                try:
                    await self.load_extension(extension_name)
                    logger.info(f"Extensão carregada com sucesso: {extension_name}")
                except commands.ExtensionError as e:
                    logger.error(f"Falha ao carregar a extensão {extension_name}.", exc_info=e)

    async def setup_hook(self) -> None:
        """É chamado uma vez quando o bot está configurando. É o lugar ideal para carregar extensões."""
        logger.info("--- O bot está iniciando, carregando extensões... ---")
        for ext_dir in ['commands', 'events']:
            if os.path.isdir(ext_dir):
                await self.load_extensions_from_dir(ext_dir)
        logger.info("--- Todas as extensões foram carregadas. ---")

async def main():
    bot = MyBot()
    token = os.getenv("TOKEN_BOT")
    if not token:
        logger.critical("Variável de ambiente TOKEN_BOT não encontrada. Por favor, crie um arquivo .env e adicione-a.")
        return

    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.critical("Falha ao fazer login. O token do bot fornecido é inválido.")

if __name__ == "__main__":
    asyncio.run(main())