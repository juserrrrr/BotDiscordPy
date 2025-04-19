import discord
from discord.ext import commands
from discord import app_commands


class TrazerTodos(commands.Cog):
  def __init__(self, client: commands.Bot):
    self.client = client

  @app_commands.command(name='puxartodos', description="Puxa todos os usuários até o seu canal.")
  @app_commands.guild_only()
  async def trazerTodos(self, interaction: discord.Interaction):
    # Verifica se o usuário está em um canal de voz
    if not interaction.user.voice:
      await interaction.response.send_message(embed=discord.Embed(description="Você precisa estar em um canal de voz para usar este comando!", color=discord.Color.red()), ephemeral=True, delete_after=5)
      return

    # Verifica se existem usuários para mover
    afkChannel = interaction.guild.afk_channel
    authorChannel = interaction.user.voice.channel
    hasUsersToMove = False

    for channel in interaction.guild.voice_channels:
      if not channel == authorChannel and len(channel.members) > 0 or channel == afkChannel:
        hasUsersToMove = True
        break

    if not hasUsersToMove:
      await interaction.response.send_message(embed=discord.Embed(description="Não há usuários para mover!", color=discord.Color.red()), ephemeral=True, delete_after=5)
      return

    await interaction.response.send_message(embed=discord.Embed(description="Iniciando o processo de mover todos os membros...", color=interaction.guild.me.color), ephemeral=True)

    for channel in interaction.guild.voice_channels:
      if not channel == authorChannel and len(channel.members) > 0 or channel == afkChannel:
        for member in channel.members:
          await member.move_to(authorChannel)

    await interaction.edit_original_response(embed=discord.Embed(description="Comando executado com sucesso!", color=interaction.guild.me.color), delete_after=5)


async def setup(client: commands.Bot):
  await client.add_cog(TrazerTodos(client))
