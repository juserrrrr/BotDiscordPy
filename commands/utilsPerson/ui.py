"""
Este arquivo define as views e botões do Discord para a criação de partidas personalizadas,
centralizando a lógica de interface do usuário em um único local.
"""
import discord
from discord import ui, app_commands
from typing import List, Callable

from .helpers import draw_teams, move_team_to_channel, generate_league_embed_text
from .lol import LeagueVerificationModal
from services.timbasService import timbasService


class CustomMatchView(ui.View):
    """View principal para gerenciar uma partida personalizada."""

    def __init__(self, creator: discord.User, waiting_channel: discord.VoiceChannel, blue_channel: discord.VoiceChannel, red_channel: discord.VoiceChannel, online_mode: app_commands.Choice[int], match_format: app_commands.Choice[int]):
        super().__init__(timeout=None)  # A view persiste
        self.creator = creator
        self.waiting_channel = waiting_channel
        self.blue_channel = blue_channel
        self.red_channel = red_channel
        self.online_mode = online_mode
        self.match_format = match_format
        self.confirmed_players: List[discord.User] = []
        self.blue_team: List[discord.User] = []
        self.red_team: List[discord.User] = []
        self.started = False

        self.update_buttons()

    def update_buttons(self):
        """Atualiza o estado dos botões com base no estado da partida."""
        # Limpa os botões antigos para redesenhar
        self.clear_items()

        # Botões de Ação
        self.add_item(JoinButton(self))
        self.add_item(LeaveButton(self))
        self.add_item(PlayerCountButton(self.confirmed_players))

        # Botões de Controle (dependem do formato e estado)
        if self.match_format.value == 0:  # Aleatório
            self.add_item(DrawButton(self))
        elif self.match_format.value == 1:  # Livre
            self.add_item(SwitchSideButton(self))

        self.add_item(StartButton(self))
        self.add_item(FinishButton(self))

    async def update_embed(self, interaction: discord.Interaction, started=False, finished=False, deferred: bool = False):
        """Atualiza o embed da partida."""
        if not self.blue_team and not self.red_team:
            blue_display = self.confirmed_players[:5]
            red_display = self.confirmed_players[5:]
        else:
            blue_display = self.blue_team
            red_display = self.red_team

        text = generate_league_embed_text(
            blue_team=blue_display,
            red_team=red_display,
            match_format=self.match_format.name,
            online_mode=self.online_mode.name
        )

        embed = discord.Embed(description=f"```{text}```", color=discord.Color.blue())
        
        footer_text = "Aguardando jogadores..."
        if finished:
            footer_text = "Partida finalizada!"
        elif started:
            footer_text = "Partida em andamento!"
        elif len(self.confirmed_players) >= 10:
            footer_text = "Pronto para começar!"

        embed.set_footer(text=footer_text)
        embed.set_image(url="attachment://timbasQueue.png")
        
        if deferred:
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)


# --- Botões --- #

class JoinButton(ui.Button):
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Entrar", style=discord.ButtonStyle.green, emoji="✅", disabled=parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        if not user.voice:
            return await interaction.response.send_message("Você precisa estar em um canal de voz.", ephemeral=True)
        
        if user in self.parent_view.confirmed_players:
            return await interaction.response.send_message("Você já está na lista.", ephemeral=True)

        if self.parent_view.online_mode.value == 1:
            timbas = timbasService()
            response = timbas.getUserByDiscordId(user.id)
            if not response or not response.json().get('leaguePuuid'):
                await interaction.response.send_modal(LeagueVerificationModal())
                return

        self.parent_view.confirmed_players.append(user)
        await user.move_to(self.parent_view.waiting_channel)
        self.parent_view.update_buttons()
        await self.parent_view.update_embed(interaction)

class LeaveButton(ui.Button):
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Sair", style=discord.ButtonStyle.red, emoji="🚪", disabled=parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        if user in self.parent_view.confirmed_players:
            self.parent_view.confirmed_players.remove(user)
            self.parent_view.update_buttons()
            await self.parent_view.update_embed(interaction)
        else:
            await interaction.response.send_message("Você não está na lista.", ephemeral=True)

class PlayerCountButton(ui.Button):
    def __init__(self, players: List[discord.User]):
        super().__init__(label=f"{len(players)}/10", style=discord.ButtonStyle.grey, disabled=True)

class DrawButton(ui.Button):
    """Botão para sortear os times."""
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Sortear", style=discord.ButtonStyle.primary, emoji="🎲", disabled=len(parent_view.confirmed_players) < 10 or parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.parent_view.creator:
            return await interaction.response.send_message("Apenas o criador pode sortear.", ephemeral=True)

        self.parent_view.blue_team, self.parent_view.red_team = draw_teams(self.parent_view.confirmed_players)
        self.parent_view.update_buttons()
        await self.parent_view.update_embed(interaction, started=False)

class SwitchSideButton(ui.Button):
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Trocar Lado", style=discord.ButtonStyle.primary, emoji="🔄", disabled=len(parent_view.confirmed_players) != 10 or parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # Implementar a lógica de troca de lado se necessário
        await interaction.response.send_message("Função ainda não implementada.", ephemeral=True)

class StartButton(ui.Button):
    def __init__(self, parent_view: CustomMatchView):
        is_ready = len(parent_view.confirmed_players) == 10
        super().__init__(label="Iniciar", style=discord.ButtonStyle.success, emoji="▶", disabled=not is_ready or parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user != self.parent_view.creator:
            await interaction.followup.send("Apenas o criador pode iniciar.", ephemeral=True)
            return

        if self.parent_view.match_format.value == 0 and not (self.parent_view.blue_team and self.parent_view.red_team):
            await interaction.followup.send("Sorteie os times primeiro.", ephemeral=True)
            return
        
        if self.parent_view.match_format.value == 1: # Modo Livre
            half = len(self.parent_view.confirmed_players) // 2
            self.parent_view.blue_team = self.parent_view.confirmed_players[:half]
            self.parent_view.red_team = self.parent_view.confirmed_players[half:]

        await move_team_to_channel(self.parent_view.blue_team, self.parent_view.blue_channel)
        await move_team_to_channel(self.parent_view.red_team, self.parent_view.red_channel)
        
        self.parent_view.started = True
        self.parent_view.update_buttons()
        await self.parent_view.update_embed(interaction, started=True, deferred=True)

class FinishButton(ui.Button):
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Finalizar", style=discord.ButtonStyle.danger, emoji="🏁", disabled=not parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.parent_view.creator:
            return await interaction.response.send_message("Apenas o criador pode finalizar.", ephemeral=True)
        
        # Lógica de finalização (ex: mover todos para um canal, registrar resultados)
        self.parent_view.update_buttons()
        await self.parent_view.update_embed(interaction, finished=True)
        self.parent_view.stop() # Termina a view


class ConfirmChannelCreationView(ui.View):
    """View para confirmar a criação dos canais de voz necessários."""
    def __init__(self):
        super().__init__(timeout=60)
        self.result = None

    @ui.button(label="Sim, criar canais", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        self.result = True
        self.stop()
        await interaction.response.defer()

    @ui.button(label="Não, cancelar", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        self.result = False
        self.stop()
        await interaction.response.defer()