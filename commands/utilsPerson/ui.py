"""
Este arquivo define as views e botões do Discord para a criação de partidas personalizadas,
centralizando a lógica de interface do usuário em um único local.
"""
import discord
from discord import ui, app_commands
from typing import List

import asyncio
import random
import string
import logging

from base.BaseViews import BaseView

from .helpers import draw_teams, move_team_to_channel, generate_league_embed_text, create_timbas_player, is_user_registered, draw_teams_with_positions_and_champions
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
        self.blue_team = []  # Pode ser List[discord.User] ou List[dict]
        self.red_team = []  # Pode ser List[discord.User] ou List[dict]
        self.started = False
        self.match_id = None
        self.blue_team_id = None
        self.red_team_id = None
        self.finishing = False
        self.show_details = False  # Flag para mostrar posições e campeões
        self.reroll_used = False  # Controla se já foi usado o re-sorteio
        self.drawn = False  # Flag para controlar se já foi sorteado (Aleatório Completo)
        self.ready_players: List[discord.User] = []  # Jogadores prontos (Aleatório Completo)

        self.update_buttons()

    def update_buttons(self):
        """Atualiza o estado dos botões com base no estado da partida."""
        self.clear_items()

        if not self.started:
            # --- State: Before match starts ---

            # Modo Aleatório Completo tem fluxo especial
            if self.match_format.value == 3:  # Aleatório Completo
                if not self.drawn:
                    # Antes do sorteio: mostrar Entrar, Sair, Sortear
                    self.add_item(JoinButton(self))
                    self.add_item(LeaveButton(self))
                    self.add_item(PlayerCountButton(self.confirmed_players))
                    self.add_item(DrawButton(self))
                else:
                    # Após sorteio: esconder Entrar/Sair/Sortear, mostrar Pronto e Re-sortear
                    self.add_item(ReadyCountButton(self.ready_players))
                    self.add_item(ReadyButton(self))
                    self.add_item(RerollIndividualChampionButton(self))
                    self.add_item(StartButton(self))
                    self.add_item(FinishButton(self))
            else:
                # Outros modos mantêm comportamento original
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
        
        # Defer the interaction immediately
        await interaction.response.defer(ephemeral=True)

        if not user.voice:
            message = await interaction.followup.send("Você precisa estar em um canal de voz.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return
        
        if user in self.parent_view.confirmed_players:
            message = await interaction.followup.send("Você já está na lista.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return

        if len(self.parent_view.confirmed_players) >= 10:
            message = await interaction.followup.send("A partida já está cheia.", ephemeral=True)
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
                
        await user.move_to(self.parent_view.waiting_channel)
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

class ReadyCountButton(ui.Button):
    def __init__(self, ready_players: List[discord.User]):
        super().__init__(label=f"Prontos: {len(ready_players)}/6", style=discord.ButtonStyle.grey, disabled=True)

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

        # Verifica o modo de sorteio
        if self.parent_view.match_format.value == 3:  # Aleatório Completo
            # Modo completo: Sorteia jogadores + posições + campeões
            self.parent_view.blue_team, self.parent_view.red_team = draw_teams_with_positions_and_champions(self.parent_view.confirmed_players)
            self.parent_view.show_details = True
            self.parent_view.drawn = True  # Marca como sorteado

            # No modo debug, marca 6 jogadores como prontos automaticamente
            if self.parent_view.debug:
                self.parent_view.ready_players = self.parent_view.confirmed_players[:6]

            message_text = "Times, posições e campeões sorteados! Agora marque-se como pronto."
        else:  # Aleatório normal (value == 0)
            # Modo simples: Sorteia apenas os jogadores
            self.parent_view.blue_team, self.parent_view.red_team = draw_teams(self.parent_view.confirmed_players)
            self.parent_view.show_details = False
            message_text = "Times sorteados!"

        self.parent_view.update_buttons()
        await self.parent_view.update_embed(interaction, started=False)
        message = await interaction.followup.send(message_text, ephemeral=True)
        await asyncio.sleep(5)
        await message.delete()

class ReadyButton(ui.Button):
    """Botão para marcar-se como pronto no modo Aleatório Completo."""
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Pronto", style=discord.ButtonStyle.success, emoji="✅", disabled=parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        await interaction.response.defer(ephemeral=True)

        if user not in self.parent_view.confirmed_players:
            message = await interaction.followup.send("Você não está na partida.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return

        if user in self.parent_view.ready_players:
            # Já está pronto - não pode desconfirmar
            message = await interaction.followup.send("Você já está confirmado como pronto!", ephemeral=True)
        else:
            # Adiciona ao pronto (confirmação)
            self.parent_view.ready_players.append(user)
            message = await interaction.followup.send(f"Você está confirmado e pronto! ({len(self.parent_view.ready_players)} prontos)", ephemeral=True)
            self.parent_view.update_buttons()
            await self.parent_view.update_embed(interaction, started=False)

        await asyncio.sleep(5)
        await message.delete()


class RerollIndividualChampionButton(ui.Button):
    """Botão para cada jogador re-sortear seu próprio campeão (sem voltar atrás)."""
    def __init__(self, parent_view: CustomMatchView):
        super().__init__(label="Re-sortear Meu Campeão", style=discord.ButtonStyle.secondary, emoji="🔄", disabled=parent_view.started)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        await interaction.response.defer(ephemeral=True)

        if user not in self.parent_view.confirmed_players:
            message = await interaction.followup.send("Você não está na partida.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return

        # Encontra o jogador nos times
        from .helpers import draw_champion_for_position
        player_data = None

        for p in self.parent_view.blue_team:
            if isinstance(p, dict) and p['user'] == user:
                player_data = p
                break

        if not player_data:
            for p in self.parent_view.red_team:
                if isinstance(p, dict) and p['user'] == user:
                    player_data = p
                    break

        if not player_data:
            message = await interaction.followup.send("Erro ao encontrar seus dados.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return

        # Verifica se já re-sorteou
        if player_data.get('rerolled', False):
            message = await interaction.followup.send("Você já re-sorteou seu campeão!", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return

        # Coleta todos os campeões já usados
        used_champions = set()
        for p in self.parent_view.blue_team + self.parent_view.red_team:
            if isinstance(p, dict) and p != player_data:
                used_champions.add(p.get('champion'))

        # Re-sorteia o campeão
        position = player_data.get('position')
        new_champion = draw_champion_for_position(position, used_champions)
        old_champion = player_data.get('champion')
        player_data['champion'] = new_champion
        player_data['rerolled'] = True  # Marca que já re-sorteou

        self.parent_view.update_buttons()
        await self.parent_view.update_embed(interaction, started=False)

        message = await interaction.followup.send(f"Campeão re-sorteado! {old_champion} → {new_champion} (não pode voltar atrás)", ephemeral=True)
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

        # Verifica se precisa sortear os times primeiro (modos aleatórios)
        if (self.parent_view.match_format.value == 0 or self.parent_view.match_format.value == 3) and not (self.parent_view.blue_team and self.parent_view.red_team):
            message = await interaction.followup.send("Sorteie os times primeiro.", ephemeral=True)
            asyncio.create_task(delete_message_after_delay(message))
            return

        # Verifica se pelo menos 6 jogadores estão prontos no modo Aleatório Completo
        if self.parent_view.match_format.value == 3:
            ready_count = len(self.parent_view.ready_players)
            required_ready = 6  # Mínimo de 6 jogadores prontos

            if ready_count < required_ready:
                message = await interaction.followup.send(
                    f"Aguarde pelo menos 6 jogadores estarem prontos para iniciar. ({ready_count}/{required_ready})",
                    ephemeral=True
                )
                asyncio.create_task(delete_message_after_delay(message))
                return

        if self.parent_view.match_format.value == 1: # Modo Livre
            half = len(self.parent_view.confirmed_players) // 2
            self.parent_view.blue_team = self.parent_view.confirmed_players[:half]
            self.parent_view.red_team = self.parent_view.confirmed_players[half:]

        # Criar a partida na API Timbas
        if self.parent_view.online_mode.value == 1:
            timbas = timbasService()

            # Gerar riotMatchId aleatório
            random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=9))
            riot_match_id = f"TB_{random_string}"

            # Construir o payload baseado no tipo de partida
            match_type = self.parent_view.match_format.value

            # Função auxiliar para construir informações dos jogadores
            def build_player_data(player_data):
                if isinstance(player_data, dict):
                    # Modo Aleatório Completo - inclui posição e campeão
                    player_info = {
                        "discordId": str(player_data['user'].id),
                        "position": player_data.get('position'),
                        "champion": player_data.get('champion'),
                        "rerolledChampion": player_data.get('rerolled', False)
                    }
                    return player_info
                else:
                    # Outros modos - apenas discordId (sem position, champion, rerolledChampion)
                    return {
                        "discordId": str(player_data.id)
                    }

            payload = {
                "serverDiscordId": str(interaction.guild.id),
                "riotMatchId": riot_match_id,
                "matchType": match_type,
                "teamBlue": {
                    "players": [build_player_data(p) for p in self.parent_view.blue_team]
                },
                "teamRed": {
                    "players": [build_player_data(p) for p in self.parent_view.red_team]
                }
            }
            response = timbas.createMatch(payload)
            if response.status_code == 201:
                match_data = response.json()
                self.parent_view.match_id = match_data.get('id')
                self.parent_view.blue_team_id = match_data.get('teamBlueId')
                self.parent_view.red_team_id = match_data.get('teamRedId')

                if not self.parent_view.match_id or not self.parent_view.blue_team_id or not self.parent_view.red_team_id:
                    message = await interaction.followup.send("Erro: A resposta da API não continha os IDs necessários.", ephemeral=True)
                    asyncio.create_task(delete_message_after_delay(message))
                    return
            else:
                message = await interaction.followup.send(f"Erro ao criar a partida na API: {response.text}", ephemeral=True)
                asyncio.create_task(delete_message_after_delay(message))
                return

            if (self.parent_view.blue_channel and self.parent_view.red_channel) and not self.parent_view.debug:
                # Extrai os usuários dos times (pode ser dict ou User)
                blue_users = [p['user'] if isinstance(p, dict) else p for p in self.parent_view.blue_team]
                red_users = [p['user'] if isinstance(p, dict) else p for p in self.parent_view.red_team]
                await move_team_to_channel(blue_users, self.parent_view.blue_channel)
                await move_team_to_channel(red_users, self.parent_view.red_channel)
        
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
        await interaction.followup.send("Quem venceu a partida?", view=finish_view, ephemeral=True)
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
            await self.parent_view.original_message.edit(view=self.parent_view.match_view)

        if response_ok:
            winner_side = 'BLUE' if winner_team_id == self.parent_view.match_view.blue_team_id else 'RED'
            winner_label = "Azul" if winner_side == 'BLUE' else "Vermelho"

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
                color=discord.Color.blue() # ou a cor original
            )
            final_embed.set_footer(text=f"Partida finalizada! Vencedor: Time {winner_label}")
            final_embed.set_image(url="attachment://timbasQueueGif.gif")

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
            await self.original_message.edit(view=self.match_view)
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
        await interaction.response.defer(ephemeral=True)

        if not user.voice:
            message = await interaction.followup.send("Você precisa estar em um canal de voz para ser movido.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
            return

        # Extrai os usuários dos times (pode ser dict ou User)
        blue_players = [p['user'] if isinstance(p, dict) else p for p in self.parent_view.blue_team]
        red_players = [p['user'] if isinstance(p, dict) else p for p in self.parent_view.red_team]

        if user in blue_players:
            await user.move_to(self.parent_view.blue_channel)
            message = await interaction.followup.send("Você foi movido para o canal do Time Azul.", ephemeral=True)
            await asyncio.sleep(5)
            await message.delete()
        elif user in red_players:
            await user.move_to(self.parent_view.red_channel)
            message = await interaction.followup.send("Você foi movido para o canal do Time Vermelho.", ephemeral=True)
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