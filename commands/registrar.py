import discord
from discord.ext import commands
from discord import app_commands


class Registrar(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.ctx_menu = app_commands.ContextMenu(
            name='Registrar',
            callback=self.registrar,
        )
        self.client.tree.add_command(self.ctx_menu)

    async def registrar(self, interaction: discord.Interaction, usuario: discord.Member):
        # Procedimentos
        cargoCriaId = 785650374195019806
        cargoAmigoId = 785650860125978635
        cargoCria = interaction.guild.get_role(cargoCriaId)
        if (not usuario.get_role(cargoCriaId) and not usuario.get_role(cargoAmigoId)):
            await usuario.add_roles(cargoCria)
        await interaction.response.send_message(embed=discord.Embed(description="Comando executado com sucesso!", color=interaction.guild.me.color), ephemeral=True, delete_after=4, )


async def setup(client: commands.Bot):
    client.command(Registrar(client))
