import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands

class AddAmigo(commands.Cog):
    def __init__(self,client: commands.Bot):
        self.client = client

    @app_commands.command(name = 'adcionaramigo',description="Adciona um usuário ao cargo de amigos através de uma votação.")
    @app_commands.guild_only()
    async def adcionarAmigo(self,interaction: discord.Interaction,usuario:discord.Member):
      #Funções
      def embedMessage(confirmados):
        embed_message = discord.Embed(
          title = f"**Votação para o cargo de amigo ✅**",
          description = f"**Usuário: {usuario.name}\nVotação: [{confirmados}/{limiteVotacao}]\nTempo: 3 minutos.**",
          color = 0xFF0004,
        )
        embed_message.set_thumbnail(url = usuario.display_avatar.url)
        return embed_message
      
      async def bttnAceitarVotacao(interaction:discord.Interaction):
        user = interaction.user
        if not user in votos_confirmados_membros:
          votos_confirmados_membros.append(user)
          votos_sim.append(user)
          if len(votos_sim) >= limiteVotacao:
            buttonNao.disabled = True
            buttonSim.disabled = True    
            cargo = interaction.guild.get_role(cargoAmigoId)
            await usuario.add_roles(cargo)
          await interaction.response.edit_message(embed=embedMessage(len(votos_sim)),view=view)
        else:
          await interaction.response.send_message(embed=discord.Embed(description="Você já votou.",color=interaction.guild.me.color),ephemeral=True,delete_after=2)

      async def bttnNegarVotacao(interaction:discord.Interaction):
        user = interaction.user
        if not user in votos_confirmados_membros:
          votos_confirmados_membros.append(user)
          await interaction.response.send_message(embed=discord.Embed(description="Voto confirmado.",color=interaction.guild.me.color),ephemeral=True,delete_after=2)
        else:
          await interaction.response.send_message(embed=discord.Embed(description="Você já votou.",color=interaction.guild.me.color),ephemeral=True,delete_after=2)
      #Procedimentos
      if usuario.get_role(785650860125978635) is None:
        votos_confirmados_membros = []
        votos_sim = []
        cargoAmigoId = 785650860125978635
        canalAmigoId = 785650118413385760
        limiteVotacao = 5
        channelAmigos = interaction.guild.get_channel(canalAmigoId)
        embedText = embedMessage(0)


        buttonSim =  Button(label="Sim",style=discord.ButtonStyle.success,emoji="✅")
        buttonSim.callback = bttnAceitarVotacao
        buttonNao =  Button(label="Não",style=discord.ButtonStyle.danger,emoji="⛔")
        buttonNao.callback = bttnNegarVotacao

        view = View()
        view.add_item(buttonSim)
        view.add_item(buttonNao)
        await channelAmigos.send(embed=embedText,view=view)
        await interaction.response.send_message(embed=discord.Embed(description="Comando executado com sucesso.",color=interaction.guild.me.color),ephemeral=True,delete_after=4)
      else:
        await interaction.response.send_message(embed=discord.Embed(description="Esse usuario já possui esse cargo.",color=interaction.guild.me.color),ephemeral=True,delete_after=4)
async def setup(client: commands.Bot):
    await client.add_cog(AddAmigo(client))