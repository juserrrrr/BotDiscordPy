import discord
from discord.ui import Button, View
from discord import app_commands
from discord.ext import commands
from random import randint


class CriarPerson(commands.Cog):
    def __init__(self, client: discord.Client):
        self.client = client

    @app_commands.command(name='criarperson', description="Cria uma mensagem para que os usuarios possam entrar no sorteio da partida personalizada.")
    @app_commands.guild_only()
    async def criarPerson(self, interaction: discord.Interaction, limite: int):
        # Funções
        def generateTextUsers(usersPersonList):
            string = ''
            tamanho = len(usersPersonList)
            for index, user in enumerate(usersPersonList):
                if index == (tamanho-1):
                    string += f" {user.name}"
                else:
                    string += f" {user.name} |"
            return string

        def drawTeam(userParticipantes):
            time_azul = []
            time_vermelho = []
            while userParticipantes:
                value1 = randint(0, len(userParticipantes)-1)
                time_azul.append(userParticipantes[value1])
                userParticipantes.pop(value1)
                value2 = randint(0, len(userParticipantes)-1)
                time_vermelho.append(userParticipantes[value2])
                userParticipantes.pop(value2)
            return (time_azul, time_vermelho)

        async def moveTime(time, channel):
            channel_azul = await self.client.fetch_channel(channel)
            for user in time:
                await user.move_to(channel_azul)

        def embedMessage(confirmed):
            embed_message = discord.Embed(
                title=f"**League of Legends | Partida personalizada. 🚩 **",
                color=0xFF0004,
            )
            embed_message.add_field(
                name="**Time Azul 🔵**", value="Juser\nZig Zag\nBibo\nFabii87\nsweaterweather", inline=True)
            embed_message.add_field(
                name="**Time Vermelho 🔴**", value="Drownny\nZemiiudo\nDroga é a Vic\nIndio\nMaurinha", inline=True)
            embed_message.set_image(url='https://i.imgur.com/kNWEtds.png')
            embed_message.set_footer(
                text="🌐SysTeamBahia v0.5")
            return embed_message

        def embedMessageWinners(usersBlue, usersRed):
            embed_message = discord.Embed(
                title=f"**League of Legends | Partida personalizada. 🚩 **",
                description=f"**TimeAzul:**{usersBlue}\n**TimeVermelho:**{usersRed}",
                color=0xFF0004,
            )
            embed_message.set_image(url='https://i.imgur.com/kNWEtds.png')
            embed_message.set_footer(
                text="🌐SysTeamBahia v0.5")
            return embed_message

        async def btnJoinPerson(interactionJoin: discord.Interaction):
            user = interactionJoin.user
            if len(users_confirmed) >= limite:
                btnJoin.disabled = True
                btnDraw.disabled = False
            else:
                if not user in users_confirmed:
                    await user.move_to(channel_aguardado)
                    users_confirmed.append(user)
                    btnAmount.label = f"{len(users_confirmed)}/{limite}"
                    await interactionJoin.response.edit_message(
                        embed=embedMessage(generateTextUsers(users_confirmed)),
                        view=view
                    )
                else:
                    await interactionJoin.response.send_message(
                        embed=discord.Embed(description="Você já esta confirmado.",
                                            color=interaction.guild.me.color),
                        ephemeral=True,
                        delete_after=3
                    )

        async def btnExitPerson(interactionExit: discord.Interaction):
            user = interactionExit.user
            if user in users_confirmed:
                await user.move_to(channel_principal)
                users_confirmed.remove(user)
                btnAmount.label = f"{len(users_confirmed)}/{limite}"
                if len(users_confirmed) < limite:
                    btnJoin.disabled = False
                    btnDraw.disabled = True
                await interactionExit.response.edit_message(embed=embedMessage(generateTextUsers(users_confirmed)), view=view)
            else:
                await interactionExit.response.send_message(embed=discord.Embed(description="Você não esta na lista de confirmed.", color=interaction.guild.me.color), ephemeral=True, delete_after=3)

        async def btnDrawPerson(interactionDraw: discord.Interaction):
            if (interactionDraw.user == interaction.user):
                btnDraw.disabled = True
                btnExit.disabled = True
                time_azul, time_vermelho = drawTeam(users_confirmed)
                timeAzul = generateTextUsers(time_azul)
                timeVermelho = generateTextUsers(time_vermelho)
                await interactionDraw.response.edit_message(embed=embedMessageWinners(timeAzul, timeVermelho), view=view)
                await moveTime(time_azul, 785652356217962516)
                await moveTime(time_vermelho, 785652405915222029)
            else:
                await interactionDraw.response.send_message(embed=discord.Embed(description="Somente o criador da personalizada pode executar esta ação.", color=interaction.guild.me.color), ephemeral=True, delete_after=3)

        # Procedimentos
        # Variaveis
        # channel_principal = await self.client.fetch_channel(785653602928033802)
        # channel_aguardado = await self.client.fetch_channel(854680472206442537)
        users_confirmed = []

        # btnJoin = Button(
        #     label="Entrar", style=discord.ButtonStyle.green, emoji="✔")
        # btnJoin.callback = btnJoinPerson

        # btnExit = Button(
        #     label="Sair", style=discord.ButtonStyle.red, emoji="❌")
        # btnExit.callback = btnExitPerson

        # btnAmount = Button(
        #     label=f"0/{limite}", style=discord.ButtonStyle.grey, emoji="👨‍👩‍         👦",disabled=True)

        # btnDraw = Button(
        #     label="Start", style=discord.ButtonStyle.success, emoji="▶", disabled=True)
        # btnDraw.callback = btnDrawPerson

        # view = View()
        # view.add_item(btnJoin)
        # view.add_item(btnExit)
        # view.add_item(btnAmount)
        # view.add_item(btnDraw)

        embed_message = embedMessage('')
        await interaction.response.send_message(embed=discord.Embed(description="Comando executado com sucesso!", color=interaction.guild.me.color), ephemeral=True, delete_after=4)
        await interaction.channel.send(embed=embed_message)


async def setup(client):
    await client.add_cog(CriarPerson(client))
