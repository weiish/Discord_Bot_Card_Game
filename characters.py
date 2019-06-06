import discord
import random
import os
import images
from discord.ext import commands

class Characters:
    def __init__(self, client):
        self.client = client
        self.sql = client.cogs['SQL']

    @commands.command(pass_context=True)
    async def top(self, ctx):
        return 
        
    @commands.command(pass_context=True, aliases=['c'])
    async def character(self, ctx, *argv):
        if len(argv) > 1:
            #Check if last two arguments are integers
            allArgs = argv
            try:
                index = int(allArgs[-2])
                picIndex = int(allArgs[-1])
                allArgs = " ".join(argv[:-2])
            except ValueError:
                picIndex = 1
                try:
                    index = int(allArgs[-1])
                    allArgs = " ".join(argv[:-1])
                except ValueError:
                    index = -1
                    picIndex = 1
        else:
            index = -1
            picIndex = 1
            allArgs = argv[0]
        print(allArgs)
        cs = self.get_character(allArgs)
        outputString = ""
        if cs:
            if len(cs) > 1:
                if index == -1:
                    counter = 1
                    outputString = outputString + "Found Multiple Matches: \n"
                    for c in cs:
                        if len(outputString) > 1800:
                            break
                        outputString = outputString + "{}: **{}** - ({})\n".format(str(counter), c.name, c.t_gender)    
                        counter += 1
                    await self.client.say(outputString)
                else:
                    try:
                        c = cs[index - 1]
                    except:
                        await self.client.say("Invalid index provided")
                    try:
                        outputString = outputString + "**{}** - ({}) found with {} favorites \n".format(c.name, c.t_gender, c.num_favorites)
                        await self.client.say(outputString)
                        destinationFolder = r'F:\Anime Character Images'
                        writeFolderPath = os.path.join(destinationFolder, str(c.id))
                        fileName = str(c.id) + "_" + str(picIndex) + ".png"
                        fullFilePath = os.path.join(writeFolderPath,fileName)
                        tempCard = images.generate_card_img(3, 0, c.name, 0, 0, 0, 0, fullFilePath, 0)                        
                        await self.client.send_file(ctx.message.channel, tempCard.name)
                        tempCard.close()
                        os.remove(tempCard.name)
                    except:
                        await self.client.say("Image retrieval failed")
            else:
                c = cs[0]
                outputString = outputString + "**{}** - ({}) found with {} favorites \n".format(c.name, c.t_gender, c.num_favorites)
                await self.client.say(outputString)
                destinationFolder = r'F:\Anime Character Images'
                writeFolderPath = os.path.join(destinationFolder, str(c.id))
                fileName = str(c.id) + "_" + str(1) + ".png"
                fullFilePath = os.path.join(writeFolderPath,fileName)
                tempCard = images.generate_card_img(3, 0, c.name, 0, 0, 0, 0, fullFilePath, 0)                        
                await self.client.send_file(ctx.message.channel, tempCard.name)
                tempCard.close()
                os.remove(tempCard.name)
                
            
            
        else:
            await self.client.say("Character not found")
    
    def get_character(self, charIDorName):
        try:
            charIDorName = int(charIDorName)
            c = self.query_character_by_id(charIDorName)
        except ValueError:
            c = self.query_character_by_name(charIDorName)
        return c
            
    def query_character_by_id(self, id):
        query = self.sql.sel2("SELECT * FROM characters WHERE id = {} ORDER BY num_favorites DESC".format(id))
        results = query.fetchall()
        if results:
            charList = []
            for result in results:
                charList.append(Character(result))
            return charList
        else:
            return None

    def query_character_by_name(self, name):
        """ #Try exact first, if no matches, try LIKE
        query = self.sql.sel2("SELECT * FROM characters WHERE `name` = '{}' ORDER BY num_favorites DESC".format(name))
        results = query.fetchall()
        if results:
            charList = []
            for result in results:
                charList.append(Character(result))
            return charList """

        query = self.sql.sel2("SELECT * FROM characters WHERE name LIKE '%{}%' ORDER BY num_favorites DESC".format(name))
        results = query.fetchall()
        if results:
            charList = []
            for result in results:
                charList.append(Character(result))
            return charList
        else:
            return None


def setup(client):
    client.add_cog(Characters(client))

class Character:
    def __init__(self, queryResult):      
        print(queryResult)  
        self.id = queryResult[0]
        self.full_name = queryResult[1]
        self.universe = queryResult[2]
        self.role = queryResult[3]
        self.num_favorites = queryResult[4]
        self.name = queryResult[5]
        self.t_gender = queryResult[6]
        self.gender = queryResult[7]
    

