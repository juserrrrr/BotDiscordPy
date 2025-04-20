import discord
from discord.ext import commands
from services.timbasService import timbasService


class JoinServer(commands.Cog):
  def __init__(self, client):
    self.client = client
    self.timbasService = timbasService()

  @commands.Cog.listener()
  async def on_member_join(self, member):
    channelDoor = self.client.get_channel(1191521944768618517)
    embed_message = discord.Embed(
        title="🎉 │ Bem-vindo(a)!",
        description=f"**{member.name}** acaba de entrar para o {member.guild.name}.",
        color=0x00FF23
    )
    embed_message.set_thumbnail(
        url=member.display_avatar.replace(format='png').url)
    await channelDoor.send(content=f"{member.mention}", embed=embed_message)

  @commands.Cog.listener()
  async def on_member_ban(self, guild: discord.Guild, member: discord.Member):
    channelDoor = self.client.get_channel(1191521944768618517)
    embed_message = discord.Embed(
        title="⛔ │ Já vai tarde.",
        description=f"**{member.name}** acaba de ser banido do {guild.name}.",
        color=0xFF0004
    )
    embed_message.set_thumbnail(
        url=member.display_avatar.replace(format='png').url)
    await channelDoor.send(content=f"{member.mention}", embed=embed_message)

  @commands.Cog.listener()
  async def on_member_remove(self, member: discord.Member):
    channelDoor = self.client.get_channel(1191521944768618517)
    try:
      ban = await member.guild.fetch_ban(member)
      if ban:
        return  # Se foi banido, não envia a mensagem
    except discord.NotFound:
      pass

    embed_message = discord.Embed(
        title="🏃 │ Até a próxima!",
        description=f"**{member.name}** acaba de sair do {member.guild.name}.",
        color=0xFF0004
    )
    embed_message.set_thumbnail(
        url=member.display_avatar.replace(format='png').url)
    await channelDoor.send(content=f"{member.mention}", embed=embed_message)


async def setup(client):
  await client.add_cog(JoinServer(client))
