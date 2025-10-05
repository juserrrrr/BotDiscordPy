"""
Este arquivo define as views e botões do Discord para a criação de partidas personalizadas,
centralizando a lógica de interface do usuário em um único local.
"""
import discord
from discord import ui, app_commands
from typing import List

import asyncio

from base.BaseViews import BaseView

from .helpers import draw_teams, move_team_to_channel, generate_league_embed_text, create_timbas_player, is_user_registered
from .lol import LeagueVerificationModal
from services.timbasService import timbasService


class CustomMatchView(BaseView):
    """View principal para gerenciar uma partida personalizada."""

    def __init__(self, creator: discord.User, waiting_channel: discord.VoiceChannel, blue_channel: discord.VoiceChannel, red_channel: discord.VoiceChannel, online_mode: app_commands.Choice[int], match_format: app_commands.Choice[int], debug: bool = False):
        super().__init__(timeout=None)  # A view persiste
        self.creator = creator
        self.waiting_channel = waiting_channel
        self.blue_channel = blue_channel
        self.red_channel = red_channel
        self.online_mode = online_mode
        self.match_format = match_format
        self.debug = debug
        self.confirmed_players: List[discord.User] = []
        self.blue_team: List[discord.User] = []
        self.red_team: List[discord.User] = []
        self.started = False
        self.match_id = None
        self.blue_team_id = None
        self.red_team_id = None
        self.message_interaction = None
        self.finishing = False

        self.update_buttons()

    def update_buttons(self):
        """Atualiza o estado dos botões com base no estado da partida."""
        self.clear_items()

        if not self.started:
            # --- State: Before match starts ---
            self.add_item(JoinButton(self))
            self.add_item(LeaveButton(self))
            self.add_item(PlayerCountButton(self.confirmed_players))

            if self.match_format.value == 0:  # Aleatório
                self.add_item(DrawButton(self))
            elif self.match_format.value == 1:  # Livre
                self.add_item(SwitchSideButton(self))

            self.add_item(StartButton(self))
            self.add_item(FinishButton(self))
        else:
            # --- State: After match starts ---
            self.add_item(RejoinButton(self))
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
        super().__init__(label="Entrar", style=discord.ButtonStyle.green, emoji="✅", disabled=parent_view.started or len(parent_view.confirmed_players) >= 10)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        if not user.voice:
            return await interaction.response.send_message("Você precisa estar em um canal de voz.", ephemeral=True, delete_after=5)
        
        if user in self.parent_view.confirmed_players:
            return await interaction.response.send_message("Você já está na lista.", ephemeral=True, delete_after=5)

        if len(self.parent_view.confirmed_players) >= 10:
            return await interaction.response.send_message("A partida já está cheia.", ephemeral=True, delete_after=5)

        if self.parent_view.online_mode.value == 1:
            timbas = timbasService()
            response = timbas.getUserByDiscordId(user.id)
            user_data = response.json() if response else None

            if not user_data or not is_user_registered(response):
                confirm_view = AccountCreationConfirmView(user=user, original_interaction=interaction)
                await interaction.response.send_message(
                    "Não encontramos uma conta Timbas vinculada ao seu Discord. Deseja criar uma agora?",
                    view=confirm_view,
                    ephemeral=True
                )
                await confirm_view.wait()

                if not confirm_view.result:
                    return
                

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
            await interaction.response.send_message("Você não está na lista.", ephemeral=True, delete_after=5)

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
            return await interaction.response.send_message("Apenas o criador pode sortear.", ephemeral=True, delete_after=5)

        self.parent_view.blue_team, self.parent_view.red_team = draw_teams(self.parent_view.confirmed_players)
        self.parent_view.update_buttons()
        await self.parent_view.update_embed(interaction, started=False)

class SwitchSideButton(ui.Button):
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Trocar Lado", style=discord.ButtonStyle.primary, emoji="🔄", disabled=len(parent_view.confirmed_players) != 10 or parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # Implementar a lógica de troca de lado se necessário
        await interaction.response.send_message("Função ainda não implementada.", ephemeral=True, delete_after=5)

class StartButton(ui.Button):
    def __init__(self, parent_view: CustomMatchView):
        is_ready = len(parent_view.confirmed_players) == 10
        super().__init__(label="Iniciar", style=discord.ButtonStyle.success, emoji="▶", disabled=not is_ready or parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user != self.parent_view.creator:
            await interaction.followup.send("Apenas o criador pode iniciar.", ephemeral=True, delete_after=5)
            return

        if self.parent_view.match_format.value == 0 and not (self.parent_view.blue_team and self.parent_view.red_team):
            await interaction.followup.send("Sorteie os times primeiro.", ephemeral=True, delete_after=5)
            return
        
        if self.parent_view.match_format.value == 1: # Modo Livre
            half = len(self.parent_view.confirmed_players) // 2
            self.parent_view.blue_team = self.parent_view.confirmed_players[:half]
            self.parent_view.red_team = self.parent_view.confirmed_players[half:]

        # Criar a partida na API Timbas ou simular em modo debug
        if self.parent_view.debug:
            # Simula a criação de IDs em modo debug
            self.parent_view.match_id = 9999
            self.parent_view.blue_team_id = 101
            self.parent_view.red_team_id = 102
        elif self.parent_view.online_mode.value == 1:
            timbas = timbasService()
            payload = {
                "ServerDiscordId": str(interaction.guild.id),
                "teamBlue": {
                    "players": [{ "discordId": str(p.id) } for p in self.parent_view.blue_team]
                },
                "teamRed": {
                    "players": [{ "discordId": str(p.id) } for p in self.parent_view.red_team]
                }
            }
            response = timbas.createMatch(payload)
            if response.status_code == 201:
                match_data = response.json()
                self.parent_view.match_id = match_data.get('id')
                if 'teamBlue' in match_data and 'id' in match_data['teamBlue']:
                    self.parent_view.blue_team_id = match_data['teamBlue']['id']
                if 'teamRed' in match_data and 'id' in match_data['teamRed']:
                    self.parent_view.red_team_id = match_data['teamRed']['id']

                if not self.parent_view.match_id or not self.parent_view.blue_team_id or not self.parent_view.red_team_id:
                    await interaction.followup.send("Erro: A resposta da API não continha os IDs necessários.", ephemeral=True, delete_after=5)
                    return
            else:
                await interaction.followup.send(f"Erro ao criar a partida na API: {response.text}", ephemeral=True, delete_after=5)
                return

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
            return await interaction.response.send_message("Apenas o criador pode finalizar.", ephemeral=True, delete_after=5)

        if self.parent_view.online_mode.value == 0: # Offline
            await self.parent_view.update_embed(interaction, finished=True)
            self.parent_view.stop()
            return

        if self.parent_view.finishing:
            return await interaction.response.send_message("A seleção de vencedor já está em andamento.", ephemeral=True, delete_after=5)

        if not self.parent_view.match_id or not self.parent_view.blue_team_id or not self.parent_view.red_team_id:
            return await interaction.response.send_message("IDs da partida ou dos times não encontrados. Não é possível finalizar.", ephemeral=True, delete_after=5)

        # Desabilita o botão e atualiza a view principal
        self.disabled = True
        self.parent_view.finishing = True
        await self.parent_view.message_interaction.edit_original_response(view=self.parent_view)

        # Envia a view de finalização como resposta efêmera à interação atual
        finish_view = FinishMatchView(self.parent_view)
        await interaction.response.send_message("Quem venceu a partida?", view=finish_view, ephemeral=True)
        finish_view.message = await interaction.original_response()


class WinningTeamSelect(ui.Select):
    def __init__(self, parent_view: 'FinishMatchView'):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label="Time Azul", value=str(parent_view.match_view.blue_team_id), emoji="🔵"),
            discord.SelectOption(label="Time Vermelho", value=str(parent_view.match_view.red_team_id), emoji="🔴"),
        ]
        super().__init__(placeholder="Selecione o time vencedor...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # Deferir a resposta para dar tempo ao bot de processar
        await interaction.response.defer(ephemeral=True)

        if interaction.user != self.parent_view.match_view.creator:
            return await interaction.followup.send("Apenas o criador da partida pode selecionar o vencedor.", ephemeral=True)

        winner_team_id = int(self.values[0])
        
        response_ok = False
        if self.parent_view.match_view.debug:
            response_ok = True
        else:
            timbas = timbasService()
            payload = {"winnerId": winner_team_id}
            response = timbas.updateMatchWinner(self.parent_view.match_view.match_id, payload)
            if response.status_code == 200:
                response_ok = True
            else:
                # Usa followup para enviar o erro
                await interaction.followup.send(f"Erro ao finalizar a partida: {response.text}", ephemeral=True)
                # Re-habilita o botão em caso de erro
                self.parent_view.match_view.finishing = False
                for item in self.parent_view.match_view.children:
                    if isinstance(item, FinishButton):
                        item.disabled = False
                        break
                await self.parent_view.match_view.message_interaction.edit_original_response(view=self.parent_view.match_view)

        if response_ok:
            winner_side = 'BLUE' if winner_team_id == self.parent_view.match_view.blue_team_id else 'RED'
            winner_label = "Azul" if winner_side == 'BLUE' else "Vermelho"

            # Gera o novo corpo da embed com o troféu
            new_embed_text = generate_league_embed_text(
                blue_team=self.parent_view.match_view.blue_team,
                red_team=self.parent_view.match_view.red_team,
                match_format=self.parent_view.match_view.match_format.name,
                online_mode=self.parent_view.match_view.online_mode.name,
                winner=winner_side
            )
            
            # Cria uma embed totalmente nova para evitar problemas de referência
            final_embed = discord.Embed(
                description=f"```{new_embed_text}```",
                color=discord.Color.blue() # ou a cor original
            )
            final_embed.set_footer(text=f"Partida finalizada! Vencedor: Time {winner_label}")
            final_embed.set_image(url="attachment://timbasQueue.png")

            # Edita a mensagem original com a nova embed
            original_interaction = self.parent_view.match_view.message_interaction
            await original_interaction.edit_original_response(embed=final_embed, view=None)

            self.parent_view.match_view.stop()
        
        # Deleta a mensagem de seleção (que é a resposta original a esta interação)
        await interaction.delete_original_response()


class FinishMatchView(BaseView):
    def __init__(self, match_view: CustomMatchView):
        super().__init__(timeout=180) # 3 minutos para decidir
        self.match_view = match_view
        self.message: discord.WebhookMessage = None
        self.add_item(WinningTeamSelect(self))

    async def on_timeout(self):
        if self.match_view.is_finished():
            return

        # Re-habilita o botão de finalizar na view principal
        self.match_view.finishing = False
        for item in self.match_view.children:
            if isinstance(item, FinishButton):
                item.disabled = False
                break
        
        try:
            await self.match_view.message_interaction.edit_original_response(view=self.match_view)
        except discord.errors.NotFound:
            pass # A interação original pode ter expirado.

        if self.message:
            await self.message.delete()
            

class RejoinButton(ui.Button):
    """Botão para retornar ao canal de voz da equipe."""
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Voltar para a Sala", style=discord.ButtonStyle.secondary, emoji="🔄")
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        if not user.voice:
            return await interaction.response.send_message("Você precisa estar em um canal de voz para ser movido.", ephemeral=True, delete_after=5)

        if user in self.parent_view.blue_team:
            await user.move_to(self.parent_view.blue_channel)
            await interaction.response.send_message("Você foi movido para o canal do Time Azul.", ephemeral=True, delete_after=5)
        elif user in self.parent_view.red_team:
            await user.move_to(self.parent_view.red_channel)
            await interaction.response.send_message("Você foi movido para o canal do Time Vermelho.", ephemeral=True, delete_after=5)
        else:
            await interaction.response.send_message("Você não faz parte desta partida.", ephemeral=True, delete_after=5)


class AccountCreationConfirmView(BaseView):
    """View para confirmar a criação de conta para o usuário."""
    def __init__(self, user: discord.User, original_interaction: discord.Interaction):
        super().__init__(timeout=60) 
        self.user = user
        self.original_interaction = original_interaction
        self.result = None 

    async def on_timeout(self):
        self.result = None
        self.stop()

    @ui.button(label="Sim, criar conta", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(
            content="⌛ Criando sua conta Timbas, por favor aguarde..."
        )
        
        create_response = await create_timbas_player(self.user, None)

        await interaction.delete_original_response()

        if create_response.status_code != 201:
            msg = await interaction.followup.send(
                "❌ Ocorreu um erro ao criar sua conta. Tente novamente.",
                ephemeral=True
            )
            self.result = False
            await asyncio.sleep(5)
            await msg.delete()

        else:
            msg = await interaction.followup.send(
                "✅ Conta criada com sucesso!",
                ephemeral=True
            )
            self.result = True
            await asyncio.sleep(5)
            await msg.delete()
            
        self.stop()

    @ui.button(label="Não, obrigado", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(
            content="É necessário ter uma conta Timbas para participar de partidas online.",
            view=None,
            delete_after=5
        )
        self.result = False
        self.stop()


class ConfirmChannelCreationView(BaseView):
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