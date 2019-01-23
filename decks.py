import discord
import images
from discord.ext import commands
import os
import re

class Decks:
    def __init__(self, client):
        self.client = client
        self.sql = client.cogs['SQL']
        self.player = client.cogs['Player']
        self.cards = client.cogs['Cards']
        self.maxdecks = 10
    
    @commands.group(pass_context=True, aliases=['d'])
    async def deck(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.client.say('Invalid deck sub command')

    @deck.command(name='list', pass_context=True, aliases=['l'])
    async def _list(self, ctx):
        author = ctx.message.author
        await self.client.say(self.list_decks(author.id, author.name))

    @deck.command(name='new', pass_context=True, aliases=['n'])
    async def _new(self,ctx):
        author = ctx.message.author
        deckData = self.sql.sel("SELECT name, list_order FROM decks WHERE discord_id = {} ORDER BY list_order".format(author.id))
        if deckData.rowcount > 9:
            await self.client.say("You already have the max number of decks (10)")
            return
        
        await self.client.say("Please enter a name for your deck, limit 15 characters: ")
        nameResponse = await self.client.wait_for_message(author=ctx.message.author, timeout=10)

        if len(nameResponse.clean_content) > 15:
            await self.client.say('Only 15 characters allowed. Cancelling deck creation')
        else:
            new_deck_index = deckData.rowcount + 1
            self.sql.exec("INSERT INTO decks (`discord_id`, `name`, `list_order`) VALUES (%s, %s, %s)", (
                author.id, nameResponse.clean_content, new_deck_index))  
            deckID = self.sql.sel("SELECT deck_id FROM decks WHERE discord_id = {} AND list_order = {}".format(author.id, new_deck_index))
            deckID = deckID.fetchone()[0]
            for x in range(5):
                self.sql.exec("INSERT INTO deckslots (`deck_id`, `slot_index`, `card_id`) VALUES (%s, %s, %s)", (
                deckID, x+1, 0))       
            await self.client.say('New Deck: **{}** created for {}'.format(nameResponse.clean_content, ctx.message.author.mention))        


        #Query to check number of existing decks, if equal to MAX DECKS, alert
        #Else create new deck, get name
        return
    
    @deck.command(name='clear', pass_context=True, aliases=['c'])
    async def _clear(self, ctx, deck_index=-1):
        if deck_index == -1:
            await self.client.say("Enter the number of the deck you would like to clear: ")
            deck_index = await self.client.wait_for_message(author=ctx.message.author, timeout=10)
            deck_index = deck_index.clean_content
            try:
                deck_index = int(deck_index)
                if deck_index > self.maxdecks:
                    raise ValueError
            except ValueError:
                await self.client.say("Invalid response - Clear cancelled")
                return

        author = ctx.message.author
        deckData = self.sql.sel("SELECT deck_id, name, list_order FROM decks WHERE discord_id = {} AND list_order = {}".format(author.id,deck_index))
        if not deckData.rowcount:
            await self.client.say("You don't have a deck numbered {}".format(deck_index))
            return
        else:
            await self.client.say("Please type 'confirm' to confirm that you would like to clear this deck: ")
            deck_id = deckData.fetchone()[0]
            deckImage = self.generate_deck(deck_id)
            #Output Deck Here
            await self.client.send_file(ctx.message.channel, deckImage.name)
            #delete temp file
            deckImage.close()
            os.remove(deckImage.name)
            response = await self.client.wait_for_message(author=ctx.message.author, timeout=10)
            if response.clean_content.lower() == 'confirm':
                #Clear Deck
                self.sql.exec("UPDATE deckslots SET card_id = 0 WHERE deck_id = {}".format(deck_id))
                await self.client.say("Deck cleared")
            else:
                await self.client.say("Deck clearing cancelled")
        return

    @deck.command(name='delete', pass_context=True, aliases=['d'])
    async def _delete(self, ctx, deck_index=-1):
        #
        return

    @deck.command(name='add', pass_context=True, aliases=['a'])
    async def add(self, ctx, deck_index, cardSearchTerm):
        if not deck_index:
            deck_index = -1
        if not cardSearchTerm:
            cardSearchTerm = -1
        #No deck_index argument given, ask for it
        if deck_index == -1:
            await self.client.say("Enter the number of the deck you would like to add a card to: ")
            deck_index = await self.client.wait_for_message(author=ctx.message.author, timeout=10)
            deck_index = deck_index.clean_content
            try:
                deck_index = int(deck_index)
                if deck_index > self.maxdecks:
                    raise ValueError
            except ValueError:
                await self.client.say("Invalid response - Add Card cancelled")
                return
        
        try:
            if cardSearchTerm == -1:
                await self.client.say("Enter the ID or name of the card you would like to add: ")
                cardSearchTerm = await self.client.wait_for_message(author=ctx.message.author, timeout=10)
                cardSearchTerm = cardSearchTerm.clean_content
        except:
            print("Issue in decks.add")
        card_id = self.cards.get_card_id(cardSearchTerm)

        author = ctx.message.author
        deckData = self.sql.sel("SELECT deck_id, name, list_order FROM decks WHERE discord_id = {} AND list_order = {}".format(author.id,deck_index))
        if not deckData.rowcount:
            await self.client.say("You don't have a deck numbered {}".format(deck_index))
            return
        else:
            deckData = deckData.fetchone()
            deck_id = deckData[0]
            num_cards = self.get_num_cards(deck_id)
            card_index = None

            #CHECK CARD ID
            if card_id == -1:
                await self.client.say("Card ID is invalid, that card does not exist")
                return

            #CHECK CARD IS IN INVENTORY AND PLAYER HAS ENOUGH OF THEM TO USE ANOTHER IN THE DECK
            #Pull deck cards to see what cards are already being used
            deckDetails = self.sql.sel("SELECT card_id FROM deckslots WHERE deck_id = {} ORDER BY slot_index".format(deck_id))
            tempDeckDictionary = {str(card_id):1}
            deckHasCards = False
            for _card_id in deckDetails:
                if _card_id[0] == 0:
                    continue
                if str(_card_id[0]) in tempDeckDictionary:
                    tempDeckDictionary[str(_card_id[0])] += 1
                else:
                    tempDeckDictionary[str(_card_id[0])] = 1
                deckHasCards = True

            if deckHasCards:
                if not self.player.player_deck_is_valid(author.id, tempDeckDictionary):
                    await self.client.say("You don't have enough of that card to add it")
                    return
            
            #IF DECK FULL, ASK FOR CARD TO REPLACE            
            if num_cards == 5:
                await self.client.say("Your deck is full, enter the position of the card you would like to replace: ")
                deckImage = self.generate_deck(deck_id)
                await self.client.send_file(ctx.message.channel, deckImage.name)
                deckImage.close()
                os.remove(deckImage.name)
                card_index = await self.client.wait_for_message(author=ctx.message.author, timeout=10)
                card_index = card_index.clean_content
                try:
                    card_index = int(card_index)
                    if card_index > 5 or card_index < 1:
                        raise ValueError
                except ValueError:
                    await self.client.say("Invalid response - Add Card cancelled")
                    return
            
            if not card_index:
                card_index = self.find_first_empty_slot(deckData[0])
            
            
            self.sql.exec("UPDATE deckslots SET card_id = {} WHERE deck_id = {} AND slot_index = {}".format(card_id, deck_id, card_index))
            cardInfo = self.cards.query_card_by_id(card_id)
            cardName = cardInfo.fetchone()[1]
            await self.client.say("Added **{}** to your **{}** deck, {}".format(cardName, deckData[1], author.mention))

        #Check if card exists and is in inventory
        return

    def find_first_empty_slot(self, deck_id):
        deckQuery = self.sql.sel("SELECT slot_index FROM deckslots WHERE deck_id = {} AND card_id = 0".format(deck_id))
        if not deckQuery.rowcount:
            return -1
        
        deckDetails = deckQuery.fetchone()
        return deckDetails[0]
    
    def get_num_cards(self, deck_id):
        deckQuery = self.sql.sel("SELECT slot_index FROM deckslots WHERE deck_id = {} AND card_id != 0".format(deck_id))
        if not deckQuery.rowcount:
            return 0
        else:
            return deckQuery.rowcount
    @deck.command(name='remove', pass_context=True, aliases=['r'])
    async def remove(self, ctx, deck_index, card_index):
        #
        return

    @deck.command(name='show', pass_context=True, aliases=['s'])
    async def show(self, ctx, deck_index):
        author = ctx.message.author
        deckData = self.sql.sel("SELECT deck_id, name, list_order FROM decks WHERE discord_id = {} AND list_order = {}".format(author.id,deck_index))
        if not deckData.rowcount:
            await self.client.say("You don't have a deck numbered {}".format(deck_index))
            return
        else:
            deck_id = deckData.fetchone()[0]
            deckImage = self.generate_deck(deck_id)
            await self.client.send_file(ctx.message.channel, deckImage.name)
            deckImage.close()
            os.remove(deckImage.name)
    
    @deck.command(name='rename', pass_context=True, aliases=['rn'])
    async def rename(self, ctx, deck_index, newName):

        return

    def remove_from_deck(self, deck_id, card_id):
        deckQuery = self.sql.sel("SELECT slot_index FROM deckslots WHERE deck_id = {} AND card_id = {}".format(deck_id, card_id))
        if deckQuery.rowcount:
            deckDetails = deckQuery.fetchall()
            for slot_index in deckDetails:
                slot_index = slot_index[0]
                self.sql.exec("UPDATE deckslots SET card_id = 0 WHERE deck_id = {} AND slot_index = {}".format(deck_id, slot_index))
                print("Removed first instance of {} from deck {}".format(card_id, deck_id))
                return
        else:
            print("Decks.remove_from_deck unable to remove card because it wasn't the deck")
        #Check if card_id is in deck_id

        #If it is, remove it
        return
    def generate_deck(self, deck_id):
        deckDetails = self.sql.sel("SELECT card_id FROM deckslots WHERE deck_id = {} ORDER BY slot_index".format(deck_id))
        tempImages = []
        deckDetails = deckDetails.fetchall()
        for card_id in deckDetails:
            if card_id[0] < 1:
                #generate default image
                tempCard = images.generate_blank_card(1)
                tempCard = images.add_card_ownership_background(tempCard, 0)
                tempImages.append(tempCard)
            else:
                cardDetails = self.cards.get_card(card_id[0])
                tempCard = images.generate_card_img(1,cardDetails[0], cardDetails[1], cardDetails[2], cardDetails[3], cardDetails[4], cardDetails[5], cardDetails[6], cardDetails[7])
                tempCard = images.add_card_ownership_background(tempCard, 0)
                tempImages.append(tempCard)
        return images.generate_hand(tempImages)
        
    def list_decks(self, discord_id, discord_name):
        deckQuery = self.sql.sel("SELECT deck_id, name, list_order FROM decks WHERE discord_id = {} ORDER BY list_order".format(discord_id))
        if not deckQuery.rowcount:
            return "You don't have any decks"
        else:
            deckQuery = deckQuery.fetchall()
            outputString = "```{}'s Decks\n------------------------\n".format(discord_name)
            for (deck_id, name, list_order) in deckQuery:
                num_cards = self.get_num_cards(deck_id)
                outputCards = ""
                #Get Deck Info - Avg Rank, and Card Names in deck
                outputString = outputString + "{}. {} ({} cards) - ".format(str(list_order),name,str(num_cards))
                cardQuery = self.sql.sel("SELECT card_id FROM deckslots WHERE deck_id = {} ORDER BY slot_index".format(deck_id))
                rankSum = 0
                cardQuery = cardQuery.fetchall()
                first = True
                for card_id in cardQuery:
                    cardDetails = self.cards.get_card(card_id[0])
                    if cardDetails:
                        if first:
                            divider = " "
                            first = False
                        else:
                            divider = " / "
                        outputCards = outputCards + divider + cardDetails[1]
                        rankSum += cardDetails[7]
                if num_cards > 0:
                    avgRank = rankSum / num_cards
                else:
                    avgRank = 0
                outputString = outputString + "(Avg Rank: {}) - ".format(str(avgRank)) + outputCards + "\n"
            outputString = outputString + "```"
            return outputString

    def isValidDeck(self, discord_id, deck_index):
        deckData = self.sql.sel("SELECT deck_id FROM decks WHERE discord_id = {} AND list_order = {}".format(discord_id,deck_index))
        deck_id = deckData.fetchone()[0]
        num_cards = self.get_num_cards(deck_id)
        if not deckData.rowcount or num_cards < 5:
            return -1
        return deck_id

def setup(client):
    client.add_cog(Decks(client))