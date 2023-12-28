import discord
from discord import ui
from .selectInterfaces import createEssentialChannels
import asyncio


class ViewActionConfirm(ui.View):
    def __init__(self, channels):
        super().__init__()
        self.future = asyncio.Future()
        self.add_item(createEssentialChannels(channels, self.future))