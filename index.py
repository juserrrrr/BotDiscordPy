import os
import asyncio
import logging
import sys

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
        # Define as intents que seu bot precisa. 'all' é simples, mas pode consumir muitos recursos.
        # Para produção, é melhor especificar apenas as intents que você realmente precisa.
        intents = discord.Intents.all()
        # Inicializa o bot. Nenhum prefixo é necessário para bots que usam apenas slash commands.
        super().__init__(command_prefix=None, intents=intents, help_command=None)

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