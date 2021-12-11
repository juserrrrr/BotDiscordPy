import discord
from discord.ext import commands

class JoinServer(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.Cog.listener()
    async def on_member_join(self,member):
        channelDoor = self.client.get_channel(919076619451269160)
        embed_message = discord.Embed(
            title = "🏃‍♂️ │ Bem-vindo!",
            description = f"{member.mention} acaba entrar para o {member.guild.name}.",
            color = 0x00FF23
        )
        embed_message.set_thumbnail(url = member.avatar_url_as(format = 'png'))
        message = await channelDoor.send(embed = embed_message)

    @commands.Cog.listener()
    async def on_member_remove(self,member):
        channelDoor = self.client.get_channel(919076619451269160)
        embed_message = discord.Embed(
            title = "🏃‍♂️ │ Até a proxima!",
            description = f"{member.mention} acaba de sair do {member.guild.name}.",
            color = 0xFF0004
        )
        embed_message.set_thumbnail(url = member.avatar_url_as(format = 'png'))
        message = await channelDoor.send(embed = embed_message)

def setup(client):
    client.add_cog(JoinServer(client))