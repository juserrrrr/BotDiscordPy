import discord
from discord.ui import Button, View
from discord import app_commands
from discord.ext import commands
from random import randint


class CriarPerson(commands.Cog):
    def __init__(self,client:discord.Client):
        self.client = client

    @app_commands.command(name = 'criarperson',description="Cria uma mensagem para que os usuarios possam entrar no sorteio da partida personalizada.")
    @app_commands.guild_only()
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
        while userParticipantes:
          value1 = randint(0,len(userParticipantes)-1)
          time_azul.append(userParticipantes[value1])
          userParticipantes.pop(value1)
          value2 = randint(0,len(userParticipantes)-1)
          time_vermelho.append(userParticipantes[value2])
          userParticipantes.pop(value2)
        return (time_azul,time_vermelho)

      async def moverTime(time,channel):
        channel_azul = await self.client.fetch_channel(channel)
        for user in time:
          await user.move_to(channel_azul)

          

      def embedMessage(confirmados):
        embed_message = discord.Embed(
          title = f"**{interaction.guild.name} | Partida personalizada 🚩 **",
          description = f"**Confirmados:**{confirmados}",
          color = 0xFF0004,
        )
        embed_message.set_thumbnail(url = 'https://i.imgur.com/z3rGL5L.png')
        embed_message.set_footer(icon_url=interaction.guild.icon.url,text="SysTeamBahia v0.5")
        return embed_message

      def embedMessageWinners(usersAzul,usersVermelho):
        embed_message = discord.Embed(
          title = f"**{interaction.guild.name} | Partida personalizada 🚩 **",
          description = f"**TimeAzul:**{usersAzul}\n**TimeVermelho:**{usersVermelho}",
          color = 0xFF0004,
        )
        embed_message.set_thumbnail(url = 'https://i.imgur.com/z3rGL5L.png')
        embed_message.set_footer(icon_url=interaction.guild.icon.url,text="SysTeamBahia v0.5")
        return embed_message

      async def buttonEntrarPerson(interaction_entrar:discord.Interaction):
        user = interaction_entrar.user
        if not user in users_confirmados:
          await user.move_to(channel_aguardado)
          users_confirmados.append(user)
          button_Qnt.label = f"{len(users_confirmados)}/{limite}"
          if len(users_confirmados) >= limite:
            button_Entrar.disabled = True
            button_Sortear.disabled = False
          await interaction_entrar.response.edit_message(embed=embedMessage(gerarTextoUsers(users_confirmados)),view=view)   
        else:
          await interaction_entrar.response.send_message(embed=discord.Embed(description="Você já esta confirmado.",color=interaction.guild.me.color),ephemeral=True,delete_after=3)

      async def buttonSairPerson(interaction_sair:discord.Interaction):
        user = interaction_sair.user
        if user in users_confirmados:
          await user.move_to(channel_principal)
          users_confirmados.remove(user)
          button_Qnt.label = f"{len(users_confirmados)}/{limite}"
          if len(users_confirmados) < limite:
            button_Entrar.disabled = False
            button_Sortear.disabled = True
          await interaction_sair.response.edit_message(embed=embedMessage(gerarTextoUsers(users_confirmados)),view=view)
        else:
          await interaction_sair.response.send_message(embed=discord.Embed(description="Você não esta na lista de confirmados.",color=interaction.guild.me.color),ephemeral=True,delete_after=3)

      async def buttonSortearPerson(interaction_sortear:discord.Interaction):
        if(interaction_sortear.user == interaction.user):
          button_Sortear.disabled = True
          button_Sair.disabled = True
          time_azul, time_vermelho = sorteadorTimes(users_confirmados)
          timeAzul = gerarTextoUsers(time_azul)
          timeVermelho = gerarTextoUsers(time_vermelho)
          await interaction_sortear.response.edit_message(embed=embedMessageWinners(timeAzul,timeVermelho),view=view)
          await moverTime(time_azul,785652356217962516)
          await moverTime(time_vermelho,785652405915222029)
        else:
          await interaction_sortear.response.send_message(embed=discord.Embed(description="Somente o criador da personalizada pode executar esta ação.",color=interaction.guild.me.color),ephemeral=True,delete_after=3)

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