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
                msg = await interaction.followup.send(f"Não foi possível obter o ranking. Erro: {response.text}", ephemeral=True)
                await msg.delete(delay=5)
                return

            ranking_data = response.json()
        
        if not ranking_data:
            msg = await interaction.followup.send("Ainda não há jogadores no ranking deste servidor.", ephemeral=True)
            await msg.delete(delay=5)
            return

        embed = discord.Embed(
            title="🏆 Ranking de Jogadores 🏆",
            color=discord.Color.gold()
        )

        # Mimic the header lines from generate_league_embed_text
        # Total width of the code block is around 45 characters.
        header_lines = [
            f"{'   -----':<21}{'TOP 10':^9}{'-----   ':>21}", # 45 chars
            f"{'':<9}{'Melhores do Servidor':^27}{'':>9}", # 45 chars
            "", # Empty line for spacing
            f"{'Pos.':<4}{'Jogador':<15}{'V/D':<8}{'WR':<8}{'Total':<10}", # Column headers (4+15+8+8+10 = 45)
            "---------------------------------------------" # 45 chars
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
            emoji_prefix = ""
            match rank:
                case 1: emoji_prefix = "🥇"
                case 2: emoji_prefix = "🥈"
                case 3: emoji_prefix = "🥉"
            
            # Truncate player name if too long
            display_name = player_name
            if len(display_name) > 15:
                display_name = display_name[:12] + "..." # 15 chars total

            ranking_list_lines.append(
                f"{emoji_prefix}{rank_str:<4}{display_name:<15}{f'{wins}/{losses}':<8}{f'{win_rate:.1f}%':<8}{total_games:<10}"
            )

        embed.description = "```\n" + "\n".join(header_lines + ranking_list_lines) + "\n```"
        embed.set_footer(text="Os melhores jogadores do servidor com base nas partidas personalizadas.")

        await interaction.followup.send(embed=embed)

async def setup(client):
    await client.add_cog(Ranking(client))