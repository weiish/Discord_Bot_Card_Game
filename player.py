#Handles all player functions:
#   Account creation, Adjusting money, Adding experience, Adjusting items/goods, Inventory management
import discord
import images
import os
import re
from prettytable import PrettyTable
from discord.ext import commands

class Player:
    def __init__(self, client):
        self.client = client
        self.sql = client.cogs['SQL']
        self.startingMoney = 100
        self.query_users()
    
    def setReferences(self, client):
        self.decks = client.cogs['Decks']

    @commands.command(pass_context=True)
    async def register(self, ctx):
        discord_id = str(ctx.message.author.id)

        if discord_id in self.existing_users:
            await self.client.say('You are already registered, {}'.format(ctx.message.author.mention))
        else:
            await self.client.say("Please enter a name for your character (no symbols or numbers, limit 15 characters): ")
            nameResponse = await self.client.wait_for_message(author=ctx.message.author, timeout=10)

            if not re.match("^[a-z]*$", nameResponse.clean_content.lower()):
                await self.client.say('Only letters a-z allowed. Cancelling registration')
            elif len(nameResponse.clean_content) > 15:
                await self.client.say('Only 15 characters allowed. Cancelling registration')
            else:
                self.sql.exec("INSERT INTO users (`discord_id`, `name`, `money`) VALUES (%s, %s, %s)", (
                    discord_id, nameResponse.clean_content, self.startingMoney))
                self.query_users()
                await self.client.say('You are now registered as {}, {}'.format(nameResponse.clean_content, ctx.message.author.mention))        

    @commands.command(pass_context=True)
    async def delete(self, ctx):
        await self.client.say("If you are sure, type 'confirm deletion' to delete your account")
        response = await self.client.wait_for_message(author=ctx.message.author, timeout=10)

        if response.clean_content.lower() == 'confirm deletion':
            self.sql.exec("DELETE FROM users WHERE discord_id={}".format(
                str(ctx.message.author.id)))
            # Delete other things related to the user account here
            self.query_users()
            await self.client.say('Successfully deleted your account, sorry to see you go {}'.format(ctx.message.author.mention))
        else:
            await self.client.say('Deletion cancelled')

    @commands.command(pass_context=True, aliases=['p'])
    async def profile(self, ctx):
        discord_id = str(ctx.message.author.id)
        profiledata = self.query_user(discord_id)
        if not profiledata.rowcount:
            await self.client.say("You are not registered, {}".format(ctx.message.author.mention))
        else:
            for (discordID, name, money) in profiledata:
                await self.client.say("Profile Output\nDiscord ID: {} \nName: {}\nMoney: {}".format(discordID, name, money))
    
    @commands.command(pass_context=True, aliases=['list','li','linv'])
    async def listinventory(self,ctx):
        discord_id = str(ctx.message.author.id)
        inventorydata = self.sql.sel("SELECT cards.card_id, cards.name, cards.top, cards.right, cards.bottom, cards.left, cards.rarity, inventory.quantity FROM cards INNER JOIN inventory ON cards.card_id = inventory.item_id WHERE inventory.discord_id = {} ORDER BY cards.card_id".format(discord_id))
        if not inventorydata.rowcount:
            await self.client.say("Your inventory is empty, {}".format(ctx.message.author.mention))
        else:
            table = PrettyTable()
            table.field_names = ["ID","Name","Rarity","^",">","v","<","Quantity"]            
            for (card_id, name, top, right, bottom, left, rarity, quantity) in inventorydata:
                table.add_row([card_id, name, rarity, top, right, bottom, left, quantity])
            await self.client.say("```" + table.get_string(title=ctx.message.author.name + "'s Inventory") + "```")
    
    @commands.command(pass_context=True, aliases=['inv','i'])
    async def inventory(self,ctx):
        discord_id = str(ctx.message.author.id)
        inventorydata = self.sql.sel("SELECT cards.card_id, cards.name, cards.top, cards.right, cards.bottom, cards.left, cards.img_path, cards.rarity, inventory.quantity FROM cards INNER JOIN inventory ON cards.card_id = inventory.item_id WHERE inventory.discord_id = {} ORDER BY cards.card_id".format(discord_id))
        if not inventorydata.rowcount:
            await self.client.say("Your inventory is empty, {}".format(ctx.message.author.mention))
        else:
            card_imgs=[]
            for (card_id, name, top, right, bottom, left, img_path, rarity, quantity) in inventorydata:
                tempCard = images.generate_card_img(2, card_id, name,top,right,bottom,left,img_path,rarity)
                tempCard = images.add_card_amount(tempCard, card_id, quantity)
                card_imgs.append(tempCard)
            inventoryImg = images.generate_inventory(card_imgs)
            await self.client.send_file(ctx.message.channel, inventoryImg.name)
            inventoryImg.close()
            os.remove(inventoryImg.name)


    """@commands.command(pass_context=True)
    async def test(self, ctx, card_id, quantity):
        author = ctx.message.author
        await self.rem_item_from_inventory(author.id, card_id, quantity)
        await self.client.say("Removing {} of card {} from your inventory".format(quantity, card_id))
"""
    def add_item_to_inventory(self, discord_id, item_id, quantity):
        try:
            cursor = self.sql.sel(
                "SELECT * FROM inventory WHERE discord_id = {} AND item_id = {}".format(discord_id, item_id))
            if not cursor.rowcount:
                # No entry yet, add a new one
                print("Add Item to Inventory: Inserting new entry")
                self.sql.exec("INSERT INTO inventory (discord_id, item_id, quantity) VALUES (%s, %s, %s)", (
                    discord_id, item_id, quantity))
            else:
                # Already have an entry, add number to quantity
                print("Add Item to Inventory: Updating existing entry")
                self.sql.exec("UPDATE inventory SET quantity = quantity + %s WHERE discord_id = %s AND item_id = %s", (
                    quantity, discord_id, item_id))
            return True
        except:
            print("Failed to add item to inventory")
            return False  
        
    async def rem_item_from_inventory(self, discord_id, item_id, quantity):
        #Remove item from inventory
        try:
            quantity = int(quantity)
            cursor = self.sql.sel(
                "SELECT quantity FROM inventory WHERE discord_id = {} AND item_id = {}".format(discord_id, item_id))
            if not cursor.rowcount:
                # No entry yet, this should throw an error
                print("Attempted to remove an item that was not in the inventory")
                return False
            else:
                currentQuantity = int(cursor.fetchall()[0][0])
                # Check if this is the last of that item, delete row if needed
                if currentQuantity <= quantity:
                    currentQuantity = 0 
                    self.sql.exec("DELETE FROM inventory WHERE discord_id = {} AND item_id = {}".format(discord_id, item_id))
                    print("Removing Item from Inventory: Deleting row")
                else:
                    currentQuantity -= quantity
                    self.sql.exec("UPDATE inventory SET quantity = quantity - %s WHERE discord_id = %s AND item_id = %s", (
                    quantity, discord_id, item_id))
        except Exception as e:
            print(e)
            print("Failed to remove item from inventory")
            return False 
        #Check if any decks are affected by this, if so, remove card from those decks
        #TODO Get deck function here maybe?

        #Query deckslots to pull all the deck_id from decks that contain the card
        deckQuery = self.sql.sel("SELECT decks.deck_id FROM decks INNER JOIN deckslots ON decks.deck_id = deckslots.deck_id WHERE decks.discord_id = {} AND deckslots.card_id = {}".format(discord_id, item_id))
        deckIDs = deckQuery.fetchall()
        deckSet = set(deckIDs)
        player = await self.client.get_user_info(discord_id)

        msgSent = False
        for uniqueDeck in deckSet:
            counts = deckIDs.count(uniqueDeck)
            if counts > currentQuantity:
                if not msgSent:
                    #await self.client.say("{}, one or more of your decks did not have enough of card ID #{} and was automatically edited".format(player.mention, item_id))
                    msgSent = True
                for x in range(counts - currentQuantity):
                    self.decks.remove_from_deck(uniqueDeck[0], item_id)
                #Do things to remove from decks

        #for each deck_id
            #check if player still owns enough of the card to have that many
            #if no, remove card from those decks until there are enough
        #message player to say some decks have been affected
        return
    
    def player_has_card(self, discord_id, card_id):

        return

    def player_has_money(self, discord_id, amount):
        moneyQuery = self.sql.sel("SELECT money FROM users WHERE discord_id = {}".format(discord_id))
        money = int(moneyQuery.fetchone()[0])
        if money >= amount:
            return True
        else:
            return False
            
    def player_deck_is_valid(self, discord_id, deck_dictionary):
        card_ids = list(deck_dictionary.keys())
        if len(card_ids) == 1:
            card_ids = card_ids[0]
            cursor = self.sql.sel("SELECT item_id, quantity FROM inventory WHERE discord_id = {} AND item_id = {}".format(discord_id, card_ids))
        else:
            card_ids = tuple(card_ids)
            cursor = self.sql.sel("SELECT item_id, quantity FROM inventory WHERE discord_id = {} AND item_id IN {}".format(discord_id, card_ids))
        if cursor.rowcount < len(card_ids):
            return False
        inventoryInfo = cursor.fetchall()
        for (item_id, quantity) in inventoryInfo:
            if deck_dictionary[str(item_id)] > quantity:
                return False
        return True

    def add_money(self, discord_id, amount):
        if not isinstance(amount, int):
            #Amount is not an integer - do error things or something
            return False
        self.sql.exec("UPDATE users SET money = money + {} WHERE discord_id = {}".format(amount, discord_id))
        return True

    def rem_money(self, discord_id, amount):
        moneyQuery = self.sql.sel("SELECT money FROM users WHERE discord_id = {}".format(discord_id))
        money = int(moneyQuery.fetchone()[0])
        if money >= amount:
            self.sql.exec("UPDATE users SET money = money - {} WHERE discord_id = {}".format(amount, discord_id))
            return True
        else:
            return False
        return
        
    def query_user(self, discord_id):
        return self.sql.sel(
            "SELECT `discord_id`, `name`, `money` FROM users WHERE `discord_id` = {}".format(discord_id))        
    
    def query_inventory(self, discord_id):
        return self.sql.sel("SELECT cards.name, inventory.quantity FROM cards INNER JOIN inventory ON cards.card_id = inventory.item_id WHERE inventory.discord_id = {}".format(discord_id))
        
    def query_users(self):
        cursor = self.sql.sel("SELECT discord_id FROM users")
        self.existing_users = ', '.join(
            [str(users[0]) for users in cursor])

def setup(client):
    client.add_cog(Player(client))