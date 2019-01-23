import random
import images
import os
import math

def card_stat_randomizer(card_rarity):
    #Defines rules for card stats
    total_points = 12 + math.ceil(card_rarity * 1.5) + random.randint(0, math.ceil(card_rarity/2))
    min_stat = 1
    if card_rarity >= 8:
        max_stat = 10
    else:
        max_stat = 9
    const_stat_keys = ['top', 'bottom', 'left', 'right']
    stat_keys = []
    stat_values = []

    for x in range(4):
        if x < 3:
            #Limit the maximum so that each stat will be a minimum of 1
            if total_points < max_stat:
                max_stat = total_points
                if total_points < (5 - x):
                    max_stat = 1
        
            #Limit the minimum so that all the points will be used up
            if total_points / (3 - x) > max_stat:
                min_stat = total_points - (3 - x) * max_stat
            
            stat_values.append(random.randint(min_stat, max_stat))
            print("Number Between {} and {} - - Random Value is : {}  Remaining Points : {}".format(str(min_stat), str(max_stat), str(stat_values[x]),str(total_points)))
        else:
            stat_values.append(total_points)
            print("Using all remaining points of : {}  Remaining Points : 0".format(str(stat_values[x])))
        
        total_points = total_points - stat_values[x]
        randIndex = random.randint(0, len(const_stat_keys)-1)
        rand_position = const_stat_keys.pop(randIndex)
        print("Popping random position: {}".format(rand_position))
        stat_keys.append(rand_position)
    stats = {}
    for x in range(4):
        stats[stat_keys[x]] = stat_values[x]
    return stats

def random_emoji():
    return
        
#x = 4
#print("Generating Card Stats with Rarity = {}: ".format(str(x+1)))
#a = card_stat_randomizer(x+1)
#print(a)
#mycard = images.generate_card_img(0, "Holo", a['top'], a['right'], a['bottom'], a['left'], "F:\\Wheat and Wolf\\img\\0001_holo.jpg",x+1)

#for x in range(10):
    #print("Generating Card Stats with Rarity = {}: ".format(str(x+1)))
    #print(card_stat_randomizer(x+1))
    