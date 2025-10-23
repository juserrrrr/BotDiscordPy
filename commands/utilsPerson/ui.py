"""
Este arquivo define as views e botões do Discord para a criação de partidas personalizadas,
centralizando a lógica de interface do usuário em um único local.
"""
import discord
from discord import ui, app_commands
from typing import List

import asyncio
import logging

from base.BaseViews import BaseView

from .helpers import generate_league_embed_text, create_timbas_player, is_user_registered
from .lol import LeagueVerificationModal
from .services.player_service import PlayerService
from .services.match_service import MatchService
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
        self.blue_team = []  # Pode ser List[discord.User] ou List[dict]
        self.red_team = []  # Pode ser List[discord.User] ou List[dict]
        self.started = False
        self.match_id = None
        self.blue_team_id = None
        self.red_team_id = None
        self.finishing = False
        self.show_details = False  # Flag para mostrar posições
        self.original_voice_channels = {}  # Armazena o canal de voz original de cada jogador

        self.update_buttons()

    def update_buttons(self):
        """Atualiza o estado dos botões com base no estado da partida."""
        self.clear_items()

        if not self.started:
            # --- State: Before match starts ---
            self.add_item(JoinButton(self))
            self.add_item(LeaveButton(self))
            self.add_item(PlayerCountButton(self.confirmed_players))

            # Modos aleatórios (0 e 3) têm botão de sortear
            if self.match_format.value in [0, 3]:  # Aleatório ou Aleatório Completo
                self.add_item(DrawButton(self))
            elif self.match_format.value == 1:  # Livre
                self.add_item(SwitchSideButton(self))

            self.add_item(StartButton(self))
            self.add_item(FinishButton(self))
        else:
            # --- State: After match starts ---
            self.add_item(RejoinButton(self))
            self.add_item(FinishButton(self))

    async def update_embed(self, interaction: discord.Interaction, started=False, finished=False):
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
            online_mode=self.online_mode.name,
            show_details=self.show_details
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
        embed.set_image(url="attachment://timbasQueueGif.gif")

        await interaction.message.edit(embed=embed, view=self)


# --- Botões --- #

class JoinButton(ui.Button):
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Entrar", style=discord.ButtonStyle.green, emoji="✅", disabled=parent_view.started or len(parent_view.confirmed_players) >= 10)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user

        # Defer da interação imediatamente
        await interaction.response.defer(ephemeral=True)

        # Valida se o jogador está em um canal de voz
        is_valid, error_msg = PlayerService.validate_player_in_voice(user)
        if not is_valid:
            message = await interaction.followup.send(error_msg, ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return

        # Valida se o jogador já não está na lista
        is_valid, error_msg = PlayerService.validate_player_not_in_list(user, self.parent_view.confirmed_players)
        if not is_valid:
            message = await interaction.followup.send(error_msg, ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return

        # Valida se a partida não está cheia
        is_valid, error_msg = PlayerService.validate_match_not_full(self.parent_view.confirmed_players)
        if not is_valid:
            message = await interaction.followup.send(error_msg, ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return

        if self.parent_view.online_mode.value == 1:
            timbas = timbasService()
            response = timbas.getUserByDiscordId(user.id)
            user_data = response.json() if response else None

            if not user_data or not is_user_registered(response):
                confirm_view = AccountCreationConfirmView(user=user, original_interaction=interaction)
                await interaction.followup.send(
                    "Não encontramos uma conta Timbas vinculada ao seu Discord. Deseja criar uma agora? (O processo é automatico)",
                    view=confirm_view,
                    ephemeral=True
                )
                await confirm_view.wait()

                if not confirm_view.result:
                    return

        # Armazena o canal de voz original antes de mover
        PlayerService.store_original_channel(user, self.parent_view.original_voice_channels)

        # Move o jogador para o canal de espera
        await PlayerService.move_player_to_channel(user, self.parent_view.waiting_channel)

        self.parent_view.confirmed_players.append(user)
        self.parent_view.update_buttons()
        await self.parent_view.update_embed(interaction)

class LeaveButton(ui.Button):
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Sair", style=discord.ButtonStyle.red, emoji="🚪", disabled=parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        await interaction.response.defer(ephemeral=True)

        if user in self.parent_view.confirmed_players:
            self.parent_view.confirmed_players.remove(user)

            # Restaura o jogador para o canal original
            if user.voice and user.id in self.parent_view.original_voice_channels:
                original_channel = self.parent_view.original_voice_channels[user.id]
                await PlayerService.move_player_to_channel(user, original_channel)
                PlayerService.remove_original_channel(user.id, self.parent_view.original_voice_channels)

            self.parent_view.update_buttons()
            await self.parent_view.update_embed(interaction)
            message = await interaction.followup.send("Você saiu da lista de jogadores.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
        else:
            message = await interaction.followup.send("Você não está na lista.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()

class PlayerCountButton(ui.Button):
    def __init__(self, players: List[discord.User]):
        super().__init__(label=f"Confirmados: {len(players)}/10", style=discord.ButtonStyle.grey, disabled=True)

class DrawButton(ui.Button):
    """Botão para sortear os times (com ou sem posições e campeões)."""
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Sortear", style=discord.ButtonStyle.primary, emoji="🎲", disabled=len(parent_view.confirmed_players) < 10 or parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        if interaction.user != self.parent_view.creator:
            message = await interaction.followup.send("Apenas o criador pode sortear.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return

        # Realiza o sorteio usando MatchService
        blue_team, red_team, show_details = MatchService.perform_draw(
            self.parent_view.match_format.value,
            self.parent_view.confirmed_players
        )

        self.parent_view.blue_team = blue_team
        self.parent_view.red_team = red_team
        self.parent_view.show_details = show_details

        # Define mensagem baseada no modo
        if self.parent_view.match_format.value == 3:
            message_text = "Times e posições sorteados!"
        else:
            message_text = "Times sorteados!"

        self.parent_view.update_buttons()
        await self.parent_view.update_embed(interaction, started=False)
        message = await interaction.followup.send(message_text, ephemeral=True)
        await asyncio.sleep(5)
        await message.delete()

class SwitchSideButton(ui.Button):
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Trocar Lado", style=discord.ButtonStyle.primary, emoji="🔄", disabled=len(parent_view.confirmed_players) != 10 or parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        # Implementar a lógica de troca de lado se necessário
        message = await interaction.followup.send("Função ainda não implementada.", ephemeral=True)
        await asyncio.sleep(5)
        await message.delete()

class StartButton(ui.Button):
    def __init__(self, parent_view: CustomMatchView):
        is_ready = len(parent_view.confirmed_players) == 10
        super().__init__(label="Iniciar", style=discord.ButtonStyle.success, emoji="▶", disabled=not is_ready or parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async def delete_message_after_delay(msg):
            await asyncio.sleep(5)
            await msg.delete()

        if interaction.user != self.parent_view.creator:
            message = await interaction.followup.send("Apenas o criador pode iniciar.", ephemeral=True)
            asyncio.create_task(delete_message_after_delay(message))
            return

        # Valida se os times foram sorteados (para modos aleatórios)
        is_valid, error_msg = MatchService.validate_teams_drawn(
            self.parent_view.match_format.value,
            self.parent_view.blue_team,
            self.parent_view.red_team
        )
        if not is_valid:
            message = await interaction.followup.send(error_msg, ephemeral=True)
            asyncio.create_task(delete_message_after_delay(message))
            return

        # Prepara times para o modo Livre
        if self.parent_view.match_format.value == 1:
            blue_team, red_team = MatchService.prepare_free_mode_teams(self.parent_view.confirmed_players)
            self.parent_view.blue_team = blue_team
            self.parent_view.red_team = red_team

        # Cria partida na API (modo online)
        if self.parent_view.online_mode.value == 1:
            success, error_msg, match_id, blue_team_id, red_team_id = await MatchService.create_match_in_api(
                interaction.guild.id,
                self.parent_view.match_format.value,
                self.parent_view.blue_team,
                self.parent_view.red_team
            )

            if not success:
                message = await interaction.followup.send(error_msg, ephemeral=True)
                asyncio.create_task(delete_message_after_delay(message))
                return

            self.parent_view.match_id = match_id
            self.parent_view.blue_team_id = blue_team_id
            self.parent_view.red_team_id = red_team_id

            # Move jogadores para os canais dos times
            if (self.parent_view.blue_channel and self.parent_view.red_channel) and not self.parent_view.debug:
                blue_users = PlayerService.extract_users_from_team(self.parent_view.blue_team)
                red_users = PlayerService.extract_users_from_team(self.parent_view.red_team)
                await PlayerService.move_team_to_channel(blue_users, self.parent_view.blue_channel)
                await PlayerService.move_team_to_channel(red_users, self.parent_view.red_channel)

        self.parent_view.started = True
        self.parent_view.update_buttons()
        await self.parent_view.update_embed(interaction, started=True)

class FinishButton(ui.Button):
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Finalizar", style=discord.ButtonStyle.danger, emoji="🏁", disabled=not parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if interaction.user != self.parent_view.creator:
            message = await interaction.followup.send("Apenas o criador pode finalizar.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return

        if self.parent_view.online_mode.value == 0: # Offline
            # Restaura todos os jogadores para os canais originais
            if not self.parent_view.debug:
                await PlayerService.restore_players_to_original_channels(
                    self.parent_view.confirmed_players,
                    self.parent_view.original_voice_channels
                )

            await self.parent_view.update_embed(interaction, finished=True)
            self.parent_view.stop()
            return

        if self.parent_view.finishing:
            message = await interaction.followup.send("A seleção de vencedor já está em andamento.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return

        if not self.parent_view.match_id or not self.parent_view.blue_team_id or not self.parent_view.red_team_id:
            message = await interaction.followup.send("IDs da partida ou dos times não encontrados. Não é possível finalizar.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return

        # Desabilita o botão e atualiza a view principal
        self.disabled = True
        self.parent_view.finishing = True
        await interaction.message.edit(view=self.parent_view)

        # Envia a view de finalização como resposta efêmera à interação atual
        finish_view = FinishMatchView(self.parent_view, interaction.message)
        finish_view.message = await interaction.followup.send("Quem venceu a partida?", view=finish_view, ephemeral=True, wait=True)


class WinningTeamSelect(ui.Select):
    def __init__(self, parent_view: 'FinishMatchView'):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label="Time Azul", value=str(parent_view.match_view.blue_team_id), emoji="🔵"),
            discord.SelectOption(label="Time Vermelho", value=str(parent_view.match_view.red_team_id), emoji="🔴"),
        ]
        super().__init__(placeholder="Selecione o time vencedor...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # Defer da resposta para dar tempo ao bot de processar
        await interaction.response.defer(ephemeral=True)

        if interaction.user != self.parent_view.match_view.creator:
            return await interaction.followup.send("Apenas o criador da partida pode selecionar o vencedor.", ephemeral=True)

        winner_team_id = int(self.values[0])

        # Atualiza o vencedor da partida usando MatchService
        success, error_msg = await MatchService.update_match_winner(
            self.parent_view.match_view.match_id,
            winner_team_id
        )

        if not success:
            # Envia erro e reabilita o botão de finalizar
            await interaction.followup.send(error_msg, ephemeral=True)
            self.parent_view.match_view.finishing = False
            for item in self.parent_view.match_view.children:
                if isinstance(item, FinishButton):
                    item.disabled = False
                    break
            await self.parent_view.original_message.edit(view=self.parent_view.match_view)
            return

        # Marca que o vencedor foi selecionado
        self.parent_view.winner_selected = True

        # Obtém o lado vencedor e o rótulo
        winner_side = MatchService.get_winner_side(
            winner_team_id,
            self.parent_view.match_view.blue_team_id,
            self.parent_view.match_view.red_team_id
        )
        winner_label = MatchService.get_winner_label(winner_side)

        # Gera o novo corpo da embed com o troféu
        new_embed_text = generate_league_embed_text(
            blue_team=self.parent_view.match_view.blue_team,
            red_team=self.parent_view.match_view.red_team,
            match_format=self.parent_view.match_view.match_format.name,
            online_mode=self.parent_view.match_view.online_mode.name,
            winner=winner_side,
            show_details=self.parent_view.match_view.show_details
        )

        # Cria uma embed totalmente nova para evitar problemas de referência
        final_embed = discord.Embed(
            description=f"```{new_embed_text}```",
            color=discord.Color.blue()
        )
        final_embed.set_footer(text=f"Partida finalizada! Vencedor: Time {winner_label}")
        final_embed.set_image(url="attachment://timbasQueueGif.gif")

        # Restaura todos os jogadores para os canais originais
        if not self.parent_view.match_view.debug:
            await PlayerService.restore_players_to_original_channels(
                self.parent_view.match_view.confirmed_players,
                self.parent_view.match_view.original_voice_channels
            )

        # Edita a mensagem original com a nova embed
        await self.parent_view.original_message.edit(embed=final_embed, view=None)

        self.parent_view.match_view.stop()

        # Deleta a mensagem de seleção (que é a resposta original a esta interação)
        await interaction.delete_original_response()


class FinishMatchView(BaseView):
    def __init__(self, match_view: CustomMatchView, original_message: discord.Message):
        super().__init__(timeout=180) # 3 minutos para decidir
        self.match_view = match_view
        self.original_message = original_message
        self.message: discord.WebhookMessage = None
        self.winner_selected = False
        self.add_item(WinningTeamSelect(self))

    async def on_timeout(self):
        # Se já foi selecionado vencedor, não faz nada
        if self.winner_selected or self.match_view.is_finished():
            return

        # Re-habilita o botão de finalizar internamente
        self.match_view.finishing = False
        for item in self.match_view.children:
            if isinstance(item, FinishButton):
                item.disabled = False
                break

        # Restaura os botões na mensagem original
        try:
            # Busca a mensagem novamente pelo ID para garantir existência
            channel = self.original_message.channel
            message = await channel.fetch_message(self.original_message.id)
            # Atualiza apenas a view, mantendo embed e conteúdo
            await message.edit(view=self.match_view)
        except:
            # Se falhar por qualquer motivo, não faz nada
            # A mensagem original permanece intacta
            pass

        # Apaga apenas a mensagem efêmera de seleção de vencedor
        if self.message:
            try:
                await self.message.delete()
            except:
                pass
            

class RejoinButton(ui.Button):
    """Botão para retornar ao canal de voz da equipe."""
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Voltar para a Sala", style=discord.ButtonStyle.secondary, emoji="🔄")
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        await interaction.response.defer(ephemeral=True)

        # Valida se o jogador está em um canal de voz
        is_valid, error_msg = PlayerService.validate_player_in_voice(user)
        if not is_valid:
            message = await interaction.followup.send(error_msg, ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return

        # Obtém o canal do time do jogador
        channel = PlayerService.get_player_team_channel(
            user,
            self.parent_view.blue_team,
            self.parent_view.red_team,
            self.parent_view.blue_channel,
            self.parent_view.red_channel
        )

        if channel:
            await PlayerService.move_player_to_channel(user, channel)
            team_name = "Azul" if channel == self.parent_view.blue_channel else "Vermelho"
            message = await interaction.followup.send(f"Você foi movido para o canal do Time {team_name}.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
        else:
            message = await interaction.followup.send("Você não faz parte desta partida.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()


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
            content="⌛ Criando sua conta Timbas, por favor aguarde...",
            view=None
        )
        
        create_response = await create_timbas_player(self.user, None)

        async def delete_message_later(interaction: discord.Interaction, delay: int):
            await asyncio.sleep(delay)
            await interaction.delete_original_response()

        if create_response.status_code != 201:
            await interaction.edit_original_response(
                content="❌ Ocorreu um erro ao criar sua conta. Tente novamente."
            )
            self.result = False
            asyncio.create_task(delete_message_later(interaction, 5))
        else:
            await interaction.edit_original_response(
                content="✅ Conta criada com sucesso!"
            )
            self.result = True
            asyncio.create_task(delete_message_later(interaction, 2))
            
        self.stop()

    @ui.button(label="Não, obrigado", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(
            content="É necessário ter uma conta Timbas para participar de partidas online.",
            view=None
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