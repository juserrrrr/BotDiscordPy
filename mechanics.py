import json
import os
import discord

def get_prefix(client,message):
    with open('prefix_servers.json','r') as file:
        Prefixs = json.load(file)
    return Prefixs[str(message.guild.id)]

def readFile():
    with open('prefix_servers.json','r') as file:
        return json.load(file)

def saveFile(save):
    with open('prefix_servers.json','w') as file:
        json.dump(save,file,indent=4)
