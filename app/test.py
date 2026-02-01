from itertools import product, permutations

def fn(x, y, z, w):
    return not (not x or y) or (z == w) or z

for a, b, c, d, e, f, g in product([0, 1], repeat = 7):
    table = [
        (0, 0, a, b),
        (c, d, 1, e),
        (f, 1, 0, g)
    ]
    
    if len(table) != len(set(table)): continue
    
    for i in permutations("xyzw"):
        if all([not fn(**dict(zip(i, r))) for r in table]):
            print(*i)