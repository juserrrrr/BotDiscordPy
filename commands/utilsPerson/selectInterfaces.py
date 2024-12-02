import discord
from discord import ui
from discord.interactions import Interaction


class createEssentialChannels(ui.Select):
  def __init__(self, channels, response):
    super().__init__(placeholder="Escolha uma opção.")
    self.channels = channels
    self.response = response
    self.options = [
        discord.SelectOption(
            label="Sim", description="Você me permite criar os canais.", emoji="✅", value=1),
        discord.SelectOption(
            label="Não", description="Você não me permite a criar os canais.", emoji="❌", value=0)
    ]

  async def callback(self, interaction: Interaction):
    selectedOption = self.values[0]

    if selectedOption == '0':
      await interaction.response.edit_message(content="Ok, Entendi.", view=None, delete_after=3)
      return
    await interaction.response.edit_message(content="Criando canais...", view=None)

    # Variaveis utilizadas
    categoryName = "🆚 Personalizada"
    categoryPerson = None
    categoriesGuild = interaction.guild.categories

    # Verificando se tem já tem a categoria da personalizada
    for category in categoriesGuild:
      if category.name == categoryName:
        categoryPerson = category
        break
    # Se não tiver, cria a categoria
    if categoryPerson is None:
      categoryPerson = await interaction.guild.create_category(categoryName)

    # Apagando os canais da personalizada, se hover
    for channel in categoryPerson.channels:
      await channel.delete()

    # Criando os canais da personalizada
    for channel in self.channels:
      if channel not in interaction.guild.channels:
        await interaction.guild.create_voice_channel(channel, category=categoryPerson)
    self.response.set_result(selectedOption)
