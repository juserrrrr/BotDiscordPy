import discord
from discord.ui import Button, View
from discord import app_commands
from discord.ext import commands
from random import randint


class CriarPerson(commands.Cog):
    def __init__(self,client):
        self.client = client

    @app_commands.command(name = 'criarperson',description="Cria uma mensagem para que os usuarios possam entrar no sorteio da partida personalizada.")
    @app_commands.checks.has_role(item=785650860125978635)
    async def criarPerson(self,interaction: discord.Interaction,limite: int):    
      #Funções
      def gerarTextoUsers(usersPersonList):
        string = ''
        tamanho = len(usersPersonList)
        for index,user in enumerate(usersPersonList):
          if index == (tamanho-1):
            string += f" {user.name}"
          else:
            string += f" {user.name} |"
        return string  
      
      def sorteadorTimes(userParticipantes):
        time_azul = []
        time_vermelho = []
        tamanho = int(len(userParticipantes)/2)
        for i in range(tamanho):
          value1 = randint(0,len(userParticipantes)-1)
          time_azul.append(userParticipantes[value1])
          userParticipantes.pop(value1)
          value2 = randint(0,len(userParticipantes)-1)
          time_vermelho.append(userParticipantes[value2])
          userParticipantes.pop(value2)
        return (time_azul,time_vermelho)

      async def moverTimeAzul(time_azul,channel):
        channel_azul = await self.client.fetch_channel(channel)
        for user in time_azul:
          await user.move_to(channel_azul)

      async def moverTimeVermelho(time_vermelho,channel):
        channel_vermelho = await self.client.fetch_channel(channel)
        for user in time_vermelho:
          await user.move_to(channel_vermelho)

      def embedMessage(confirmados):
        embed_message = discord.Embed(
          title = f"**{interaction.guild.name} | Partida personalizada 🚩 **",
          description = f"**Confirmados:**{confirmados}",
          color = 0xFF0004,
        )
        embed_message.set_thumbnail(url = 'https://cdn-icons-png.flaticon.com/512/1732/1732468.png')
        return embed_message

      def embedMessageWinners(usersAzul,usersVermelho):
        embed_message = discord.Embed(
          title = f"**{interaction.guild.name} | Partida personalizada 🚩 **",
          description = f"**TimeAzul:**{usersAzul}\n**TimeVermelho:**{usersVermelho}\n**Ganhadores:**",
          color = 0xFF0004,
        )
        embed_message.set_thumbnail(url = 'https://cdn-icons-png.flaticon.com/512/1732/1732468.png')
        return embed_message

      async def buttonEntrarPerson(interaction:discord.Interaction):
        user = interaction.user
        if not user in users_confirmados:
          await user.move_to(channel_aguardado)
          users_confirmados.append(user)
          button_Qnt.label = f"{len(users_confirmados)}/{limite}"
          if len(users_confirmados) >= limite:
            button_Entrar.disabled = True
            button_Sortear.disabled = False
          await interaction.response.edit_message(embed=embedMessage(gerarTextoUsers(users_confirmados)),view=view)
        
        else:
          msg = await interaction.user.send("Você já esta confirmado.")
          msg.delete(delay=4)
          await interaction.response.defer()

      async def buttonSairPerson(interaction:discord.Interaction):
        user = interaction.user
        if user in users_confirmados:
          await user.move_to(channel_principal)
          users_confirmados.remove(user)
          button_Qnt.label = f"{len(users_confirmados)}/{limite}"
          if len(users_confirmados) < limite:
            button_Entrar.disabled = False
            button_Sortear.disabled = True
          await interaction.response.edit_message(embed=embedMessage(gerarTextoUsers(users_confirmados)),view=view)

      async def buttonSortearPerson(interaction:discord.Interaction):
        time_azul, time_vermelho = sorteadorTimes(users_confirmados)
        await moverTimeAzul(time_azul,785652356217962516)
        await moverTimeVermelho(time_vermelho,785652405915222029)
        button_Sortear.disabled = True
        button_Sair.disabled = True
        timeAzul = gerarTextoUsers(time_azul)
        timeVermelho = gerarTextoUsers(time_vermelho)
        await interaction.response.edit_message(embed=embedMessageWinners(timeAzul,timeVermelho),view=view)

      #Procedimentos
        #Variaveis
      channel_principal = await self.client.fetch_channel(785653602928033802)
      channel_aguardado = await self.client.fetch_channel(854680472206442537)
      users_confirmados = []

      button_Entrar = Button(label="Entrar",style=discord.ButtonStyle.green, emoji="✔")
      button_Entrar.callback = buttonEntrarPerson

      button_Sair = Button(label="Sair",style=discord.ButtonStyle.red, emoji="❌")
      button_Sair.callback = buttonSairPerson

      button_Qnt = Button(label=f"0/{limite}",style=discord.ButtonStyle.grey, emoji="👨‍👩‍👦",disabled=True)

      button_Sortear = Button(label="Start",style=discord.ButtonStyle.success, emoji="▶",disabled=True)
      button_Sortear.callback = buttonSortearPerson


      view = View()
      view.add_item(button_Entrar)
      view.add_item(button_Sair)
      view.add_item(button_Qnt)
      view.add_item(button_Sortear)
    
    
      embed_message = embedMessage('')
      await interaction.response.send_message(embed=discord.Embed(description="Comando executado com sucesso!",color=interaction.guild.me.color),ephemeral=True,delete_after=4)
      await interaction.channel.send(embed = embed_message, view = view)    

async def setup(client):
    await client.add_cog(CriarPerson(client))