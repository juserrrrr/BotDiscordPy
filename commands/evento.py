import discord
from discord import app_commands, ui
from discord.ext import commands
import asyncio

from base.BaseViews import BaseView
from base.BaseModal import BaseModal
from commands.utilsPerson.ui import CustomMatchView
from commands.utilsPerson.helpers import generate_league_embed_text


# ─── Modal de criação do evento ──────────────────────────────────────────────

class EventoModal(BaseModal, title="Criar Evento"):
    titulo = ui.TextInput(
        label="Título do evento",
        placeholder="Ex: Person das 21h",
        max_length=80,
        required=True
    )
    descricao = ui.TextInput(
        label="Descrição",
        placeholder="Detalhes do evento, regras, etc.",
        style=discord.TextStyle.paragraph,
        max_length=300,
        required=False
    )
    horario = ui.TextInput(
        label="Horário (opcional)",
        placeholder="Ex: Hoje às 21h, Sábado 20:00",
        max_length=50,
        required=False
    )

    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        titulo = self.titulo.value.strip()
        descricao = self.descricao.value.strip() if self.descricao.value else None
        horario = self.horario.value.strip() if self.horario.value else None

        embed = _build_event_embed(
            creator=interaction.user,
            titulo=titulo,
            descricao=descricao,
            horario=horario,
            going=[],
            not_going=[]
        )

        view = EventoView(
            creator=interaction.user,
            titulo=titulo,
            descricao=descricao,
            horario=horario
        )
        msg = await self.channel.send(embed=embed, view=view)
        view.message = msg

        await interaction.followup.send(
            f"Evento criado em {self.channel.mention}!",
            ephemeral=True,
            delete_after=5
        )


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _build_event_embed(
    creator: discord.User,
    titulo: str,
    descricao: str | None,
    horario: str | None,
    going: list,
    not_going: list
) -> discord.Embed:
    embed = discord.Embed(title=f"📅  {titulo}", color=discord.Color.blurple())

    if descricao:
        embed.description = descricao

    if horario:
        embed.add_field(name="🕐 Horário", value=horario, inline=False)

    embed.add_field(
        name=f"✅ Vou ({len(going)})",
        value="\n".join(u.display_name for u in going) or "*Ninguém ainda*",
        inline=True
    )
    embed.add_field(
        name=f"❌ Não Vou ({len(not_going)})",
        value="\n".join(u.display_name for u in not_going) or "*Ninguém ainda*",
        inline=True
    )

    embed.set_footer(text=f"Criado por {creator.display_name}")
    embed.set_thumbnail(url=creator.display_avatar.url)
    return embed


# ─── View principal do evento ─────────────────────────────────────────────────

class EventoView(BaseView):
    def __init__(self, creator: discord.User, titulo: str, descricao: str | None, horario: str | None):
        super().__init__(timeout=None)
        self.creator = creator
        self.titulo = titulo
        self.descricao = descricao
        self.horario = horario
        self.going: list[discord.User] = []
        self.not_going: list[discord.User] = []
        self.message: discord.Message | None = None

    async def _update_embed(self):
        if not self.message:
            return
        embed = self.message.embeds[0]
        for i, field in enumerate(embed.fields):
            if field.name.startswith("✅"):
                embed.set_field_at(
                    i,
                    name=f"✅ Vou ({len(self.going)})",
                    value="\n".join(u.display_name for u in self.going) or "*Ninguém ainda*",
                    inline=True
                )
            elif field.name.startswith("❌"):
                embed.set_field_at(
                    i,
                    name=f"❌ Não Vou ({len(self.not_going)})",
                    value="\n".join(u.display_name for u in self.not_going) or "*Ninguém ainda*",
                    inline=True
                )
        await self.message.edit(embed=embed, view=self)

    @ui.button(label="Vou", style=discord.ButtonStyle.success, emoji="✅", row=0)
    async def btn_vou(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user

        if user in self.not_going:
            self.not_going.remove(user)

        if user in self.going:
            msg = await interaction.followup.send("Você já confirmou presença.", ephemeral=True)
            await asyncio.sleep(4)
            await msg.delete()
            return

        self.going.append(user)
        await self._update_embed()

        msg = await interaction.followup.send("Presença confirmada!", ephemeral=True)
        await asyncio.sleep(4)
        await msg.delete()

    @ui.button(label="Não Vou", style=discord.ButtonStyle.danger, emoji="❌", row=0)
    async def btn_nao_vou(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user

        if user in self.going:
            self.going.remove(user)

        if user in self.not_going:
            msg = await interaction.followup.send("Você já marcou que não vai.", ephemeral=True)
            await asyncio.sleep(4)
            await msg.delete()
            return

        self.not_going.append(user)
        await self._update_embed()

        msg = await interaction.followup.send("Marcado como não vai.", ephemeral=True)
        await asyncio.sleep(4)
        await msg.delete()

    @ui.button(label="Criar Partida", style=discord.ButtonStyle.primary, emoji="🎮", row=0)
    async def btn_criar_partida(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)

        if interaction.user != self.creator:
            msg = await interaction.followup.send(
                "Apenas o criador do evento pode iniciar a partida.",
                ephemeral=True
            )
            await asyncio.sleep(5)
            await msg.delete()
            return

        view = EscolherFormatoView(creator=self.creator)
        msg = await interaction.followup.send(
            "Escolha o formato e o modo da partida:",
            view=view,
            ephemeral=True,
            wait=True
        )
        view.message = msg


# ─── View de seleção de formato/modo ─────────────────────────────────────────

class EscolherFormatoView(BaseView):
    def __init__(self, creator: discord.User):
        super().__init__(timeout=60)
        self.creator = creator
        self.formato_value: int | None = None
        self.modo_value: int | None = None
        self.message: discord.WebhookMessage | None = None
        self.add_item(FormatoSelect(self))
        self.add_item(ModoSelect(self))

    async def tentar_criar(self, interaction: discord.Interaction):
        """Cria a partida após ambos os selects serem preenchidos."""
        if self.formato_value is None or self.modo_value is None:
            return  # Aguarda o outro select

        from discord.app_commands import Choice

        formato_names = {0: "Aleatório", 1: "Livre", 3: "Aleatório Completo"}
        modo_names = {1: "Online", 0: "Offline"}

        match_format = Choice(name=formato_names[self.formato_value], value=self.formato_value)
        online_mode = Choice(name=modo_names[self.modo_value], value=self.modo_value)

        guild = interaction.guild
        required_voice = {"| 🕘 | AGUARDANDO", "LADO [ |🔵| ]", "LADO [ |🔴| ]"}
        voice_map = {ch.name: ch for ch in guild.voice_channels if ch.name in required_voice}
        text_channel = discord.utils.get(guild.text_channels, name="custom_game")

        missing = required_voice - set(voice_map.keys())
        if missing or not text_channel:
            if self.message:
                try:
                    await self.message.delete()
                except Exception:
                    pass
            msg = await interaction.followup.send(
                "Os canais da partida não existem. Use `/criarperson` primeiro para criá-los.",
                ephemeral=True,
                wait=True
            )
            await asyncio.sleep(8)
            try:
                await msg.delete()
            except Exception:
                pass
            return

        waiting_channel = voice_map["| 🕘 | AGUARDANDO"]
        blue_channel = voice_map["LADO [ |🔵| ]"]
        red_channel = voice_map["LADO [ |🔴| ]"]

        view = CustomMatchView(
            creator=self.creator,
            waiting_channel=waiting_channel,
            blue_channel=blue_channel,
            red_channel=red_channel,
            online_mode=online_mode,
            match_format=match_format,
        )

        embed_text = generate_league_embed_text(
            blue_team=[],
            red_team=[],
            match_format=match_format.name,
            online_mode=online_mode.name
        )
        embed = discord.Embed(
            description=f"```{embed_text}```",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Aguardando jogadores...")
        embed.set_image(url="attachment://timbasQueueGif.gif")

        await text_channel.send(
            embed=embed,
            view=view,
            file=discord.File('./images/timbasQueueGif.gif')
        )

        if self.message:
            try:
                await self.message.delete()
            except Exception:
                pass

        msg = await interaction.followup.send(
            f"Partida criada! Ver em {text_channel.mention}",
            ephemeral=True,
            wait=True
        )
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except Exception:
            pass


class FormatoSelect(ui.Select):
    def __init__(self, parent: EscolherFormatoView):
        self.parent = parent
        options = [
            discord.SelectOption(label="Aleatório", value="0", emoji="🎲"),
            discord.SelectOption(label="Livre", value="1", emoji="✋"),
            discord.SelectOption(label="Aleatório Completo", value="3", emoji="🔀"),
        ]
        super().__init__(placeholder="Formato da partida...", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.parent.formato_value = int(self.values[0])
        await self.parent.tentar_criar(interaction)


class ModoSelect(ui.Select):
    def __init__(self, parent: EscolherFormatoView):
        self.parent = parent
        options = [
            discord.SelectOption(label="Online", value="1", description="Registra estatísticas", emoji="📊"),
            discord.SelectOption(label="Offline", value="0", description="Sem registro", emoji="🎮"),
        ]
        super().__init__(placeholder="Modo da partida...", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.parent.modo_value = int(self.values[0])
        await self.parent.tentar_criar(interaction)


# ─── Cog ─────────────────────────────────────────────────────────────────────

class Evento(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name='evento', description="Cria um convite de evento com confirmação de presença.")
    @app_commands.guild_only()
    async def evento(self, interaction: discord.Interaction):
        modal = EventoModal(channel=interaction.channel)
        await interaction.response.send_modal(modal)


async def setup(client):
    await client.add_cog(Evento(client))
