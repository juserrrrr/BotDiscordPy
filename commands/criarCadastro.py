import discord
from discord.ext import commands
import asyncio

from discord.ext.commands.core import command

class CriarCadastro(commands.Cog):
    def __init__(self,client):
        self.client = client

    @commands.command(name = 'criarcadastro')
    @commands.has_role(785650860125978635)
    async def criarcadastro(self,ctx):
        def checkChannel(message):
            return ctx.message.author == message.author and ctx.channel == message.channel  
        await ctx.message.delete()

        questions = ["Ok, vamos lá, qual titulo da embed?","Qual a descrição da embed?","Escolha agora um emote para ficar como parametro de cadastro!"]
        values = []
        for num in range(len(questions)):
            await ctx.send(questions[num])
            values.append(await self.client.wait_for('message', check = checkChannel))
            await asyncio.sleep(0.5)
            await ctx.channel.purge(limit=2)
        embed_message = discord.Embed(
            title = f"⚠ │ **{values[0].content}   **",
            description = f"**{values[1].content}**",
            color = 0xB300FF
        )
        embed_message.set_thumbnail(url = ctx.guild.icon_url_as(format='png'))
        message = await ctx.send(embed = embed_message)
        await message.add_reaction(values[2].content)

    # @commands.Cog.listener()
    # async def on_reaction_add(self,reaction,user):
    #     print(reaction)
    #     print('💞')
    #     if reaction == '💞':
    #         print('Entrei')
    #         role = await self.cliet.guild.get_role(915383046704889964)
    #         await self.client.add_roles(user,role)
    #     print(f"o user {user} adcinou a reação{reaction} ")



async def setup(client):
    await client.add_cog(CriarCadastro(client))