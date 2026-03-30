"""
Lida com a verificação de contas do League of Legends via backend Timbas.
"""
import discord
from discord import ui
import random

from services.timbasService import timbasService
from .helpers import get_league_account_data, create_timbas_player


class VerificationView(ui.View):
    """View para o processo de verificação de conta do LoL."""

    def __init__(self, timbas: timbasService, player_data: dict, verification_icon_id: int, verification_icon_url: str):
        super().__init__(timeout=180)
        self._timbas = timbas
        self.player_data = player_data
        self.verification_icon_id = verification_icon_id
        self.verification_icon_url = verification_icon_url
        self.result = None

    @ui.button(label='Verificar', style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()

        puuid = self.player_data.get('puuid')
        verify_response = self._timbas.verifyIconLol(puuid, self.verification_icon_id)

        if verify_response is None or verify_response.status_code != 200:
            self.result = {'success': False, 'message': "Não foi possível verificar a conta. Tente novamente."}
            self.stop()
            return

        verified = verify_response.json().get('verified', False)
        if verified:
            response = await create_timbas_player(interaction.user, self.player_data)
            if response.status_code == 201:
                self.result = {'success': True, 'message': "Conta verificada e registrada com sucesso!"}
            else:
                self.result = {'success': False, 'message': "Erro ao registrar a conta. Tente novamente."}
        else:
            self.result = {'success': False, 'message': "O ícone de perfil não foi alterado. Verificação falhou."}

        self.stop()

    @ui.button(label='Cancelar', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        self.result = {'success': False, 'message': "Verificação cancelada."}
        self.stop()


class LeagueVerificationModal(ui.Modal, title="Verificação de Conta do LoL"):
    """Modal para o usuário inserir seu nick do League of Legends."""
    league_name = ui.TextInput(
        label="Seu nick e tag do LoL (Ex: Timbas#BR1)",
        min_length=5,
        max_length=25,
        placeholder="Nickname#TAG",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Buscando sua conta...", ephemeral=True)

        player_data = get_league_account_data(self.league_name.value)
        if not player_data:
            await interaction.edit_original_response(content="Conta não encontrada. Verifique o nick e a tag.")
            final_message = await interaction.original_response()
            await final_message.delete(delay=5)
            return

        timbas = timbasService()
        current_icon_id = player_data.get('profileIconId')

        available_icons = list(range(1, 30))
        if current_icon_id in available_icons:
            available_icons.remove(current_icon_id)
        verification_icon_id = random.choice(available_icons)
        verification_icon_url = timbas.getProfileIconUrlLol(verification_icon_id)

        embed = discord.Embed(
            title=f"É você, {player_data.get('name')}?",
            description="Para confirmar que a conta é sua, mude seu ícone de perfil no LoL para o ícone abaixo e clique em **Verificar**.",
            color=discord.Color.green()
        )
        embed.add_field(name="Nível", value=player_data.get('level'))
        embed.add_field(name="Solo/Duo", value=f"{player_data.get('tierSolo')} {player_data.get('rankSolo')}")
        embed.add_field(name="Flex", value=f"{player_data.get('tierFlex')} {player_data.get('rankFlex')}")
        embed.set_thumbnail(url=verification_icon_url)

        view = VerificationView(timbas, player_data, verification_icon_id, verification_icon_url)
        await interaction.edit_original_response(content=None, embed=embed, view=view)

        await view.wait()

        result_message = "Ocorreu um erro inesperado."
        if view.result:
            result_message = view.result.get('message', result_message)

        result_embed = discord.Embed(
            description=result_message,
            color=discord.Color.green() if view.result and view.result.get('success') else discord.Color.red()
        )
        await interaction.edit_original_response(content=None, embed=result_embed, view=None)

        final_message = await interaction.original_response()
        await final_message.delete(delay=5)
