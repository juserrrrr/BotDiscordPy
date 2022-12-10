import discord
from discord.ext import commands

class MoveOnReact(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.command(name = 'moveOnReact')
    @commands.has_role(785650860125978635)
    async def moveOnReact(self,ctx):
        await ctx.message.delete()  
        embed_message = discord.Embed(
            title = f"🎅 │ **{ctx.guild.name}**",
            description = f"**Reaja a esta mensagem**\nVocê precisa estar em um canal de voz!",
            color = 0xFF0004,
        )
        embed_message.set_thumbnail(url = ctx.guild.icon.replace(format="png").url)
        message = await ctx.send(embed = embed_message)
        await message.add_reaction('🚨')

        def check(reaction,user):
          return str(reaction) == '🚨'

        channel = await self.client.fetch_channel(785657702806323270)
        contador = 0
        while (contador != 1):
            reaction,user = await self.client.wait_for("reaction_add",check = check)
            if user.voice == None:
                await reaction.remove(user)
            else:
                contador +=1
            
        await user.move_to(channel)
        await message.delete(delay=0)

      
async def setup(client):
    await client.add_cog(MoveOnReact(client))