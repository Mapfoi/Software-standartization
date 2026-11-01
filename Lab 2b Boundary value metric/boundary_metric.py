"""
Расчёт метрики граничных значений для shortgo2 (2).go
for { } — принимающая вершина (outdegree = 1).
"""

# Скорректированные сложности вершин выбора:
# C = |вершины подграфа| + 1 (нижняя граница)
CHOICE = {
    4: 15,   # x > 10
    6: 13,   # x > 0
    8: 11,   # i < 12 (цикл)
    9: 8,    # i == 1
    11: 6,   # i == 2
    13: 4,   # i == 5
    15: 2,   # i == 11
    20: 3,   # n < 2 (цикл)
    25: 3,   # range (цикл)
    27: 7,   # x == 5
    29: 5,   # x == 3
    31: 2,   # x > icount
}

NU = 34
END = 34
ACCEPTING = [i for i in range(1, NU + 1) if i not in CHOICE and i != END]

complexities = {v: 1 for v in ACCEPTING}
complexities.update(CHOICE)
complexities[END] = 0

Sa = sum(complexities.values())
So = 1 - (NU - 1) / Sa

print(f"nu = {NU}")
print(f"choice vertices: {sorted(CHOICE)} ({len(CHOICE)})")
print(f"accepting (C=1): {ACCEPTING}")
print(f"C(22) for{{}} = {complexities[22]}  # accepting")
print(f"Sa = {Sa}")
print(f"So = {So:.2f}")
