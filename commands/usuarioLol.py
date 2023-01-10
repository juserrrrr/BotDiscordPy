import discord
from discord.ext import commands
from discord import app_commands
from apiLol.apilol import ApiLol
class UsuarioLol(commands.Cog):
    def __init__(self,client: commands.Bot):
      self.client = client
    
    @app_commands.command(name = 'usuariolol',description="Mostra as informações de determinado usuario do lol")
    @app_commands.guild_only()
    async def usuarioLol(self,interaction: discord.Interaction,usuario:str):

      embed_message = discord.Embed(
        title = f"🔷 │ **Usuário não encotrado**",
        description = f"Por favor, tente novamente",
        color = 0xFF0004
      )
      embed_message.set_thumbnail(url = interaction.guild.icon.url)

      apiLol = ApiLol()
      dados = apiLol.getSummonerName(usuario)
      if dados.status_code == 200:
        dados = dados.json()
        rankedDados = apiLol.getRankedStats(dados['id']).json()
        rankedDadosSolo = rankedDados[0]
        rankedDadosFlex = rankedDados[1]
        soloDuoStats =f"**{rankedDadosSolo.get('tier')} {rankedDadosSolo.get('rank')}**" 
        flexStats =f"**{rankedDadosFlex.get('tier')} {rankedDadosFlex.get('rank')}**"
        nomeUsuario = dados.get('name')
        idIcon = dados.get('profileIconId')
        urlImage = apiLol.getUrlProfileIcon(idIcon)

        #EmbedChanged
        embed_message.add_field(name="Solo/Duo",value=soloDuoStats)
        embed_message.add_field(name="Flex",value=flexStats)
        embed_message.set_thumbnail(url= urlImage)
        embed_message.title = f"🔷 │ **{nomeUsuario}**"
        embed_message.description = f"**Infomações sobre o jogador**"

      
      
      await interaction.channel.send(embed = embed_message)
      await interaction.response.send_message(embed=discord.Embed(description="Comando executado com sucesso!",color=interaction.guild.me.color),ephemeral=True,delete_after=4)

async def setup(client: commands.Bot):
    await client.add_cog(UsuarioLol(client))