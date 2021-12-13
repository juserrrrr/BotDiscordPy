import json
def readFile():
    with open('prefix_servers.json','r') as file:
        return json.load(file)

def saveFile(save):
    with open('prefix_servers.json','w') as file:
        json.dump(save,file,indent=4)
