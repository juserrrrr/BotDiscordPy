import discord
from discord import app_commands
from discord.ext import commands

from services.timbasService import timbasService

class Ranking(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name='ranking', description="Mostra o ranking dos 10 melhores jogadores do servidor.")
    @app_commands.guild_only()
    @app_commands.describe(debug="Ativa o modo de debug para gerar um ranking com 10 jogadores falsos.")
    async def ranking(self, interaction: discord.Interaction, debug: bool = False):
        await interaction.response.defer()

        if debug:
            if interaction.user.id != interaction.guild.owner_id:
                return await interaction.followup.send("Você não tem permissão para usar o modo de debug.", ephemeral=True, delete_after=5)
            
            # Gerar 10 jogadores mocados
            from random import randint, uniform
            ranking_data = []
            for i in range(1, 11):
                wins = randint(10, 50)
                losses = randint(5, 30)
                ranking_data.append({
                    'rank': i,
                    'name': f'DebugPlayer{i}',
                    'wins': wins,
                    'losses': losses,
                    'winRate': wins / (wins + losses)
                })
        else:
            timbas = timbasService()
            server_id = str(interaction.guild.id)
            response = timbas.getRanking(server_id)

            if response.status_code != 200:
                return await interaction.followup.send(f"Não foi possível obter o ranking. Erro: {response.text}", ephemeral=True, delete_after=5)

            ranking_data = response.json()
        
        if not ranking_data:
            return await interaction.followup.send("Ainda não há jogadores no ranking deste servidor.", ephemeral=True, delete_after=5)

        embed = discord.Embed(
            title=f"🏆 Ranking de {interaction.guild.name}",
            color=discord.Color.gold()
        )

        description = ""
        for i, player_stats in enumerate(ranking_data):
            rank = player_stats.get('rank', i + 1)
            player_name = player_stats.get('name', 'N/A')
            wins = player_stats.get('wins', 0)
            losses = player_stats.get('losses', 0)
            win_rate = player_stats.get('winRate', 0) * 100

            emoji = ""
            match rank:
                case 1: emoji = "🥇"
                case 2: emoji = "🥈"
                case 3: emoji = "🥉"
                case _: emoji = f"**#{rank}**"

            description += f"{emoji} **{player_name}** (V: {wins} / D: {losses} | {win_rate:.1f}% WR)\n"

        embed.description = description
        embed.set_footer(text="Os melhores jogadores do servidor com base nas partidas personalizadas.")

        await interaction.followup.send(embed=embed)

async def setup(client):
    await client.add_cog(Ranking(client))