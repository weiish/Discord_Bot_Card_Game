import discord
import discord.client
import images
from discord.ext import commands
import os
import randomgen
import random
import tripletriadai as ttai

class Cards:
    def __init__(self, client):
        self.client = client
        self.sql = client.cogs['SQL']
        self.player = client.cogs['Player']

    async def get_random_card(self, ctx):
        randomCard = random.randint(1,9)
        cardDetails = self.get_card(randomCard)
        if cardDetails == None:
            await self.client.say("That card does not exist")
        else:
            tempCard = images.generate_card_img(3, cardDetails[0], cardDetails[1], cardDetails[2], cardDetails[3], cardDetails[4], cardDetails[5], cardDetails[6], cardDetails[7])                        
            await self.client.send_file(ctx.message.channel, tempCard.name)
            tempCard.close()
            os.remove(tempCard.name)

    def get_card(self, cardIDorName):
        try:
            cardIDorName = int(cardIDorName)
            cardData = self.query_card_by_id(cardIDorName)
        except ValueError:
            cardData = self.query_card_by_name(cardIDorName)
        if not cardData.rowcount:
            return None
        else:
            if cardData.rowcount:
                for (card_id, name, top, right, bottom, left, img_path, rarity) in cardData:
                    return (card_id, name, top, right, bottom, left, img_path, rarity)

    def get_card_id(self, cardIDorName):
        try:
            cardIDorName = int(cardIDorName)
            cardData = self.query_card_by_id(cardIDorName)
        except ValueError:
            cardData = self.query_card_by_name(cardIDorName)
        if not cardData.rowcount:
            return -1
        else:
            if cardData.rowcount:
                for (card_id, name, top, right, bottom, left, img_path, rarity) in cardData:
                    return card_id

    @commands.command(pass_context=True)
    #@commands.cooldown(rate=1,per=2,type=commands.BucketType.user)
    async def card(self, ctx, cardSearchTerm):
        cardDetails = self.get_card(cardSearchTerm)
        if cardDetails == None:
            await self.client.say("That card does not exist")
        else:
            tempCard = images.generate_card_img(3, cardDetails[0], cardDetails[1], cardDetails[2], cardDetails[3], cardDetails[4], cardDetails[5], cardDetails[6], cardDetails[7])                        
            await self.client.send_file(ctx.message.channel, tempCard.name)
            tempCard.close()
            os.remove(tempCard.name)
        
        #if ctx.command._buckets.valid:            
        #    bucket = ctx.command._buckets.get_bucket(ctx)
            #bucket.per = random.randint(1, 20)
        #    bucket.per = 2
        #    await self.client.say("Setting your cooldown to {}".format(bucket.per))

    #@card.error
    #async def card_error(self, error, ctx):
        #if isinstance(error, commands.CommandOnCooldown):
            #await self.client.say("You are on cooldown for **{}** seconds".format(int(error.retry_after)))

    #@commands.command(pass_context=True)
    #@commands.cooldown(rate=1,per=1,type=commands.BucketType.user)
    #async def cardcd(self, ctx):
        #if self.card._buckets.valid:
            #myCD = self.card._buckets.get_bucket(ctx).is_rate_limited()
            #if myCD:
                #await self.client.say("Your card command is on cooldown for {} seconds".format(myCD))
            #else:
                #await self.client.say("Your card command is not on cooldown")

    @commands.command(pass_context=True)
    async def addcard(self, ctx, randomStats=False, card_id=None, name=None, img_path=None, rarity=None, top=None, right=None, bottom=None, left=None):        
        if not self.user_is_me(ctx):
            await self.client.say("Command limited to owner")
            return

        if randomStats:
            stats = randomgen.card_stat_randomizer(int(rarity))
            top = stats['top']
            bottom = stats['bottom']
            left = stats['left']
            right = stats['right']

        result = self.create_card(
            card_id, name, top, right, bottom, left, img_path, rarity)
        if result:
            await self.client.say("Successfully added card {}, {}".format(name, ctx.message.author.mention))
        else:
            await self.client.say("Error, card not added")

    
    @commands.command(pass_context=True)
    async def smallcard(self, ctx, cardSearchTerm):
        cardDetails = self.get_card(cardSearchTerm)
        if cardDetails == None:
            await self.client.say("That card does not exist")
        else:
            tempCard = images.generate_card_img(1,cardDetails[0], cardDetails[1], cardDetails[2], cardDetails[3], cardDetails[4], cardDetails[5], cardDetails[6], cardDetails[7])                                    
            await self.client.send_file(ctx.message.channel, tempCard.name)
            tempCard.close()
            os.remove(tempCard.name)

    @commands.command(pass_context=True)
    async def medcard(self, ctx, cardSearchTerm):
        cardDetails = self.get_card(cardSearchTerm)
        if cardDetails == None:
            await self.client.say("That card does not exist")
        else:
            tempCard = images.generate_card_img(2,cardDetails[0], cardDetails[1], cardDetails[2], cardDetails[3], cardDetails[4], cardDetails[5], cardDetails[6], cardDetails[7])                                    
            await self.client.send_file(ctx.message.channel, tempCard.name)
            tempCard.close()
            os.remove(tempCard.name)
    
    @commands.command(pass_context=True)
    async def randcard(self, ctx, cardSearchTerm):
        if not self.user_is_me(ctx):
            await self.client.say("Command limited to owner")
            return

        
        cardDetails = self.get_card(cardSearchTerm)
        if cardDetails == None:
            await self.client.say("That card does not exist")
        else:
            response = ""
            while True:
                print("Generating Card Stats with Rarity = {}: ".format(str(cardDetails[7])))
                a = randomgen.card_stat_randomizer(cardDetails[7])
                print(a)
                tempCard = images.generate_card_img(3,cardDetails[0], cardDetails[1], a['top'], a['right'], a['bottom'], a['left'], cardDetails[6], cardDetails[7])
                await self.client.send_file(ctx.message.channel, tempCard.name)
                tempCard.close()
                os.remove(tempCard.name)

                await self.client.say("Are you okay with these stats?")
                response = await self.client.wait_for_message(author=ctx.message.author)                
                response = response.clean_content.lower()
                if response == 'yes':
                    self.sql.exec("UPDATE cards SET top = {}, `right` = {}, bottom = {}, `left` = {} WHERE card_id = {}".format(a['top'], a['right'], a['bottom'], a['left'], cardDetails[0]))
                    await self.client.say("Updated card with new randomized stats")
                    return
                elif response == 'cancel':
                    await self.client.say("Cancelling stat randomization")
        

    @commands.command(pass_context=True)
    async def getcard(self, ctx, cardSearchTerm, quantity=1):
        try:
            cardSearchTerm = int(cardSearchTerm)
            cardData = self.query_card_by_id(cardSearchTerm)
        except ValueError:
            cardData = self.query_card_by_name(cardSearchTerm)
        if not cardData.rowcount:
            await self.client.say("That card does not exist")
        else:
            if cardData.rowcount:
                for (card_id, name, top, right, bottom, left, img_path, rarity) in cardData:
                    quantity = int(quantity)
                    result = self.player.add_item_to_inventory(ctx.message.author.id, card_id, quantity)
                    if result:
                        await self.client.say('Successfully added {} ***{}*** to your collection, {}'.format(quantity, name, ctx.message.author.mention))                        
                    else:
                        await self.client.say('No card added, something went wrong')
                    break

    async def GetHand(self, game_id, player_id, orientation, playerNum):
        handQuery = self.sql.sel("SELECT card_id FROM handslots WHERE game_id = {} AND discord_id = {}".format(game_id, player_id))
        if not handQuery.rowcount:
            return None
        handDetails = handQuery.fetchall()
        tempImages = []

        for card_id in handDetails:
            if card_id[0] < 1:
                #generate default image
                tempCard = images.generate_blank_card(1)
                tempCard = images.add_card_ownership_background(tempCard, playerNum)
                tempImages.append(tempCard)
            else:
                cardDetails = self.get_card(card_id[0])
                tempCard = images.generate_card_img(1,cardDetails[0], cardDetails[1], cardDetails[2], cardDetails[3], cardDetails[4], cardDetails[5], cardDetails[6], cardDetails[7])
                tempCard = images.add_card_ownership_background(tempCard, playerNum)
                tempImages.append(tempCard)
        if orientation == 1:
            handImg = images.generate_hand(tempImages)
        elif orientation == 2:
            handImg = images.generate_hand_vert(tempImages)
        return handImg

    def GetBoard(self, game_id, flips=None):
        boardQuery = self.sql.sel("SELECT card_id, owner FROM boardslots WHERE game_id = {}".format(game_id))
        if not boardQuery.rowcount:
            return None
        boardDetails = boardQuery.fetchall()
        tempImages = []

        counter = 0
        for (card_id, card_owner) in boardDetails:
            counter = counter + 1
            if card_id < 1:
                #generate default image
                tempCard = images.generate_blank_card(2, counter)
                tempCard = images.add_card_ownership_background(tempCard, card_owner)
                tempImages.append(tempCard)
            else:
                cardDetails = self.get_card(card_id)
                tempCard = images.generate_card_img(2,cardDetails[0], cardDetails[1], cardDetails[2], cardDetails[3], cardDetails[4], cardDetails[5], cardDetails[6], cardDetails[7])
                tempCard = images.add_card_ownership_background(tempCard, card_owner)
                tempImages.append(tempCard)
        boardImg = images.generate_board(tempImages, flips)
        return boardImg
         
    def card_exists(self, card_identifier):
        try:
            card_identifier = int(card_identifier)
            cursor = self.query_card_by_id(card_identifier)
        except ValueError:
            cursor = self.query_card_by_name(card_identifier)
        if not cursor.rowcount:
            return False
        else:
            return True

    def query_card_by_id(self, card_id):
        return self.sql.sel(
            "SELECT * FROM cards WHERE card_id = {}".format(card_id))

    def query_card_by_name(self, cardName):
        return self.sql.sel(
            "SELECT * FROM cards WHERE name LIKE '%{}%'".format(cardName))

    def query_hand(self, game_id, discord_id):
        return self.sql.sel(
            "SELECT card_id FROM handslots WHERE discord_id = {} AND game_id = {} ORDER BY slot_index".format(discord_id, game_id))

    def create_card(self, card_id, name, top, right, bottom, left, img_path, rarity):
        if card_id == -1:
            #No Card ID specified
            #Insert without Card ID so that Card ID will auto-iterate in the DB
            card_description = ("INSERT INTO cards "
                            "(`name`, `top`, `right`, `bottom`, `left`, `img_path`, `rarity`) "
                            "VALUES (%(name)s, %(top)s, %(right)s, %(bottom)s, %(left)s, %(img_path)s, %(rarity)s)")

            card_data = {
            'name': name,
            'top': top,
            'right': right,
            'bottom': bottom,
            'left': left,
            'img_path': img_path,
            'rarity': rarity,
            }
        else:
            #Card ID is specified
            #Insert using the specified Card ID
            card_description = ("INSERT INTO cards "
                            "(`card_id`,`name`, `top`, `right`, `bottom`, `left`, `img_path`, `rarity`) "
                            "VALUES (%(card_id)s,%(name)s, %(top)s, %(right)s, %(bottom)s, %(left)s, %(img_path)s, %(rarity)s)")

            card_data = {
            'card_id': card_id,
            'name': name,
            'top': top,
            'right': right,
            'bottom': bottom,
            'left': left,
            'img_path': img_path,
            'rarity': rarity,
            }

        # print(card_data)
        try:
            self.sql.exec(card_description, card_data)
            print("Successfully added card: {}".format(name))
            return True
        except:
            print("Failed to create card")
            return False

    def user_is_me(self,ctx):
        return ctx.message.author.id == '97417120815513600'

    def CardStats(self, card_id):
        cardQuery = self.sql.sel("SELECT top, right, bottom, left FROM cards WHERE card_id = {}".format(card_id))
        return cardQuery.fetchall()

def setup(client):
    client.add_cog(Cards(client))