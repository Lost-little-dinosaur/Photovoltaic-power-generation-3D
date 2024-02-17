arr = [[1, 2], [3, 4], [5, 6], [7, 8]]
for a in arr:
    if a[0] == 3 or a[0] == 5:
        del a
print(arr)
