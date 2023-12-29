import discord
from discord.ui import Button, View
from discord import app_commands
from discord.ext import commands
from .utilsPerson.viewInterfaces import *
from .utilsPerson.inputInterfaces import *
from .utilsPerson.utilsFunc import *




class CriarPerson(commands.Cog):
    def __init__(self, client: discord.Client):
        self.client = client

    @app_commands.command(name='criarperson', description="Cria uma mensagem para que os usuarios possam entrar no sorteio da partida personalizada.")
    @app_commands.guild_only()
    async def criarPerson(self, interaction: discord.Interaction):       

        def embedMessage(confirmed):
            embed_message = discord.Embed(
                title=f"**Partida personalizada ⚔️ **",
                description=f"**[League of Legends] - Summoner's rift**",
                color=0xFF0004,
            )
            embed_message.set_footer(
                text="⏳Aguardando jogadores...")
            embed_message.add_field(
                name="**Jogadores confirmados:**", value=f"{confirmed}")
            embed_message.set_image(url='https://i.imgur.com/kNWEtds.png')
            return embed_message
        
        def embedMessageTeam(blueUsers, redUsers):
            embed_message = discord.Embed(
                title=f"**Partida personalizada ⚔️ **",
                description=f"**League of Legends**",
                color=0xFF0004,
            )
            embed_message.set_footer(
                text="⏳Aguardando início da partida")
            embed_message.add_field(
                name="**Time Azul 🔵**", value=f"{blueUsers}", inline=True)
            embed_message.add_field(
                name="**Time Vermelho 🔴**", value=f"{redUsers}", inline=True)
            embed_message.set_image(url='https://i.imgur.com/kNWEtds.png')
            return embed_message

        def embedMessageWinners(usersBlue, usersRed):
            embed_message = discord.Embed(
                title=f"**League of Legends | Partida personalizada. 🚩 **",
                description=f"**TimeAzul:**{usersBlue}\n**TimeVermelho:**{usersRed}",
                color=0xFF0004,
            )
            embed_message.set_image(url='https://i.imgur.com/kNWEtds.png')
            embed_message.set_footer(
                text="🌐Timbas")
            return embed_message


        

        # Variaveis globais
        confirmedUsers = []
        guildChannelsDict = {channel.name: channel for channel in interaction.guild.channels}
        channelNameWaiting = '| 🕘 | AGUARDANDO'
        channelNameBlue = 'LADO [ |🔵| ]'
        channelNameRed = 'LADO [ |🔴| ]'
        userCallCommand = interaction.user
        if interaction.user.voice == None:
            return await interaction.response.send_message(embed=discord.Embed(description="Você não está em um canal de voz.", color=interaction.guild.me.color), ephemeral=True, delete_after=3)
        channelHome = interaction.user.voice.channel
        

        # Checar se o canal aguardado, lado azul e lado vermelho existem.
        if not all(channel in guildChannelsDict.keys() for channel in [channelNameWaiting, channelNameBlue, channelNameRed]):
            viewCreateChannels = ViewActionConfirm(channels=[channelNameWaiting, channelNameBlue, channelNameRed])
            await interaction.response.send_message(content="Percebi que o servidor não possui os canais de voz essenciais para o funcionamento da fila. Será que você poderia me permitir criar esses canais?", ephemeral=True, view=viewCreateChannels)
            try:
                responseCreate = await asyncio.wait_for(viewCreateChannels.future, timeout=5)
                if responseCreate == '0':
                    return
            except asyncio.TimeoutError:
                # Limite de tempo excedido, evento cancelado.
                return await interaction.delete_original_response()

       
        # 1. Pegar os canais de voz essenciais para o funcionamento da fila.
        guildChannelsDict = {channel.name: channel for channel in interaction.guild.channels}
        
        channelWaiting = guildChannelsDict[channelNameWaiting]
        channelBlue = guildChannelsDict[channelNameBlue]
        channelRed = guildChannelsDict[channelNameRed]
        # 2. Fazer os views para configuração da personalizada.
            
        # 3. Criar a personalizada.
        embed_message = embedMessage('')
        viewBtns = ViewBtnInterface(userCallCommand, channelWaiting, channelHome, channelBlue, channelRed, confirmedUsers, embedMessage, embedMessageTeam)
        await interaction.response.send_message(embed=embed_message, view=viewBtns)
        


async def setup(client):
    await client.add_cog(CriarPerson(client))
