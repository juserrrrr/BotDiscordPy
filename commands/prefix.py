import discord
from discord.ext import commands
from mechanics import readFile,saveFile
class Prefix(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @commands.command(name = 'prefix')
    async def prefix(self,ctx,arg):
        await ctx.message.delete()
        if not len(arg)>= 4 and arg[-1] in ['!',',','.','/','*','-','_','@']:
            servers_prefix = readFile()
            servers_prefix[str(ctx.guild.id)] = arg
            saveFile(servers_prefix)
            message_description = f"O Prefixo foi alterado para[ {arg} ]."
        else:
            if len(arg)>= 4:
                message_description = f"O prefixo precisa ter menos de 4 caracteres."
            else:
                message_description = f"O prefixo precisa terminar com um desses simbolos:\n! , . / * - _ @"

        embed_message = discord.Embed(
            title = f"🎅 │ **{ctx.guild.name}     **",
            description = f"**{message_description}**",
            color = 0xFF0004
        )
        embed_message.set_thumbnail(url = ctx.guild.icon_url_as(format='png'))
        message = await ctx.send(embed = embed_message)
        await message.delete(delay=3)

def setup(client):
    client.add_cog(Prefix(client))