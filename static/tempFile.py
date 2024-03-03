import time

import numpy as np


def getLineSegmentNodes(start, end):
    x0, y0, z0 = start
    x1, y1, z1 = end

    dx = x1 - x0
    dy = y1 - y0
    dz = z1 - z0

    points = []

    if dx == 0 and dy == 0:  # 仅在z方向上移动
        points = [[x0, y0, z0], [x1, y1, z1]]
    else:
        max_steps = max(abs(dx), abs(dy))
        for step in range(max_steps + 1):
            t = step / max_steps
            x = round(x0 + t * dx)
            y = round(y0 + t * dy)
            z = z0 + t * dz
            points.append([x, y, z])

    return points


# [[0, 0, 0.0], [0, 1, 0.0], [0, 2, 0.0], [1, 3, 0.0], [1, 4, 0.0]]
t = 100000
time1 = time.time()
for i in range(t):
    getLineSegmentNodes([20, 4, 10], [0, 0, 0])
print(time.time() - time1)

# d1 = {"id": ["123", {1: 2, 3: 4}]}
# placement = []
# placement.append(d1)
# tempArray = copy.copy(placement)
# placement.append(d1)
# print(tempArray)

# 测试深浅拷贝
# t = 500000
# arr1 = np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
#                  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]])
# Arr = []
# time1 = time.time()
# for i in range(t):
#     Arr = arr1.copy()  # 22.12149477005005，可行
#     # Arr[0][0] = 100
# print(time.time() - time1)
# arr1[0][0] = 100
# print(Arr)
#
# arr2 = [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
#         [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
# time1 = time.time()
# for i in range(t):
#     Arr = arr2.copy()  # 5.845637321472168，不可行
#     # Arr[0][0] = 100
# print(time.time() - time1)
# arr2[0][0] = 100
# print(Arr)
#
# arr1 = np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
#                  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]])
# time1 = time.time()
# for i in range(t):
#     Arr = np.array(arr1)  # 23.795085191726685，可行
#     # Arr[0][0] = 100
# print(time.time() - time1)
# arr1[0][0] = 100
# print(Arr)
#
# arr2 = [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
#         [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
# time1 = time.time()
# for i in range(t):
#     Arr = np.array(arr2)  # 191.8370418548584，可行
#     # Arr[0][0] = 100
# print(time.time() - time1)
# arr2[0][0] = 100
# print(Arr)
#
# arr1 = np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
#                  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]])
# time1 = time.time()
# for i in range(t):
#     Arr = copy.deepcopy(arr1)  # 79.38154625892639，可行
#     # Arr[0][0] = 100
# print(time.time() - time1)
# arr1[0][0] = 100
# print(Arr)
#
# arr2 = [[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
#         [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]
# time1 = time.time()
# for i in range(t):
#     Arr = copy.deepcopy(arr2)  # 1240.5，可行
#     # Arr[0][0] = 100
# print(time.time() - time1)
# arr2[0][0] = 100
# print(Arr)

# 测试多线程库
# import multiprocessing
#
# # 定义一个计算平方和的函数
# def compute_square_sum(numbers):
#     return sum(x*x for x in numbers)
#
# # 分割数据为多个子集，以便多进程处理
# def chunk_it(seq, num):
#     avg = len(seq) / float(num)
#     out = []
#     last = 0.0
#
#     while last < len(seq):
#         out.append(seq[int(last):int(last + avg)])
#         last += avg
#
#     return out
#
# if __name__ == '__main__':
#     # 准备数据
#     numbers = range(10000)  # 假设我们要计算0到9999的平方和
#     cpu_count = multiprocessing.cpu_count()  # 获取CPU核心数量
#
#     # 将数据分割为与CPU核心数量相等的块
#     chunks = chunk_it(numbers, cpu_count)
#
#     # 创建一个进程池
#     with multiprocessing.Pool(processes=cpu_count) as pool:
#         # 使用map异步并行处理数据
#         results = pool.map(compute_square_sum, chunks)
#
#         # 计算最终的结果
#         total_sum = sum(results)
#
#     print(f"Total sum of squares: {total_sum}")
