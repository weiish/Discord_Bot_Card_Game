from PIL import Image, ImageFilter, ImageDraw, ImageFont  # imports the library
import os.path
import tempfile
import io
import math
import config

large_card_width = 200
large_card_height = 205
medium_card_width = 115
medium_card_height = 120
small_card_width = 75
small_card_height = 80
large_stat_font_size = 30
medium_stat_font_size = 28
small_stat_font_size = 25
inner_border = 4
outer_border = 4
hand_spacing = 2
flip_indicator_short = 24
flip_indicator_long = 120
amount_border_size = 25

card_amount_path = r'C:\Windows\Fonts\phagspab.ttf'
game_font_path = r'C:\Windows\Fonts\phagspab.ttf'
card_stat_font_path = r'C:\Windows\Fonts\phagspab.ttf'
card_rarity_font_path = r'C:\Windows\Fonts\phagspab.ttf'
card_rarity_star_font_path = r'C:\Windows\Fonts\ARIALUNI_2.TTF'
flip_indicator_font_path = r'C:\Windows\Fonts\Inconsolata-Bold.ttf'

large_card_width = 205
large_card_height = 300
medium_card_width = 115
medium_card_height = round(large_card_height/large_card_width * medium_card_width)
small_card_width = 75
small_card_height = round(large_card_height/large_card_width * small_card_width)

""" large_card_width = 225
large_card_height = 350
medium_card_width = 115
medium_card_height = 180
small_card_width = 75
small_card_height = 118 """
rootFolder = config.localimgfolder

def generate_flip_indicator(orientation, playerNum, reason):
    if playerNum == 1:
        OuterColor = (46, 204, 113)
        InnerColor = (30, 30, 30)
        #InnerColor = (46, 204, 113)
        #OuterColor = (30, 30, 30)
    elif playerNum == 2:
        OuterColor = (214, 48, 49)
        InnerColor = (30, 30, 30)
        #InnerColor = (214, 48, 49)
        #OuterColor = (30, 30, 30)
    fntName = ImageFont.truetype(flip_indicator_font_path,20)
    black = (0,0,0)
    textColor = (251, 244, 180)
    borderWidth = 3
    if orientation == 1:
        #Horizontal
        height = flip_indicator_short
        width = flip_indicator_long
        img = Image.new('RGB', (width, height), color = OuterColor)
        d = ImageDraw.Draw(img)
        textXOffset, textYOffset = d.textsize(reason, font=fntName)
        d.rectangle((borderWidth, borderWidth, width - borderWidth-1, height - borderWidth-1), fill=InnerColor)
        d.text((math.ceil((width-textXOffset)/2), math.ceil((height-textYOffset)/2)), reason, font=fntName, fill=textColor)
    elif orientation == 2:
        #Vertical
        height = flip_indicator_long
        width = flip_indicator_short
        img = Image.new('RGB', (width, height), color = OuterColor)
        d = ImageDraw.Draw(img)
        d.rectangle((borderWidth, borderWidth, width - borderWidth-1, height - borderWidth-1), fill=InnerColor)
        counter = 0
        _, textYOffset = d.textsize(reason, font=fntName)
        for letter in reason:
            counter = counter + 1
            textXOffset, _ = d.textsize(letter, font=fntName)
            offsetMultiplier = (len(reason) / 2 - counter) * 2
            d.text((math.ceil((width-textXOffset)/2), math.ceil((height-textYOffset*offsetMultiplier)/2)-20), letter, font=fntName, fill=textColor)
    
    
    tempImg = tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)    
    img.save(tempImg, "PNG")
    return tempImg

def add_card_amount(imgFilePath, id, amount):
    BorderColor = (100,100,100)
    BorderSize = amount_border_size
    imgFilePath.close()
    img = Image.open(imgFilePath.name)
    width,height = img.size
    img2 = Image.new('RGB', (width, height + BorderSize), color=BorderColor)    
    d = ImageDraw.Draw(img2)
    img2.paste(img, (0,0))
    fntName = ImageFont.truetype(card_amount_path,18)
    tempImg = tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)
    idText = "#" + str(id)
    amountText = str(amount)
    textWidth, textHeight = d.textsize(amountText,font=fntName)
    DrawShadow(d,(width-textWidth)/2, height + BorderSize - textHeight-5, amountText, fntName, (0,0,0))
    d.text(((width-textWidth)/2, height +BorderSize - textHeight-5), amountText, font=fntName, fill="white")
    textWidth, textHeight = d.textsize(idText,font=fntName)
    DrawShadow(d,width-textWidth-5, 5, idText, fntName, (0,0,0))
    d.text((width-textWidth-5, 5), idText, font=fntName, fill="white")
    
    img2.save(tempImg, "PNG")
    os.remove(imgFilePath.name)
    return tempImg

def add_card_ownership_background(imgFilePath, playerNum):
    if playerNum == 1:
        OuterColor = (46, 204, 113)
        InnerColor = (30, 30, 30)
    elif playerNum == 2:
        OuterColor = (214, 48, 49)
        InnerColor = (30, 30, 30)
    elif playerNum == 0:
        OuterColor = (150, 150, 150)
        InnerColor = (30, 30, 30)
    OuterBorderSize = outer_border
    InnerBorderSize = inner_border
    imgFilePath.close()
    img = Image.open(imgFilePath.name)
    width,height = img.size
    img2 = Image.new('RGB', (width + (OuterBorderSize + InnerBorderSize) * 2, height + (OuterBorderSize + InnerBorderSize) * 2), color=OuterColor)    
    d = ImageDraw.Draw(img2)
    d.rectangle((OuterBorderSize, OuterBorderSize, OuterBorderSize + InnerBorderSize * 2 + width-1, OuterBorderSize + InnerBorderSize * 2 + height-1), fill=InnerColor)
    img2.paste(img, (OuterBorderSize + InnerBorderSize, OuterBorderSize + InnerBorderSize))
    tempImg = tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)    
    img2.save(tempImg, "PNG")
    os.remove(imgFilePath.name)
    return tempImg

def generate_blank_card(size=1, num=-1):
    if size == 1:
        width = small_card_width
        height = small_card_height
        statFontSize = small_stat_font_size
        textOffsetX = 4
        textOffsetY = 8
    elif size == 2:
        width = medium_card_width
        height = medium_card_height
        statFontSize = medium_stat_font_size
        textOffsetX = 7
        textOffsetY = 13
    elif size == 3:
        width = large_card_width
        height = large_card_height
        statFontSize = large_stat_font_size
        textOffsetX = 8
        textOffsetY = 12

    fontPathStats = r'C:\Windows\Fonts\phagspab.ttf'
    fntStats = ImageFont.truetype(fontPathStats,statFontSize)
    #white = (255,255,255)
    statColor = (162, 155, 254)
    textX = width / 2 - textOffsetX
    textY = height / 2 - textOffsetY
    
    borderWidth = 3
    img = Image.new('RGB', (width,height),color = 'white')
    d = ImageDraw.Draw(img)
    #fnt = ImageFont.truetype(r'C:\Windows\Fonts\Arial.ttf', 15)
    #d.text((10,10),text,font=fnt,fill=(255,255,255))
    d.rectangle((borderWidth, borderWidth, width - borderWidth-1, height - borderWidth-1), fill=(0,0,0,155))
    if num > 0:
        #DrawShadow(d,textX, textY, str(num), fntStats, white)
        d.text((textX, textY), str(num), font=fntStats, fill=statColor)
    tempImg = tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)    
    img.save(tempImg, "PNG")
    return tempImg


def generate_card_img(size, card_id, name, top, right, bottom, left, img_path, rarity):
    img = Image.open(os.path.join(rootFolder, img_path))
    if size == 3:
        targetWidth = large_card_width
        targetHeight = large_card_height
        statFontSize = large_stat_font_size
        statCP = (30,30)
        statHeight = 22
        statWidth = 20
        rarityOffset = (37,20)
    elif size == 2:
        targetWidth = medium_card_width
        targetHeight = medium_card_height
        statFontSize = medium_stat_font_size
        statCP = (25,25)
        statHeight = 20
        statWidth = 18
        rarityOffset = (37,20)
    elif size == 1:
        targetWidth = small_card_width
        targetHeight = small_card_height
        statFontSize = small_stat_font_size
        statCP = (20,20)
        statHeight = 17
        statWidth = 15
        rarityOffset = (37,20)
    
    width, height = img.size
    if width < targetWidth or height < targetHeight:
        print("Issue with image (Too Small) - " + img_path)
        return

    if width/targetWidth < height/targetHeight:
        thumbnail_ratio = width / targetWidth
    else:
        thumbnail_ratio = height / targetHeight
    
    thumbnail_width = width / thumbnail_ratio + 1
    thumbnail_height = height / thumbnail_ratio + 1

    img.thumbnail((thumbnail_width,thumbnail_height), Image.ANTIALIAS)
    croppedImg = CropImage(img, targetWidth, targetHeight)
    width, height = croppedImg.size
    d = ImageDraw.Draw(croppedImg)
    fontPathName = r'C:\Windows\Fonts\phagspab.ttf'
    fntStats = ImageFont.truetype(card_stat_font_path,statFontSize)
    fntName = ImageFont.truetype(fontPathName,15)
    fntRarity = ImageFont.truetype(card_rarity_font_path,18)
    fntRarityStar = ImageFont.truetype(card_rarity_star_font_path,20)
    white = (255,255,255)
    black = (0,0,0)
    statColor = (251, 244, 180)

    if top == 10:
        top = "A"
    if right == 10:
        right = "A"
    if bottom == 10:
        bottom = "A"
    if left == 10:
        left = "A"

    #Top Stat
    DrawShadow(d,statCP[0], statCP[1] - statHeight, str(top), fntStats, black)
    d.text((statCP[0], statCP[1] - statHeight), str(top), font=fntStats, fill=statColor)
    #Right Stat
    DrawShadow(d,statCP[0]+statWidth, statCP[1], str(right), fntStats, black)
    d.text((statCP[0]+statWidth, statCP[1]), str(right), font=fntStats, fill=statColor)
    #Bottom Stat
    DrawShadow(d,statCP[0], statCP[1] + statHeight, str(bottom), fntStats, black)
    d.text((statCP[0], statCP[1] + statHeight), str(bottom), font=fntStats, fill=statColor)
    #Left Stat
    DrawShadow(d,statCP[0]-statWidth, statCP[1], str(left), fntStats, black)
    d.text((statCP[0]-statWidth, statCP[1]), str(left), font=fntStats, fill=statColor)

    #Name and ID (only on largest card)
    if size == 3:
        d.rectangle((0, height, width, height-22), fill=(0,0,0,155))
        DrawShadow(d,2, height - 18, name, fntName, black)
        d.text((2, height - 18), name, font=fntName, fill=white)
        idOffset = len("#" + str(card_id)) * 8 + 3
        DrawShadow(d,width - idOffset, 3, "#" + str(card_id), fntName, black)
        d.text((width - idOffset, 3), "#" + str(card_id), font=fntName, fill=white)

    #rarity
    
    starOffsetX = 0
    if rarity < 10:
        starOffsetX = -8

    #d.ellipse((rarityOffset[0]-rarityRadius, height - rarityOffset[1]-rarityRadius, rarityOffset[0]+rarityRadius,height - rarityOffset[1]+rarityRadius), fill=(0,0,0,155))
    DrawShadow(d,width - rarityOffset[0] - starOffsetX, height - rarityOffset[1], str(rarity), fntRarity, black)
    DrawShadow(d,width - rarityOffset[0] + 20, height - rarityOffset[1] - 5,"★", fntRarityStar, black)
    d.text((width - rarityOffset[0] - starOffsetX, height - rarityOffset[1]), str(rarity), font=fntRarity, fill="yellow")
    d.text((width - rarityOffset[0] + 20, height - rarityOffset[1] - 5), "★", font=fntRarityStar, fill="yellow")

    tempImg = tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)    
    croppedImg.save(tempImg, "PNG")
    return tempImg

def generate_hand(cards):
    imgSizesX = small_card_width + (inner_border + outer_border) * 2
    imgSizesY = small_card_height + (inner_border + outer_border) * 2
    spacingX = hand_spacing
    totalX = imgSizesX * 5 + spacingX * 4
    totalY = imgSizesY
    img = Image.new('RGB', (totalX,totalY), color='black')
    counter = 0
    for card in cards:
        if counter == 0:
            x = 0
        else:
            x = counter * (imgSizesX + spacingX)        
        card.close()
        add_img = Image.open(card.name)
        img.paste(add_img, (x, 0))
        counter = counter + 1
    tempImg = tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)    
    img.save(tempImg, "PNG")

    for card in cards:
        os.remove(card.name)
    return tempImg

def generate_hand_vert(cards):
    imgSizesX = small_card_width + (inner_border + outer_border) * 2
    imgSizesY = small_card_height + (inner_border + outer_border) * 2
    spacingY = hand_spacing

    totalX = imgSizesX
    totalY = imgSizesY  * 5 + spacingY * 4 

    img = Image.new('RGB', (totalX,totalY), color='black')
    
    counter = 0
    for card in cards:
        if counter == 0:
            y = 0
        else:
            y =  counter * (imgSizesY + spacingY)        
        card.close()
        add_img = Image.open(card.name)
        img.paste(add_img, (0, y))
        counter = counter + 1
    tempImg = tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)    
    img.save(tempImg, "PNG")

    for card in cards:
        os.remove(card.name)
    return tempImg

def generate_board(cardImgs, flips=None, backgroundImg=None):
    #print ("Printing Flips from images.generate_board")
    #print(flips)
    imgSizesX = medium_card_width + (inner_border + outer_border) * 2
    imgSizesY = medium_card_height + (inner_border + outer_border) * 2
    spacingX = 10
    spacingY = 10
    totalX = imgSizesX * 3 + spacingX * 2
    totalY = imgSizesY * 3 + spacingY * 2
    img = Image.new('RGB', (totalX,totalY), color='black')
    for row in range(3):
        for col in range(3):
            index = row * 3 + col
            card = cardImgs[index]
            x = col * (imgSizesX + spacingX)
            y = row * (imgSizesY + spacingY)    
            card.close()
            add_img = Image.open(card.name)
            img.paste(add_img, (x, y))
    
    if flips:
        for flip in flips:
            slot = flip[0]
            reason = flip[1]
            origin = flip[2]
            player = flip[3]

            if slot < origin:
                placementSlot = slot
            else:
                placementSlot = origin

            if abs(origin - slot) < 2:
                #Need vertical indicator to fit between two cards in same row
                orientation = 2
                column = placementSlot % 3
                if column == 0:
                    column = 3
                row = math.ceil(placementSlot / 3)
                x = math.ceil(column * (imgSizesX + spacingX) - (spacingX / 2) - (flip_indicator_short/2))
                y = math.ceil((row - 1) * (imgSizesY + spacingY) + (imgSizesY - flip_indicator_long) / 2)
            else:
                #Need horizontal indicator to fit between two cards in same column
                orientation = 1
                column = placementSlot % 3
                if column == 0:
                    column = 3
                row = math.ceil(placementSlot / 3)
                x = math.ceil((column - 1) * (imgSizesX + spacingX) + (imgSizesX-flip_indicator_long)/2)
                y = math.ceil(row  * (imgSizesY + spacingY) - spacingY/2 - flip_indicator_short / 2)
            flipImg = generate_flip_indicator(orientation, player, reason)
            flipImg.close()
            add_img = Image.open(flipImg.name)
            img.paste(add_img, (x,y))

    tempImg = tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)    
    img.save(tempImg, "PNG")

    for card in cardImgs:
        os.remove(card.name)
    return tempImg

def generate_game(handImg, handImg2, boardImg, name1, name2, rules, wager, turn, backgroundImg=None):
    handImg.close()
    handImg2.close()
    boardImg.close()
    imgHand = Image.open(handImg.name)
    imgHand2 = Image.open(handImg2.name)
    imgBoard = Image.open(boardImg.name)

    h_width,h_height = imgHand.size
    b_width,b_height = imgBoard.size
    
    if len(name1) > 16:
        name1 = name1[:16] + ".."

    if len(name2) > 16:
        name2 = name2[:16] + ".."

    nameSpace = 25
    nameFontSize = 18
    fntName = ImageFont.truetype(game_font_path,nameFontSize)
    fntTurn = ImageFont.truetype(game_font_path, 25)
    black = (0,0,0)
    nameColor = (251, 244, 180)
    

    gap = 50
    totalWidth = h_width * 2 + b_width + gap * 2
    totalHeight = h_height + nameSpace

    img = Image.new('RGB',(totalWidth, totalHeight), color = 'black')
    d = ImageDraw.Draw(img)
    #Player 1 Name
    DrawShadow(d,2, 0, name1, fntName, black)
    d.text((2, 0), name1, font=fntName, fill=nameColor)
    
    #Player 2 Name
    P2NameXOffset, h = d.textsize(name2, font=fntName)
    DrawShadow(d,totalWidth - P2NameXOffset, 0, name2, fntName, black)
    d.text((totalWidth - P2NameXOffset, 0), name2, font=fntName, fill=nameColor)

    #Turn
    if turn == 1:
        turnString = name1 + " To Play"
    elif turn == 2:
        turnString = name2 + " To Play"
    elif turn == -1:
        turnString = name1 + " Wins"
    elif turn == -2:
        turnString = name2 + " Wins"
    w, h = d.textsize(turnString, font=fntTurn)
    DrawShadow(d, math.ceil((totalWidth-w)/2) , 5, turnString, fntTurn, black)
    d.text((math.ceil((totalWidth-w)/2), 5), turnString, font=fntTurn, fill=nameColor)

    

    #Rules
    ruleString = ""
    for rule in rules:
        ruleString += rule.name + " "
    DrawShadow(d, h_width + gap , totalHeight - 25, ruleString, fntName, black)
    d.text((h_width + gap, totalHeight - 25), ruleString, font=fntName, fill=nameColor)

    #Wager
    wagerString = "Wager: " + wager.upper()
    wagerXOffset, h = d.textsize(wagerString, font=fntName)
    DrawShadow(d, h_width + gap + b_width - wagerXOffset, totalHeight - 25, wagerString, fntName, black)
    d.text((h_width + gap + b_width - wagerXOffset, totalHeight - 25), wagerString, font=fntName, fill=nameColor)

    img.paste(imgHand, (0,nameSpace))
    img.paste(imgBoard, (h_width+gap, math.ceil((h_height-b_height)/2) + nameSpace - 10))
    img.paste(imgHand2, (h_width+gap+b_width+gap,nameSpace))

    tempImg = tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)    
    img.save(tempImg, "PNG")

    handImg.close()
    handImg2.close()
    boardImg.close()
    os.remove(handImg.name)
    os.remove(handImg2.name)
    os.remove(boardImg.name)
    return tempImg

def generate_inventory(cardImgs):
    gridX = 4
    gridY = 3

    imgSizesX = medium_card_width
    imgSizesY = medium_card_height + amount_border_size
    spacingX = 10
    spacingY = 10
    totalX = imgSizesX * gridX + spacingX * (gridX-1)
    totalY = imgSizesY * gridY + spacingY * (gridY-1)
    img = Image.new('RGB', (totalX,totalY), color='black')
    for row in range(gridY):
        for col in range(gridX):
            index = row * gridX + col
            try:
                card = cardImgs[index]
            except:
                break
            x = col * (imgSizesX + spacingX)
            y = row * (imgSizesY + spacingY)    
            card.close()
            add_img = Image.open(card.name)
            img.paste(add_img, (x, y))
        else:
            continue
        break
    tempImg = tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False)    
    img.save(tempImg, "PNG")

    for card in cardImgs:
        os.remove(card.name)
    return tempImg

def DrawShadow(d, x, y, text, fnt, fil):
    shadowOffset = 1
    d.text((x-shadowOffset, y-shadowOffset), text, font=fnt, fill=fil)
    d.text((x+shadowOffset, y-shadowOffset), text, font=fnt, fill=fil)
    d.text((x-shadowOffset, y+shadowOffset), text, font=fnt, fill=fil)
    d.text((x+shadowOffset, y+shadowOffset), text, font=fnt, fill=fil)

def CropImage(img, maxX, maxY):
    #Crops image by equal amounts from all sides to the desired size
    width, height = img.size
    diffX = width - maxX
    diffY = height - maxY

    if diffX > 0:
        left = math.ceil(diffX/2)
        right = left + maxX        
    else:
        left = 0
        right = width
    if diffY > 0:
        top = math.ceil(diffY/2)
        bottom = top + maxY
    else:
        top = 0
        bottom = height
    newImg = img.crop((left, top, right, bottom))
    width, height = newImg.size
    
    return newImg


