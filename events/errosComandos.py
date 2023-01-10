import discord
from discord.ext import commands

class ErroComando(commands.Cog):
    def __init__(self,client: commands.Bot):
        self.client = client


    @commands.Cog.listener()
    async def on_error(self, ctx: commands.Context, error):
        print("porra")


async def setup(client:commands.bot):
    await client.add_cog(ErroComando(client))