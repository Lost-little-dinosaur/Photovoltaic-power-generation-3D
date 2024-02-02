import time
from math import tan, radians, cos, sin, sqrt
import numpy as np
from tools.getData import dataDict
from typing import List
def arePointsCoplanar(points):
    """判断四个点是否共面"""
    assert len(points) == 4, "点的数量必须为4"
    for point in points:
        assert len(point) == 3, "每个点的坐标必须为三维"

    # 构建矩阵，每个点增加一列1
    matrix = np.array([point + [1] for point in points])

    # 计算矩阵的秩
    rank = np.linalg.matrix_rank(matrix)

    # 如果秩小于3，则点共面
    return rank < 3


print(arePointsCoplanar([[10, 20, 0], [30, 40, 0], [50, 60, 0], [70, 80, 0.0000000000001]]))


def calculateShadow(nodeArray, obstacleArray=None):
    if not arePointsCoplanar(nodeArray):
        raise Exception("点不共面或者点的数量不为4")
    if obstacleArray is not None:  # 返回阴影数组
        pass
    else:  # 在obstacleArray上更新每个点的最高阴影
        pass
def is_point_in_triangle(p, p0, p1, p2):
    """
    判断点p是否在由p0, p1, p2构成的三角形内部
    """
    # 计算向量
    def vec(a, b):
        return [b[0] - a[0], b[1] - a[1]]
    # 计算向量叉乘
    def cross(v1, v2):
        return v1[0] * v2[1] - v1[1] * v2[0]
    # 计算点是否在同一侧
    def same_side(v1, v2, p1, p2):
        cross1 = cross(v1, vec(p1, p2))
        cross2 = cross(v1, vec(p2, p2))
        return cross1 * cross2 >= 0

    v0 = vec(p0, p)
    v1 = vec(p1, p)
    v2 = vec(p2, p)
    # 判断点p是否在每条边的同侧
    b1 = cross(v0, v1) < 0.0
    b2 = cross(v1, v2) < 0.0
    b3 = cross(v2, v0) < 0.0
    return ((b1 == b2) and (b2 == b3))
def find_integer_points_in_projected_triangle(node1, node2, node3):
    """
    找到投影到xy平面上的三角形内所有整数坐标点
    """
    # 忽略z坐标，直接投影到xy平面
    p1, p2, p3 = [node1[:2], node2[:2], node3[:2]]

    # 寻找边界
    min_x = min(p1[0], p2[0], p3[0])
    max_x = max(p1[0], p2[0], p3[0])
    min_y = min(p1[1], p2[1], p3[1])
    max_y = max(p1[1], p2[1], p3[1])

    # 存储所有在三角形内的整数坐标点
    points_in_triangle = []

    # 遍历边界框内的所有点
    for x in range(int(min_x), int(max_x) + 1):
        for y in range(int(min_y), int(max_y) + 1):
            if is_point_in_triangle([x, y], p1, p2, p3):
                points_in_triangle.append((x, y))
    # 求三个点的所构成的空间三角形的方程
    node1 = np.array(node1)
    node2 = np.array(node2)
    node3 = np.array(node3)

    v1 = node2 - node1
    v2 = node3 - node1
    normal = np.cross(v1, v2)

    A, B, C = normal
    D = -np.dot(normal, node1)
    points_in_triangle_heigh = []
    for [x, y] in points_in_triangle:
        z = -(A * x + B * y + D) / C
        points_in_triangle_heigh.append((x, y, z))


    return points_in_triangle_heigh

def getOnePointShadow(point: List[int], latitude):  # x,y,z
    returnList = []
    h = point[2]
    # 检查纬度是否在字典中
    if latitude in dataDict:
        for k, v in dataDict[latitude].items():
            # 获取阴影长度和方向
            shadowLength, shadowDirection = v
            shadowLength /= 1000  # 将单位转换为米，只有在这里计算的时候用到的是米，其他都是UNIT
            adjustedLength = shadowLength * h / point[2]
            x = round(point[0] + adjustedLength * cos(radians(shadowDirection)))
            y = round(point[1] + adjustedLength * sin(radians(shadowDirection)))
            z = 0
            returnList.append([x, y, z])  # 这里先不取整
            max_y = 0
            max_x = 0
            min_y = 1000000
            min_x = 1000000
            result_list = []
            for i in range(6):
                returnList[i] = find_integer_points_in_projected_triangle(returnList[i], returnList[i+1], point)
            merged_array = np.concatenate((result_list[0], returnList[1], returnList[2], returnList[3],
                                           returnList[4], returnList[5], returnList[6]))
            for node in merged_array:
                if node[0] < min_x:
                    min_x = node[0]
                if node[0] > max_x:
                    max_x = node[0]
                if node[1] < min_y:
                    min_y = node[1]
                if node[1] > max_y:
                    max_y = node[1]
            final_list = []
            f = -1
            for x in range(min_x, max_x):
                for y in range(min_y, max_y):
                    for node in merged_array:
                        if node[0] == x and node[1] == y:
                            f = node[2]
                            break
                    if f != -1:
                        final_list.append([x, y, f])
                        f = -1
    else:
        if latitude not in dataDict:
            print("纬度 ", latitude, " 不在字典中")
    return returnList
if __name__ == '__main__':
# 示例节点
   node1 = [2, 0, 0]  # A
   node2 = [0, 2, 0]  # B
   node3 = [0, 0, 1]  # C，投影到xy平面后z坐标被忽略

# 执行函数
print(find_integer_points_in_projected_triangle(node1, node2, node3))




