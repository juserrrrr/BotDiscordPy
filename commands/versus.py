import discord
from discord import app_commands
from discord.ext import commands
import asyncio

from services.timbasService import timbasService


class Versus(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name='versus', description="Compara as estatísticas de dois jogadores do servidor.")
    @app_commands.guild_only()
    @app_commands.describe(
        jogador1="Primeiro jogador.",
        jogador2="Segundo jogador."
    )
    async def versus(self, interaction: discord.Interaction, jogador1: discord.Member, jogador2: discord.Member):
        await interaction.response.defer()

        if jogador1.id == jogador2.id:
            msg = await interaction.followup.send("Selecione dois jogadores diferentes.", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()
            return

        timbas = timbasService()
        server_id = str(interaction.guild.id)

        # Busca o ranking completo do servidor e encontra os dois jogadores
        response = timbas.getRanking(server_id)

        if response is None or response.status_code != 200:
            msg = await interaction.followup.send("Não foi possível obter os dados do servidor.", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()
            return

        ranking_data = response.json()

        # Tenta encontrar os jogadores pelo nome do Discord
        def find_player(members_name: str):
            for p in ranking_data:
                if p.get('name', '').lower() == members_name.lower():
                    return p
            return None

        p1_data = find_player(jogador1.name)
        p2_data = find_player(jogador2.name)

        # Fallback: tenta buscar individualmente pelo Discord ID
        if not p1_data:
            r1 = timbas.getUserByDiscordId(str(jogador1.id))
            if r1 and r1.status_code == 200:
                p1_data = r1.json()

        if not p2_data:
            r2 = timbas.getUserByDiscordId(str(jogador2.id))
            if r2 and r2.status_code == 200:
                p2_data = r2.json()

        def extract_stats(data):
            if not data:
                return None
            wins = data.get('wins', 0)
            losses = data.get('losses', 0)
            total = data.get('totalGames', wins + losses)
            win_rate = data.get('winRate', (wins / total) if total > 0 else 0)
            if win_rate > 1:
                win_rate = win_rate / 100
            return {
                'name': data.get('name') or data.get('username') or 'N/A',
                'wins': wins,
                'losses': losses,
                'total': total,
                'win_rate': win_rate * 100,
            }

        s1 = extract_stats(p1_data)
        s2 = extract_stats(p2_data)

        if not s1 and not s2:
            msg = await interaction.followup.send("Nenhum dos jogadores possui estatísticas registradas.", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()
            return

        # Nomes de exibição
        name1 = (s1['name'] if s1 else jogador1.display_name)[:12]
        name2 = (s2['name'] if s2 else jogador2.display_name)[:12]

        def stat_or_dash(stats, key):
            if stats is None:
                return '-'
            return str(stats[key])

        def wr_or_dash(stats):
            if stats is None:
                return '-'
            return f"{stats['win_rate']:.1f}%"

        def winner_icon(v1, v2, higher_is_better=True):
            if v1 is None or v2 is None:
                return ' '
            if higher_is_better:
                if v1 > v2:
                    return '<'
                elif v2 > v1:
                    return '>'
            return '='

        w_icon = winner_icon(
            s1['wins'] if s1 else None,
            s2['wins'] if s2 else None
        )
        wr_icon = winner_icon(
            s1['win_rate'] if s1 else None,
            s2['win_rate'] if s2 else None
        )
        t_icon = winner_icon(
            s1['total'] if s1 else None,
            s2['total'] if s2 else None
        )
        l_icon = winner_icon(
            s1['losses'] if s1 else None,
            s2['losses'] if s2 else None,
            higher_is_better=False
        )

        col = 12
        separator = '─' * (col * 2 + 13)

        lines = [
            f"{'':^{col}}  {'VS':^7}  {'':^{col}}",
            f"{name1:^{col}}  {'   ':^7}  {name2:^{col}}",
            separator,
            f"{'Vitórias':^{col}}  {w_icon:^7}  {'Vitórias':^{col}}",
            f"{stat_or_dash(s1,'wins'):^{col}}  {'   ':^7}  {stat_or_dash(s2,'wins'):^{col}}",
            separator,
            f"{'Derrotas':^{col}}  {l_icon:^7}  {'Derrotas':^{col}}",
            f"{stat_or_dash(s1,'losses'):^{col}}  {'   ':^7}  {stat_or_dash(s2,'losses'):^{col}}",
            separator,
            f"{'Total':^{col}}  {t_icon:^7}  {'Total':^{col}}",
            f"{stat_or_dash(s1,'total'):^{col}}  {'   ':^7}  {stat_or_dash(s2,'total'):^{col}}",
            separator,
            f"{'WinRate':^{col}}  {wr_icon:^7}  {'WinRate':^{col}}",
            f"{wr_or_dash(s1):^{col}}  {'   ':^7}  {wr_or_dash(s2):^{col}}",
        ]

        # Rodapé com o vencedor geral
        if s1 and s2:
            if s1['win_rate'] > s2['win_rate']:
                footer = f"Melhor WinRate: {name1}"
            elif s2['win_rate'] > s1['win_rate']:
                footer = f"Melhor WinRate: {name2}"
            else:
                footer = "WinRates iguais"
        else:
            footer = "Dados incompletos"

        embed = discord.Embed(
            title=f"⚔️  {name1}  vs  {name2}",
            description="```\n" + "\n".join(lines) + "\n```",
            color=discord.Color.purple()
        )
        embed.set_footer(text=footer)
        embed.set_thumbnail(url=jogador1.display_avatar.url)

        await interaction.followup.send(embed=embed)


async def setup(client):
    await client.add_cog(Versus(client))
