def calc(_, item):
    weight = item.weight
    height = item.height
    return weight / ((height / 100) * (height / 100))
