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
            
            from random import randint
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
                msg = await interaction.followup.send(f"Não foi possível obter o ranking. Erro: {response.text}", ephemeral=True)
                await msg.delete(delay=5)
                return

            ranking_data = response.json()
        
        if not ranking_data:
            msg = await interaction.followup.send("Ainda não há jogadores no ranking deste servidor.", ephemeral=True)
            await msg.delete(delay=5)
            return
        
        total_width = 45
        line1 = '----- TOP 10 -----'
        line2 = 'Melhores do Servidor'

        embed = discord.Embed(
            title="🏆 Ranking de Jogadores 🏆",
            color=discord.Color.gold()
        )
        header_lines = [
            f"{line1:^{total_width}}",
            f"{line2:^{total_width}}",
            "",
            # Ajuste a largura da coluna 'Pos.' para 5
            f"{'Pos.':<5}{'Jogador':<15}{'V/D':<8}{'Total':<6}{'WR':<8}",
            "---------------------------------------------"
        ]

        ranking_list_lines = []
        for i, player_stats in enumerate(ranking_data):
            rank = player_stats.get('rank', i + 1)
            player_name = player_stats.get('name', 'N/A')
            wins = player_stats.get('wins', 0)
            losses = player_stats.get('losses', 0)
            win_rate = player_stats.get('winRate', 0) * 100
            total_games = player_stats.get('totalGames', 0)

            rank_str = f"{rank}."
            
            # rjust(3) garante que " 1." e "10." tenham 3 caracteres de largura
            pos_column = rank_str.rjust(3) 

            medal = ""
            match rank:
                case 1: medal = " 🥇"
                case 2: medal = " 🥈"
                case 3: medal = " 🥉"

            display_name = player_name
            if len(display_name) > 15:
                display_name = display_name[:12] + "..."

            # Ajuste a largura da coluna 'pos_column' para 5.
            # pos_column (3 caracteres) + 2 espaços = 5 caracteres no total.
            main_line = f"{pos_column:<5}{display_name:<15}{f'{wins}/{losses}':<8}{total_games:<6}{f'{win_rate:.1f}%':<8}"
            
            full_line = f"{main_line}{medal}"
            
            ranking_list_lines.append(full_line)

        embed.description = "```\n" + "\n".join(header_lines + ranking_list_lines) + "\n```"
        embed.set_footer(text="Os melhores jogadores do servidor com base nas partidas personalizadas.")

        await interaction.followup.send(embed=embed)

async def setup(client):
    await client.add_cog(Ranking(client))