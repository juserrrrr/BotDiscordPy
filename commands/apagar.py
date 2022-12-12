import discord
from discord.ext import commands
from discord import app_commands

class Apagar(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @app_commands.command(name = 'apagar')
    @commands.has_role(785650860125978635)
    async def apagar(self,interaction: discord.Interaction,quantidade:int):
        embed_message = discord.Embed(
            title = f"🎅 │ **{interaction.guild.name}     **",
            description = f"**{quantidade} {'mensagem apagada' if quantidade == 1 else 'mensagens apagadas'} com sucesso!**",
            color = 0xFF0004
        )
        embed_message.set_thumbnail(url = interaction.guild.icon.replace(format="png").url)
        await interaction.channel.purge(limit = quantidade,)
        await interaction.response.send_message(embed = embed_message,ephemeral=True,delete_after=2)


async def setup(client):
    await client.add_cog(Apagar(client))