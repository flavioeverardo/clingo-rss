""" Distance """
def distance(l1, l2):
    #l3 = list(set(l1) & set(l2)) # Intersect
    #l4 = list(set(l1)-set(l3))   # Difference
    #l5 = list(set(l2)-set(l3))   # Difference
    #return len(l4)+len(l5)
    diff = len(set(l1).symmetric_difference(l2))
    return diff

def calculate_distances(models, k):
    total = 0
    local_dist = 0
    local_min  = 1000000000

    distancesText = ""
    
    for i in range(len(models)):
        for j in range(i+1,len(models)):
            partial = distance(models[i], models[j])
            if partial >= k:
                distancesText += "distance(%s,%s,%s).\n"%(i+1, j+1, partial)
                distancesText += "distance(%s,%s,%s).\n"%(j+1, i+1, partial)
                total += partial
            if local_dist < partial:
                local_dist = partial
            if partial < local_min:
                local_min = partial
    distancesText += "\n"
    distancesText += "%% Total distance: %s \n"%total
    distancesText += "%% Max distance between two answer sets: %s \n"%local_dist
    distancesText += "max_distance(%s). \n"%local_dist
    distancesText += "%% Min distance between two answer sets: %s \n"%local_min
    distancesText += "min_distance(%s). \n"%local_min

    return distancesText

def calculate_incremental_distances(models, slice_value):

    part1 = models[ : slice_value]
    part2 = models[slice_value : ]
    distancesText = ""

    for i in range(len(part1)):
        for j in range(len(part2)):
            partial = distance(part1[i], part2[j])
            distancesText += "  distance(%s,%s,%s).\n"%(i+1, slice_value + j+1, partial)
            distancesText += "  distance(%s,%s,%s).\n"%(slice_value + j+1, i+1, partial)

    distancesText += "\n"
    for i in range(len(part2)):
        for j in range(i+1, len(part2)):
            partial = distance(part2[i], part2[j])
            distancesText += "  distance(%s,%s,%s).\n"%(slice_value + i+1, slice_value + j+1, partial)
            distancesText += "  distance(%s,%s,%s).\n"%(slice_value + j+1, slice_value + i+1, partial)
    
    distancesText += "\n"

    return distancesText

def distances(models):
    total = 0;
    
    for i in range(len(models)):
        for j in range(i+1,len(models)):
            partial = distance(models[i], models[j])
            total += partial
    return total


## Weights for propagators
def calculate_weights(distances, models):
    partial = 0
    for i in range(len(models)):
        for j in range(i+1,len(models)):
            answer1 = models[i]
            answer2 = models[j]
            partial += distances[(answer1, answer2)]
    return partial
