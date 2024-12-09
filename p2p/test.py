current_time = 2133415104.6205525
DELTA = 30
dic1 = {'44445': 1733415104.6205525,'44444': 1733478979.7526214, '44446': 1733415097.0769417, '22222': 1733415104.6188161, '33333': 1733415104.6180027, '11111': 1733415097.065989}
dic2 ={'44444': 1733415104.6195538, '44446': 1733478975.0002356, '44445': 1733478975.0002356, '22222': 1733478979.7520673, '33333': 1733478975.0215294, '11111': 1733478975.0215294}

# dic = {key: value for key, value in dic.items() if (current_time - value) <= DELTA}


def merge_set(dic1, dic2):
    merged = dic1 
    for key in dic2:
        if key in merged:
            merged[key] = max(dic1[key], dic2[key])
        else:
            merged[key] = dic2[key]
    return merged

print(merge_set(dic1, dic2))