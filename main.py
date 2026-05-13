# 3 задача

# vod = input("Введите данные: ").split()
#
# num = vod[1:]
#
# list1 = []
#
# for x in num:
#     f = 1
#     for j in x:
#         f *= int(j)
#     list1.append(f)
#
# if list1:
#     generators = 0
#
#     for f in list1:
#         scet = list1.count(f) #считаем сколько раз  произведение встречается в списке
#         if scet > generators:
#             generators = scet
#     print(generators)
# else:
#     print(0)


# 2 задача
# %  остатка от деления
# // без остатка


# m, n = map(int, input("Введете числа: ").split())
# # map превращает их в целые числа

# result = 0

# for j in range(n, m - 1, -1):
#     e = j
#     sums = 0
#     res = False

#     while e > 0:
#         check = e % 10

#         if check > 0 and check % 2 == 0:
#             sums += check
#             eve = True

#         e //= 10

#     if check and sums % 3 == 0:
#         result = j
#         break
# print(result)

#4
# data = input().split()
# n, k, m = int(data[0]), int(data[1]), int(data[2])
#
# total = 2 * n
# ones = total - k - m
#
# if ones < 0 or (2 * k + ones) % 2 != 0:
#     print(-1)
# else:
#     base3 = [2] * k + [1] * ones + [0] * m
#     result = []
#     for i in range(0, total, 2):
#         result.append(str(base3[i] * 3 + base3[i + 1]))
#     print(''.join(result))
