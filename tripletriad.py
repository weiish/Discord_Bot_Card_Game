import discord
import time
import random
import images
import os
import tripletriadai as ttai
from enum import Enum
from discord.ext import commands
from operator import add

class TripleTriad:
    def __init__(self, client):
        self.client = client
        self.sql = client.cogs['SQL']
        self.player = client.cogs['Player']
        self.player.setReferences(client)
        self.cards = client.cogs['Cards']
        self.decks = client.cogs['Decks']
        self.games_in_session = []

    @commands.group(pass_context=True, aliases=['t', 'tt'])
    async def triad(self, ctx):
        if ctx.invoked_subcommand is None:
            await self.client.say('Invalid triad sub command')

    @triad.command(pass_context=True, brief="Win triple triad game instantly", description="This is the description", help="This is the help")
    async def cheat(self, ctx):
        player = ctx.message.author
        gameState = self.UserGameStateCheck(player.id)
        await self.EndGame(ctx.message.channel, gameState[1], losingPlayer=2)

    @triad.command(pass_context=True, aliases=['b','mygame'])
    async def board(self, ctx):
        #Check if player is in game
        player = ctx.message.author
        gameState = self.UserGameStateCheck(player.id)
        if gameState[0] == 1 or gameState[0] == 2:
            await self.OutputOpenBoard(ctx.message.channel, gameState[1])
        else:
            await self.client.say('You are not in a game, {}'.format(player.mention))

    @triad.command(pass_context=True, aliases=['ai','computer'])
    async def startai(self, ctx, ai_level=-1):
        player = ctx.message.author
        gameState = self.UserGameStateCheck(player.id)
        if gameState[0] > 0:
            await self.client.say('You are already in a game, {}'.format(player.mention))
            return

        await self.client.say("Enter the number of the deck you would like to use: ")
        await self.client.say(self.decks.list_decks(player.id, player.name))
        deck_index = await self.client.wait_for_message(author=ctx.message.author, timeout=10)
        deck_index = deck_index.clean_content
        try:
            deck_index = int(deck_index)
        except ValueError:
            await self.client.say("Invalid response - AI Game cancelled")
            return
        deck_id = self.decks.isValidDeck(player.id, deck_index)
        if deck_id == -1:
            await self.client.say("That deck is incomplete or does not exist")
            return

        # Check if an ai_deck_level was chosen, if not then ask for one
        # TODO - add a recommendation based on deck level of player
        if ai_level == -1:
            await self.client.say("Enter the level of AI you would like to face (1 to 10)")
            ai_level = await self.client.wait_for_message(author=ctx.message.author, timeout=10)
            ai_level = ai_level.clean_content
            try:
                ai_level = int(ai_level)
                if ai_level > 10 or ai_level < 1:
                    raise ValueError
            except ValueError:
                await self.client.say("Invalid response - AI Game cancelled")
                return

        ai_id = -ai_level
        ai_name = ttai.GetAIName(ai_id)
        wager = 'card'

        # TODO Assign random deck to AI based on level
        ai_deck_id = 18

        # TODO Ask for rules
        rules = [Rules.SAME, Rules.PLUS, Rules.OPEN]
        
        rules_packed = self.PackRules(rules)
        rule_output = ""
        for rule in rules:
            rule_output += rule.name + ' '

        (newGame_id, startingTurn) = self.StartGame(player.id, ai_id, player.name, ai_name, deck_id, ai_deck_id, wager, rules_packed)
        await self.client.say('Starting game of triple triad with {} vs {}! - Player {} goes first'.format(ctx.message.author.mention, ai_name, str(startingTurn)))
        await self.client.say("**Rules in play:** " + rule_output)

        await self.OutputOpenBoard(ctx.message.channel, newGame_id)

    @triad.command(pass_context=True, aliases=['c'])
    async def challenge(self, ctx, otherPlayer, wager=None):
        otherPlayer = ctx.message.mentions[0]
        player = ctx.message.author

        #Check if already in a game
        gameState = self.UserGameStateCheck(player.id)
        if gameState[0] > 2:
            await self.client.say('You are already in a lobby, {}'.format(player.mention))
            return

        if gameState[0] > 0:
            await self.client.say('You are already in a game, {}'.format(player.mention))
            return

        #Check if other player is already in a game
        gameState = self.UserGameStateCheck(otherPlayer.id)
        if gameState[0] > 2:
            await self.client.say('Your opponent is already in a lobby, {}'.format(player.mention))
            return
        
        if gameState[0] > 0:
            await self.client.say('Your opponent is already in a lobby, {}'.format(player.mention))
            return

        #Ask for the type of wager
        if not wager:
            await self.client.say("What type of wager would you like to set?\n    number - Money amount to wager\n    'card' - Winner picks one card to take from the loser's deck \n    'deck' - Winner takes the whole deck from the loser\n    'none' - No Wager")
            wager = await self.client.wait_for_message(author=ctx.message.author, timeout=10)
            wager = wager.clean_content.lower()

        #See if wager input is valid
        if wager == 'card':
            wager_text = 'The winner picks and takes **one card** from the deck of the loser'
        elif wager == 'deck':
            wager_text = 'The winner takes the **entire deck** of the loser'
        elif wager == 'none':
            wager_text = '**None**'
        else:
            try:
                wager = int(wager)
                #Check if both players have enough money
                if not self.player.player_has_money(player.id, wager):
                    await self.client.say("You don't have enough money to wager that - Challenge cancelled")
                    return
                if not self.player.player_has_money(otherPlayer.id, wager):
                    await self.client.say("Your opponent doesn't have enough money to wager that - Challenge cancelled")
                    return
                wager_text = 'The winner takes {} money from the loser'.format(str(wager))
                wager = str(wager)
            except ValueError:
                await self.client.say("Invalid response - Challenge cancelled")
                return

        #Ask for confirmation from the other player
        await self.client.say("{}! - {} is challenging you to a game of Triple Triad\n **Wager**: {} , **type 'confirm' to accept**.".format(otherPlayer.mention, player.mention, wager_text))

        response = await self.client.wait_for_message(author=otherPlayer, timeout=30)
        if not response:
            await self.client.say("{} did not accept the challenge".format(otherPlayer.name))
            return
        response = response.clean_content.lower()
        if response != 'confirm':
            await self.client.say("{} did not accept the challenge".format(otherPlayer.name))
            return

        #Remove money from both players if wager was money
        if wager != 'card' and wager != 'deck' and wager != 'none':
            self.player.rem_money(player.id, int(wager))
            self.player.rem_money(otherPlayer.id, int(wager))
            await self.client.say("Collecting wagers from both players...")

        #Ask each player in private message what deck they would like to use
            #Command to pick deck
        await self.client.send_message(player, "Please pick the deck you would like to use in your match against {}\n Use the **$t d #** command, where # is the number of the deck you want to use \n You may edit decks as needed prior to making your decision".format(otherPlayer.name))
        await self.client.send_message(player, self.decks.list_decks(player.id, player.name))

        await self.client.send_message(otherPlayer, "Please pick the deck you would like to use in your match against {}\n Use the **$t d #** command, where # is the number of the deck you want to use \n You may edit decks as needed prior to making your decision".format(player.name))
        await self.client.send_message(otherPlayer, self.decks.list_decks(otherPlayer.id, otherPlayer.name))

        #TODO implement rules here
        rules = [Rules.SAME, Rules.PLUS, Rules.OPEN]
        
        rules = self.PackRules(rules)

        #Add game_state to game lobby table, set both players to waiting for deck pick
        self.sql.exec("INSERT INTO ttlobbies (`player1_id`, `player2_id`, `player1_name`, `player2_name`, `deck1_id`, `deck2_id`, `wager`, `rules`, `game_channel`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                      (player.id, otherPlayer.id, player.name, otherPlayer.name, -1, -1, wager, rules, ctx.message.channel.id))
        await self.client.say("Lobby created for {} vs {}, please check your private messages to pick a deck".format(player.mention, otherPlayer.mention))


    @triad.command(pass_context=True,aliases=['d'])
    async def deck(self, ctx, deck_index):
        player = ctx.message.author
        gameState = self.UserGameStateCheck(player.id)
        if gameState[0] == 0:
            await self.client.say('You are not in a game lobby')
            return
        elif gameState[0] == 4:
            await self.client.say('Waiting on your opponent to pick a deck')
            return
        elif gameState[0] < 3:
            await self.client.say('You are in a game already')
            return
        else:
            #Check if deck_index is valid
            try:
                deck_index = int(deck_index)
            except ValueError:
                await self.client.say("That is an invalid deck number - Try again")
            deck_id = self.decks.isValidDeck(player.id, deck_index)
            if deck_id == -1:
                await self.client.say("That deck is incomplete or does not exist")
                return
            
            #Deck is valid, so set the player's deck index to that number
            if gameState[2] == 1: 
                #Player 1
                self.sql.exec("UPDATE ttlobbies SET deck1_id = {} WHERE lobby_id = {}".format(deck_id, gameState[1]))
            elif gameState[2] == 2:
                #Player 2
                self.sql.exec("UPDATE ttlobbies SET deck2_id = {} WHERE lobby_id = {}".format(deck_id, gameState[1]))
            await self.client.say("You have chosen your deck, {}".format(player.mention))

            #Check if both decks have been chosen, if so, start the game
            gameCheck = self.sql.sel("SELECT * FROM ttlobbies WHERE lobby_id = {}".format(gameState[1]))
            gameDetails = gameCheck.fetchone()
            if gameDetails[5] != -1 and gameDetails[6] != -1:
                gameChannel = self.client.get_channel(gameDetails[9])
            
                rules = self.UnpackRules(gameDetails[8])
                rule_output = ""
                for rule in rules:
                    rule_output += rule.name + ' '
            #Create game entry in ttgames
            #Delete lobby
                self.sql.exec("DELETE FROM ttlobbies WHERE lobby_id = {}".format(gameState[1]))
                (newGame_id, startingTurn) = self.StartGame(gameDetails[1], gameDetails[2], gameDetails[3], gameDetails[4], gameDetails[5], gameDetails[6], gameDetails[7], gameDetails[8])
                await self.client.send_message(gameChannel, "<@{}> and <@{}> have selected their decks, starting a game of Triple Triad! {} goes first".format(gameDetails[1], gameDetails[2],gameDetails[2+startingTurn]))
                await self.client.send_message(gameChannel, "**Rules in play:** " + rule_output)
                await self.OutputOpenBoard(gameChannel, newGame_id)

    @triad.command(pass_context=True)
    async def forfeit(self, ctx):
        player = ctx.message.author
        gameState = self.UserGameStateCheck(player.id)
        if gameState[0] == 0:
            await self.client.say('You are not in a game, {}'.format(player.mention))
        else:
            await self.EndGame(ctx.message.channel, gameState[1], losingPlayer=gameState[2])
            # await game.DeclareVictor(player.id,False)

    @triad.command(pass_context=True)
    async def games(self):
        cursor = self.sql.sel("SELECT COUNT(*) FROM ttgames")
        num_games = cursor.fetchone()[0]
        await self.client.say('Current games in session: {}'.format(str(num_games)))

    @triad.command(pass_context=True, aliases=['p', 'put', 'place'])
    async def play(self, ctx, hand_index, board_slot):
        #print ("PLAY " + hand_index + ' TO SLOT ' + board_slot)
        # Check if in game
        player = ctx.message.author
        gameState = self.UserGameStateCheck(player.id)
        if gameState[0] == 0:
            await self.client.say('You are not in a game')
            return
        elif gameState[0] == 2:
            await self.client.say('It is not your turn')
            return

        # Check hand_index is valid
        try:
            hand_index = int(hand_index)
            if hand_index < 1 or hand_index > 5:
                raise ValueError
        except ValueError:
            await self.client.say("Your hand index input of {} is invalid".format(hand_index))

        # Check board_slot is valid
        try:
            board_slot = int(board_slot)
            if board_slot < 1 or board_slot > 9:
                raise ValueError
        except ValueError:
            await self.client.say("Your board slot input of {} is invalid".format(board_slot))

        # Check if board slot is empty
        slotQuery = self.sql.sel("SELECT card_id FROM boardslots WHERE game_id = {} AND slot = {}".format(gameState[1], board_slot))
        slot_card_id = slotQuery.fetchone()[0]
        if slot_card_id > 0:
            await self.client.say('That play is invalid - A card is already in that position')
            return

        # Get card_id from hand, check that it isn't empty, then remove card from hand
        handQuery = self.sql.sel("SELECT card_id FROM handslots WHERE discord_id = {} AND slot_index = {}".format(player.id, hand_index))
        card_id = handQuery.fetchone()[0]
        if card_id == 0:
            await self.client.say('That play is invalid - That hand slot is empty')
            return

        # Play is valid, Remove card from hand
        self.sql.exec("UPDATE handslots SET card_id = 0 WHERE game_id = {} AND discord_id = {} AND slot_index = {}".format(gameState[1], player.id, hand_index))
        # Update the game state using the play
        flips = await self.UpdateGameState(ctx=ctx, game_id=gameState[1], slot_index=board_slot, card_id=card_id, player_num=gameState[2])
        await self.OutputOpenBoard(ctx.message.channel, gameState[1], flips=flips)

        if self.IsAIGame(gameState[1]):
            await self.ComputerPlayRandom(ctx, gameState[1])

    async def UpdateGameState(self, ctx, game_id, slot_index, card_id, player_num):
        # Pull card_id, and owner of other slots for the game board
        boardQuery = self.sql.sel("SELECT card_id, owner FROM boardslots WHERE game_id = {}".format(game_id))
        boardDetails = boardQuery.fetchall()

        # Unpack rules
        ruleQuery = self.sql.sel("SELECT rules FROM ttgames WHERE game_id = {}".format(game_id))        
        rules = ruleQuery.fetchone()
        rules = rules[0]
        rules = self.UnpackRules(rules)

        #First Power Flip Check
        flip_list = self.CardPowerCheck(card_id, slot_index, boardDetails, False, player = player_num)
        
        #Rule check to see which cards should be flipped according to Plus or Same
        rule_flipped_cards = self.CardRuleCheck(rules, card_id, slot_index, boardDetails, player = player_num)
        
        combo_list = rule_flipped_cards.copy()
        combo_flipped_cards = []
        combo_flipped_slots = []

        combo_iterations = 0
        while len(combo_list) > 0:
            current_slot = combo_list.pop()[0]
            combo_card_id = boardDetails[current_slot-1][0]
            combo_card_owner = boardDetails[current_slot-1][1]
            if current_slot != -1 and current_slot not in combo_flipped_slots and combo_card_owner != player_num:
                new_flipped_cards = self.CardPowerCheck(combo_card_id, current_slot, boardDetails, True, player=player_num)                
                combo_list += new_flipped_cards
                combo_flipped_cards += new_flipped_cards
            combo_flipped_slots.append(current_slot)
            combo_iterations += 1
            if combo_iterations > 25:
                return

        flip_list = rule_flipped_cards + combo_flipped_cards + flip_list

        alreadyFlipped = []
        flip_record = []
        # Update board slots as needed, starting with rule_flipped_cards
        for (slot, flipReason, flipOrigin) in flip_list:
            if slot > 0 and slot < 10 and slot not in alreadyFlipped:
                if boardDetails[slot-1][1] != player_num:
                    await self.FlipCard(game_id, slot, flipReason)
                    alreadyFlipped.append(slot)
                    flip_record.append((slot, flipReason, flipOrigin, player_num))

        # Update the board to indicate the new card has been placed
        self.sql.exec("UPDATE boardslots SET card_id = {}, owner = {} WHERE game_id = {} and slot = {}".format(card_id, player_num, game_id, slot_index))

        # Update the turn number
        self.sql.exec("UPDATE ttgames SET turn = IF(turn=1,2,1), totalturns = totalturns + 1")
        # Check for end game conditions
        turnQuery = self.sql.sel("SELECT totalturns FROM ttgames WHERE game_id = {}".format(game_id))
        totalturns = turnQuery.fetchone()[0]

        if totalturns == 9:
            winner = self.CheckWinner(game_id)
            await self.EndGame(ctx.message.channel, game_id, winningPlayer=winner, flips=flip_record)
        
        return flip_record

    async def ComputerPlayRandom(self, ctx, game_id):
        gameQuery = self.sql.sel("SELECT game_id FROM ttgames WHERE game_id = {}".format(game_id))
        if not gameQuery.rowcount:
            return

        time.sleep(5)
        # Get state of hand
        handQuery = self.sql.sel("SELECT slot_index, card_id FROM handslots WHERE game_id = {} AND discord_id < 0".format(game_id))
        handDetails = handQuery.fetchall()

        # Get state of board
        boardQuery = self.sql.sel("SELECT slot, card_id FROM boardslots WHERE game_id = {}".format(game_id))
        boardDetails = boardQuery.fetchall()

        # Generate a random number for hand slot until a valid one is chosen
        card_id = -1
        boardIndex = -1

        while card_id == -1:
            randomHandIndex = random.randint(0, 4)
            if handDetails[randomHandIndex][1] != 0:
                card_id = handDetails[randomHandIndex][1]

        # Generate a random number for board slot until a valid one is chosen
        while boardIndex == -1:
            randomBoardIndex = random.randint(0, 8)
            if boardDetails[randomBoardIndex][1] == 0:
                boardIndex = randomBoardIndex

        # Remove card from computer's hand
        self.sql.exec("UPDATE handslots SET card_id = 0 WHERE game_id = {} AND discord_id < 0 AND slot_index = {}".format(game_id, randomHandIndex+1))

        # Play the card in the board slot
        flips = await self.UpdateGameState(ctx=ctx, game_id=game_id, slot_index=boardIndex+1, card_id=card_id, player_num=2)
        await self.OutputOpenBoard(ctx.message.channel, game_id, flips=flips)

    def CheckWinner(self, game_id):
        boardQuery = self.sql.sel("SELECT owner FROM boardslots WHERE game_id = {}".format(game_id))
        owners = boardQuery.fetchall()
        p1 = 0
        p2 = 0
        for owner in owners:
            if owner[0] == 1:
                p1 += 1
            elif owner[0] == 2:
                p2 += 1
        if p1 > p2:
            return 1
        else:
            return 2

    def GetAdjacentSlots(self, slot):
        adjacent_slots = [-1, -1, -1, -1]
        # Top
        if slot > 3:
            adjacent_slots[0] = slot-3
        # Right
        if not (slot % 3 == 0):
            adjacent_slots[1] = slot+1
        # Bottom
        if slot < 7:
            adjacent_slots[2] = slot+3
        # Left
        if not ((slot + 2) % 3 == 0):
            adjacent_slots[3] = slot-1
        return adjacent_slots

    def CardRuleCheck(self, rules, centerCard_id, centerCard_slot, boardDetails, player):
        # Returns result, which is a list of slot numbers that should be owned according to the rules applied
        result = []
        adjacent_slots = self.GetAdjacentSlots(centerCard_slot)
        adjacent_card_ids = []
        adjacent_stats = []
        adjacent_owner = []

        # Get Card Stats of adjacent slots
        for slot in adjacent_slots:
            if slot > 0:
                adjacent_card_ids.append(boardDetails[slot-1][0])
                adjacent_owner.append(boardDetails[4])
            else:
                adjacent_card_ids.append(-1)
                adjacent_owner.append(-1)

        centerCard = self.cards.get_card(centerCard_id)
        centerStats = []
        statIndexes = [4, 5, 2, 3]

        for x in range(4):
            centerStats.append(centerCard[x+2]) #Gets Top, right, bottom, and left stat of main card
            if adjacent_slots[x] > 0:
                if adjacent_card_ids[x] > 0:
                    #Gets bottom stat of top card, left stat of right card... etc
                    adjacent_stats.append(self.cards.get_card(adjacent_card_ids[x])[statIndexes[x]])
                else:
                    adjacent_stats.append(-1)
            else:
                adjacent_stats.append(10)
        
        if Rules.SAME in rules:
            #print("Checking SAME")
            same_indexes = []
            for x in range(4):
                #print(str(centerStats[x]) + ' == ' + str(adjacent_stats[x]) + '?')
                if centerStats[x] == adjacent_stats[x] and adjacent_stats[x] != -1:
                    #print('Yes')
                    same_indexes.append(x)
            if len(same_indexes) > 1:
                for index in same_indexes:
                    if adjacent_owner[index] != player:
                        result.append((adjacent_slots[index], 'SAME', centerCard_slot))
                    #print("SAME RULE APPLIED TO " + str(adjacent_slots[index]))
            
            
        if Rules.PLUS in rules:
            sums = list(map(add, centerStats, adjacent_stats))
            #Check for duplicates in sums, and find their indexes if there are any
            seen = set()
            dupes = []
            counter = 0
            for x in sums:
                if adjacent_stats[counter] != -1:
                    if x in seen and x not in dupes:
                        dupes.append(x)
                    else:
                        seen.add(x)
                counter = counter + 1
            if len(dupes) > 0:
                for dupe in dupes:
                    #Find indexes of dupes
                    indexes = [i for i, x in enumerate(sums) if x == dupe]
                    for index in indexes:
                        if not (adjacent_slots[index], 'SAME', centerCard_slot) in result: #Don't add it if it's already been applied as a SAME
                            if adjacent_owner[index] != player:
                                result.append((adjacent_slots[index], 'PLUS', centerCard_slot))
                            
        
        return result

    def CardPowerCheck(self, centerCard_id, centerCard_slot, boardDetails, isComboCheck, player):
        adjacent_slots = self.GetAdjacentSlots(centerCard_slot)
        adjacent_card_ids = []
        adjacent_owner = []
        if isComboCheck:
            reason = "COMBO"
        else:
            reason = "POWER"

        # Get Card Stats of adjacent slots
        for slot in adjacent_slots:
            if slot > 0:
                adjacent_card_ids.append(boardDetails[slot-1][0])
                adjacent_owner.append(boardDetails[4])
            else:
                adjacent_card_ids.append(-1)
                adjacent_owner.append(-1)

        # Returns result, which is a list of slot numbers that should be owned according to power
        result = []
        centerCard = self.cards.get_card(centerCard_id)
        #print("CENTER CARD IS")
        #print(centerCard)
        # Top
        if adjacent_card_ids[0] > 0 and adjacent_owner[0] != player:
            adjacentCard = self.cards.get_card(adjacent_card_ids[0])
            #print("Adjacent Card is...")
            #print(adjacentCard)
            #print("Checking Main vs Top - {} vs {}".format(str(mainCard[2]), str(adjacentCard[4])))
            if centerCard[2] > adjacentCard[4]:
                result.append((adjacent_slots[0], reason, centerCard_slot))

        # Right
        if adjacent_card_ids[1] > 0 and adjacent_owner[0] != player:
            adjacentCard = self.cards.get_card(adjacent_card_ids[1])
            #print("Checking Main vs Right - {} vs {}".format(str(mainCard[3]), str(adjacentCard[5])))
            if centerCard[3] > adjacentCard[5]:
                result.append((adjacent_slots[1], reason, centerCard_slot))

        # Bottom
        if adjacent_card_ids[2] > 0 and adjacent_owner[0] != player:
            adjacentCard = self.cards.get_card(adjacent_card_ids[2])
            #print("Checking Main vs Bottom - {} vs {}".format(str(mainCard[4]), str(adjacentCard[2])))
            if centerCard[4] > adjacentCard[2]:
                result.append((adjacent_slots[2], reason, centerCard_slot))

        # Left
        if adjacent_card_ids[3] > 0 and adjacent_owner[0] != player:
            adjacentCard = self.cards.get_card(adjacent_card_ids[3])
            #print("Checking Main vs Left - {} vs {}".format(str(mainCard[5]), str(adjacentCard[3])))
            if centerCard[5] > adjacentCard[3]:
                result.append((adjacent_slots[3], reason, centerCard_slot))

        return result

    async def FlipCard(self, game_id, slot_index, reason):
        # Do things that add to the image? Or output text
        #await self.client.say("Flipping card in slot {} with {}".format(str(slot_index), reason))
        self.sql.exec("UPDATE boardslots SET owner = IF(owner = 1, 2, 1) WHERE game_id = {} AND slot = {}".format(game_id, slot_index))

    async def on_game_end(self, game):
        if game in self.games_in_session:
            self.games_in_session.remove(game)

    def UserGameStateCheck(self, userID):
        # Returns 0 if player is not in game
        #         1 if player is in game and it is their turn
        #         2 if player is in game but it is NOT their turn
        #         3 if player is in lobby and needs to pick a deck
        #         4 if player is in lobby and is waiting on their opponent to pick a deck
        # Returns game_id as 2nd value of tuple
        # Returns player's player number as 3rd value of tuple
        cursor = self.sql.sel("SELECT turn, player1_id, player2_id, game_id FROM ttgames WHERE player1_id = {} OR player2_id = {}".format(userID, userID))
        if cursor.rowcount > 0:
            gameDetails = cursor.fetchone()
            if userID == gameDetails[1]:
                playerNum = 1
            elif userID == gameDetails[2]:
                playerNum = 2

            if (gameDetails[0] == playerNum):
                return (1, gameDetails[3], playerNum)
            else:
                return (2, gameDetails[3], playerNum)
        else:
            cursor = self.sql.sel("SELECT player1_id, player2_id, deck1_id, deck2_id, lobby_id FROM ttlobbies WHERE player1_id = {} OR player2_id = {}".format(userID, userID))
            if cursor.rowcount > 0:
                lobbyDetails = cursor.fetchone()
                lobby_id = lobbyDetails[4]
                if userID == lobbyDetails[0]:
                    #Player is player 1
                    if lobbyDetails[2] == -1:
                        #Player needs to pick a deck
                        return (3, lobby_id, 1)
                    elif lobbyDetails[3] == -1:
                        #Player is waiting on opponent
                        return (4, lobby_id, 1)
                elif userID == lobbyDetails[1]:
                    #Player is player 2
                    if lobbyDetails[3] == -1:
                        #Player needs to pick a deck
                        return (3, lobby_id, 2)
                    elif lobbyDetails[2] == -1:
                        #Player is waiting on opponent
                        return (4, lobby_id, 2)
                
            return (0, -1, -1)

    async def EndGame(self, channel, game_id, winningPlayer=-1, losingPlayer=-1, flips=None):
        # Get player IDs
        playerQuery = self.sql.sel("SELECT player1_id, player2_id, player1_name, player2_name, wager, deck1_id, deck2_id, game_type FROM ttgames WHERE game_id = {}".format(game_id))
        playerInfo = playerQuery.fetchall()[0]
        wager = playerInfo[4]
        gameType = playerInfo[7]
        if winningPlayer == 1 or losingPlayer == 2:
            losingPlayer = 2
            winningPlayer = 1
            losingDeck = playerInfo[6]            
        elif winningPlayer == 2 or losingPlayer == 1:
            losingPlayer = 1
            winningPlayer = 2
            losingDeck = playerInfo[5]
        
        if gameType == 'pve':
            if winningPlayer == 2:
                winningUser = playerInfo[3]
                losingName = await self.client.get_user_info(playerInfo[losingPlayer-1])
            else:
                winningUser = await self.client.get_user_info(playerInfo[winningPlayer-1])
                losingName = playerInfo[3]
        else:
            winningUser = await self.client.get_user_info(playerInfo[winningPlayer-1])
            losingUser = await self.client.get_user_info(playerInfo[losingPlayer-1])
            losingName = losingUser.name
        
        # Declare Winner
        await self.OutputOpenBoard(channel, game_id, winningPlayer, flips=flips)

        # Get Wager, distribute rewards
        try:
            wager = int(wager) * 2
            #Money wager, give 2X wager to winning player
            await self.client.say("Paying {} to {}".format(wager, winningUser.mention))
            self.player.add_money(winningUser.id, wager)            
        except ValueError:
            if wager == 'card':
                if gameType == 'pvp':
                    #Handle Card Reward
                    #Ask winning player for a card to take from the losing player
                    await self.client.say("{}, please select the card you wish to take from {}'s deck (1-5)".format(winningUser.mention, losingName))
                    tempDeckImg = self.decks.generate_deck(losingDeck)
                    await self.client.send_file(channel, tempDeckImg.name)
                    cardTransferred = False
                    while not cardTransferred:
                        card_index = await self.client.wait_for_message(author=winningUser, timeout=1000)
                        card_index = card_index.clean_content
                        try:
                            card_index = int(card_index)
                            if card_index < 1 or card_index > 5:
                                raise ValueError                            
                            #Valid input, take card from losing player and give to winning player
                            #Get card_id of card
                            card_id = self.sql.sel("SELECT card_id FROM deckslots WHERE deck_id = {} AND slot_index = {}".format(losingDeck, card_index))
                            card_id = card_id.fetchone()[0]
                            cardDetails = self.cards.get_card(card_id)                            
                            await self.player.rem_item_from_inventory(losingUser.id, card_id, 1)
                            self.player.add_item_to_inventory(winningUser.id, card_id, 1)
                            await self.client.say("{} took ***{}*** from {}".format(winningUser.mention, cardDetails[1], losingUser.mention))
                            cardTransferred = True                        
                        except ValueError:
                            await self.client.say("Invalid response - Try again")
                elif gameType == 'pve': 
                    if winningPlayer == 1:
                        #Handle Card Reward
                        #Ask winning player for a card to take from the losing player
                        await self.client.say("{}, please select the card you wish to take from {}'s deck (1-5)".format(winningUser.mention, losingName))
                        tempDeckImg = self.decks.generate_deck(losingDeck)
                        await self.client.send_file(channel, tempDeckImg.name)
                        cardTransferred = False
                        while not cardTransferred:
                            card_index = await self.client.wait_for_message(author=winningUser, timeout=1000)
                            card_index = card_index.clean_content
                            try:
                                card_index = int(card_index)
                                if card_index < 1 or card_index > 5:
                                    raise ValueError                            
                                #Valid input, take card from losing player and give to winning player
                                #Get card_id of card
                                card_id = self.sql.sel("SELECT card_id FROM deckslots WHERE deck_id = {} AND slot_index = {}".format(losingDeck, card_index))
                                card_id = card_id.fetchone()[0]
                                cardDetails = self.cards.get_card(card_id)                          
                                self.player.add_item_to_inventory(winningUser.id, card_id, 1)
                                await self.client.say("{} took ***{}*** from {}".format(winningUser.mention, cardDetails[1], losingName))
                                cardTransferred = True                        
                            except ValueError:
                                await self.client.say("Invalid response - Try again")
                    else:
                        await self.client.say("You lost your wager against the AI")
            elif wager == 'deck':
                #Handle Deck Reward
                deckQuery = self.sql.sel("SELECT card_id FROM deckslots WHERE deck_id = {}".format(losingDeck))
                deckDetails = deckQuery.fetchall()
                cardString = "{} took ".format(winningUser.mention)
                for card in deckDetails:
                    card_id = card[0]
                    cardDetails = self.cards.get_card(card_id)
                    await self.player.rem_item_from_inventory(losingUser.id, card_id, 1)
                    self.player.add_item_to_inventory(winningUser.id, card_id, 1)
                    cardString = cardString + "***{}***      ".format(cardDetails[1])                    
                    await self.client.say(cardString + " from {}".format(losingUser.mention))                    
            elif wager == 'none':
                #Acknowledge that no reward will be given
                await self.client.say("This was a free match, so no wager will be paid")
                return
                    
        #await self.client.say("Game between {} and {} has ended! {} emerges victorious!".format(playerInfo[2], playerInfo[3], winName))
        self.sql.exec("DELETE FROM ttgames WHERE player1_id = {} or player2_id = {}".format(playerInfo[0], playerInfo[1]))
        self.sql.exec("DELETE FROM handslots WHERE game_id = {} AND discord_id = {}".format(game_id, -1))
        self.sql.exec("DELETE FROM boardslots WHERE game_id = {}".format(game_id))

    def StartGame(self, discord_id1, discord_id2, name1, name2, deck_id1, deck_id2, wager, rules):
        if discord_id2 == -1:
            gametype = "pve"
        else:
            gametype = "pvp"
        #startingTurn = random.randint(1, 2)
        startingTurn = 1
        self.sql.exec("INSERT INTO ttgames (`game_type`, `player1_id`, `player2_id`, `player1_name`, `player2_name`, `deck1_id`, `deck2_id`, `wager`, `turn`, `rules`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                      (gametype, discord_id1, discord_id2, name1, name2, deck_id1, deck_id2, wager, startingTurn, rules))

        cursor = self.sql.sel("SELECT game_id FROM ttgames WHERE player1_id = {} AND player2_id = {}".format(discord_id1, discord_id2))
        game_id = cursor.fetchone()[0]
        self.PrepareNewBoard(game_id)
        self.PrepareHand(discord_id1, deck_id1, game_id)
        self.PrepareHand(discord_id2, deck_id2, game_id)
        return (game_id, startingTurn)

    def IsAIGame(self, game_id):
        cursor = self.sql.sel("SELECT game_type FROM ttgames WHERE game_id = {}".format(game_id))        
        if not cursor.rowcount:
            return False
        if cursor.fetchone()[0] == 'pve':
            return True
        return False

    def PackRules(self, rules):
        packedRules = ''
        for rule in rules:
            packedRules = packedRules + rule.value
        return packedRules

    def UnpackRules(self, rules):
        ruleList = []
        if 'S' in rules:
            ruleList.append(Rules.SAME)
        if 'P' in rules:
            ruleList.append(Rules.PLUS)
        if 'O' in rules:
            ruleList.append(Rules.OPEN)
        if 'C' in rules:
            ruleList.append(Rules.CLOSED)
        return ruleList

    def PrepareNewBoard(self, game_id):
        for x in range(9):
            self.sql.exec("INSERT INTO boardslots (game_id, slot, card_id, owner) VALUES ({}, {}, {}, {})".format(game_id, x+1, 0, 0))

    def PrepareHand(self, discord_id, deck_id, game_id):
        # Insert new hand row using deck if needed, otherwise clear the hand and insert the deck cards
        # Get info of deck
        if (discord_id == -1):
            cursor = self.sql.sel("SELECT handslot_id FROM handslots WHERE discord_id = {} AND game_id = {}".format(discord_id, game_id))
        else:
            cursor = self.sql.sel("SELECT handslot_id FROM handslots WHERE discord_id = {}".format(discord_id))
        if not cursor.rowcount:
            # No existing hand slots yet, so create them
            for x in range(5):
                self.sql.exec("INSERT INTO handslots (game_id, discord_id, slot_index, card_id) VALUES ({}, {}, {}, (SELECT card_id FROM deckslots WHERE deck_id = {} AND slot_index = {}))".format(
                    game_id, discord_id, x+1, deck_id, x+1))
        else:
            # Already have an existing hand so update them
            for x in range(5):
                self.sql.exec("UPDATE handslots SET game_id = {},card_id = (SELECT card_id FROM deckslots WHERE deck_id = {} AND slot_index = {}) WHERE discord_id = {} AND slot_index = {}".format(
                    game_id, deck_id, x+1, discord_id, x+1))

    async def OutputOpenBoard(self, channelObject, game_id, winner=None, flips=None):
        gameQuery = self.sql.sel("SELECT game_type, player1_id, player2_id, player1_name, player2_name, wager, turn, rules FROM ttgames WHERE game_id = {}".format(game_id))
        gameDetails = gameQuery.fetchall()
        for (game_type, player1_id, player2_id, player1_name, player2_name, wager, turn,rules ) in gameDetails:
            rules = self.UnpackRules(rules)
            hand1Img = await self.cards.GetHand(game_id, player1_id, 2, 1)
            hand2Img = await self.cards.GetHand(game_id, player2_id, 2, 2)
            boardImg = self.cards.GetBoard(game_id, flips)
            if winner:
                turn = -1 * winner
            gameImg = images.generate_game(hand1Img, hand2Img, boardImg, player1_name, player2_name, rules=rules, wager=wager, turn=turn)
            await self.client.send_file(channelObject, gameImg.name)
            gameImg.close()
            os.remove(gameImg.name)

class Rules(Enum):
    SAME = 'S'
    PLUS = 'P'
    OPEN = 'O'
    CLOSED = 'C'


def setup(client):
    client.add_cog(TripleTriad(client))
