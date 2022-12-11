import discord
from discord.ext import commands
import asyncio
from random import randint


class Desativado(commands.Cog):
  def __init__(self,client):
    self.client = client

  @commands.command(name='desativado')
  @commands.has_role(785650860125978635)
  async def criarPerson(self,ctx):
    #Funções
    def embedCreateMessage(confirmados,qntd_confirmados):
      embed = discord.Embed(
      title=f"{ctx.guild.name} [{qntd_confirmados}/{limite}]",
      description=f"**Reaja a esta mensagem para participar da personalizada!**\nVocê precisa estar conectado a um canal de voz.\nConfirmados:{confirmados}",
      color=0xffff00
      )
      embed.set_thumbnail(url = 'https://cdn-icons-png.flaticon.com/512/1732/1732468.png')
      return embed

    def embedDmMessage():
      embed = discord.Embed(
      title=f"{ctx.guild.name} | Confirmar personalizada.",
      description=f"**Reaja com ✅, quando estiver pronto para sorteador as equipes!**",
      color=0xffff00
      )
      # embed.set_thumbnail(url = ctx.author.display_avatar.replace(format='png').url)
      return embed

    def checkAdd(reaction,user):
      return str(reaction) == '🆗' and reaction.message.id == message_embed.id and not user in contador_players

    def checkRemove(reaction,user):
      return str(reaction) == '🆗' and reaction.message.id == message_embed.id

    def checkDm(reaction,user):
      return str(reaction) == '✅' and reaction.message.id == dm_message.id

    def gerarConfirmados(users_confirmados):
      string = ''
      for user in users_confirmados:
        string += f" {user.name} |"
      return string  

    def sorteadorTimes(users_confirmados):
      time_azul = []
      time_vermelho = []
      for i in range(int(len(users_confirmados)/2)):
        value1 = randint(0,len(users_confirmados)-1)
        time_azul.append(users_confirmados[value1])
        users_confirmados.pop(value1)
        value2 = randint(0,len(users_confirmados)-1)
        time_vermelho.append(users_confirmados[value2])
        users_confirmados.pop(value2)
      return (time_azul,time_vermelho)

    async def moverTimeAzul(time_azul,channel):
      channel_azul = await self.client.fetch_channel(channel)
      for user in time_azul:
        await user.move_to(channel_azul)

    async def moverTimeVermelho(time_vermelho,channel):
      channel_vermelho = await self.client.fetch_channel(channel)
      for user in time_vermelho:
        await user.move_to(channel_vermelho)

    async def reactionAddParticipation():
      while len(contador_players) < limite:
          reaction,user = await self.client.wait_for('reaction_add',check= checkAdd,timeout=60)
          if(user.voice != None):
            contador_players.append(user)
            confirmados = gerarConfirmados(contador_players)
            qnts_confirmados = str(len(contador_players))
            embed_edited = embedCreateMessage(confirmados,qnts_confirmados)
            await message_embed.edit(embed = embed_edited)
            await user.move_to(channel_aguardado)      
      task2.cancel()

    async def reactionRemoveParticipation():
      while len(contador_players) < limite:
          reaction,user = await self.client.wait_for('reaction_remove',check= checkRemove,timeout=60)
          contador_players.remove(user)
          confirmados = gerarConfirmados(contador_players)
          qnts_confirmados = str(len(contador_players))
          embed_edited = embedCreateMessage(confirmados,qnts_confirmados)
          await message_embed.edit(embed = embed_edited)

    #Procedimentos
    limite = 2

    await ctx.message.delete()

    embed = embedCreateMessage('','0')

    message_embed = await ctx.send(embed=embed)
    await message_embed.add_reaction('🆗')

    contador_players = [] #Colocar os usuarios que já reagiram a mensagem!
    channel_aguardado = await self.client.fetch_channel(854680472206442537)

    try:
      async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(reactionAddParticipation())
        task2 = tg.create_task(reactionRemoveParticipation())

    except asyncio.TimeoutError:
      await message_embed.delete()
    else:
      await message_embed.delete()

      dm_embed = embedDmMessage()
      dm_message = await ctx.author.send(embed = dm_embed)
      await dm_message.add_reaction('✅')
      reaction,user = await self.client.wait_for('reaction_add',check= checkDm,timeout=60)
      await dm_message.delete()

      time_azul,time_vermelho = sorteadorTimes(contador_players)
      await moverTimeAzul(time_azul,785652356217962516)
      await moverTimeVermelho(time_vermelho,785652405915222029)



async def setup(client):
    await client.add_cog(Desativado(client))
