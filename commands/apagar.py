import discord
import asyncio
from discord.ext import commands
from discord import app_commands


class Apagar(commands.Cog):
  def __init__(self, client: commands.Bot):
    self.client = client

  @app_commands.command(name='apagar', description="Apaga x mensagens no canal que foi executado o comando.")
  @app_commands.guild_only()
  async def apagar(self, interaction: discord.Interaction, quantidade: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=quantidade)
    embed_message = discord.Embed(
        title=f"🚨 │ **{interaction.guild.name}**",
        description=f"**{quantidade} {'mensagem apagada' if quantidade == 1 else 'mensagens apagadas'}!**",
        color=0xFF0004
    )
    if interaction.guild.icon:
        embed_message.set_thumbnail(url=interaction.guild.icon.with_format("png").url)
    msg = await interaction.followup.send(embed=embed_message, ephemeral=True, wait=True)
    await asyncio.sleep(5)
    try:
        await msg.delete()
    except Exception:
        pass


async def setup(client: commands.Bot):
  await client.add_cog(Apagar(client))
