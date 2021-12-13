import json

def loadEvents():
    for filename in os.listdir('events'):
        if filename.endswith('.py'):
            client.load_extension(f'events.{filename[:-3]}')

def loadCommands():
    for filename in os.listdir('commands'):
        if filename.endswith('.py'):
            client.load_extension(f'commands.{filename[:-3]}')

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
