from const.const import INF
import time
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from math import tan, radians, cos, sin, sqrt
import numpy as np
from tools.getData import dataDict
from typing import List


def draw3dModel(model3DArray):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # 生成每个柱子的x，y坐标
    numRows, numCols = len(model3DArray), len(model3DArray[0])
    x = np.arange(numCols)
    y = np.arange(numRows)
    xpos, ypos = np.meshgrid(x, y)

    xpos = xpos.flatten()
    ypos = ypos.flatten()
    zpos = np.zeros(numCols * numRows)

    # 生成每个柱子的dx，dy，dz值
    dx = dy = np.ones_like(zpos)
    dz = np.array(model3DArray).flatten()

    ax.bar3d(xpos, ypos, zpos, dx, dy, dz, shade=True)

    ax.set_xlabel('X Axis')
    ax.set_ylabel('Y Axis')
    ax.set_zlabel('Z Axis')
    ax.set_title('3D Grid Model Visualization')

    plt.show()


def arePointsCoplanar(nodeArray):
    # 确保nodeArray的长度为4，且每个元素长度为3
    if len(nodeArray) != 4 or any(len(node) != 3 for node in nodeArray):
        return False

    # 检查任意三点是否共线
    def isCollinear(p1, p2, p3):
        # 计算向量p1p2和向量p1p3
        v1 = np.array(p2) - np.array(p1)
        v2 = np.array(p3) - np.array(p1)
        # 计算两向量的叉积
        cross_product = np.cross(v1, v2)
        # 如果叉积的模为0，则三点共线
        return np.linalg.norm(cross_product) == 0

    # 对nodeArray中的每个三点组合进行检查
    for i in range(len(nodeArray)):
        node1, node2, node3 = nodeArray[i], nodeArray[(i + 1) % 4], nodeArray[(i + 2) % 4]
        if isCollinear(node1, node2, node3):
            raise Exception("物体有三点共线！")

    # 如果行列式的值为零，则点共面，否则不共面
    return abs(np.linalg.det(np.array([node + [1] for node in nodeArray]))) < 1e-6  # 使用小的阈值来处理浮点数的精度问题


def interpolateZ(x, y, x0, y0, z0, dx, dy, dz):
    """线性插值计算z值"""
    if dx != 0:
        t = (x - x0) / dx
    elif dy != 0:
        t = (y - y0) / dy
    else:
        return z0  # 避免除以0
    return z0 + t * dz


def getLineSegmentNodes(start, end):
    x0, y0, z0 = start
    x1, y1, z1 = end
    dx = x1 - x0
    dy = y1 - y0
    dz = z1 - z0

    nodes = []

    if abs(dx) > abs(dy):  # x变化更大，以x为基准
        if x0 > x1:
            x0, x1, y0, y1, z0, z1 = x1, x0, y1, y0, z1, z0  # 确保从小到大遍历
        for x in range(x0, x1 + 1):
            y = round(y0 + dy * (x - x0) / dx)
            z = interpolateZ(x, y, x0, y0, z0, dx, dy, dz)
            nodes.append([x, y, z])
    else:  # y变化更大，以y为基准
        if y0 > y1:
            x0, x1, y0, y1, z0, z1 = x1, x0, y1, y0, z1, z0  # 确保从小到大遍历
        for y in range(y0, y1 + 1):
            x = round(x0 + dx * (y - y0) / dy)
            z = interpolateZ(x, y, x0, y0, z0, dx, dy, dz)
            nodes.append([x, y, z])

    return nodes


def isPointInTriangle(p, p0, p1, p2):
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


def findIntegerPointsInProjectedTriangle(node1, node2, node3):
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
            if isPointInTriangle([x, y], p1, p2, p3):
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
    if point[2] == 0:  # 如果点在地面上，阴影长度为0
        return INF, INF, []
    returnList = []
    h = point[2]
    m = 0.1
    # 检查纬度是否在字典中
    if latitude in dataDict:
        for k, v in dataDict[latitude].items():
            # 获取阴影长度和方向
            shadowLength, shadowDirection = v
            shadowLength /= 1000  # 将单位转换为米，只有在这里计算的时候用到的是米，其他都是UNIT
            adjustedLength = shadowLength * h / point[2]
            x = round((point[0] + adjustedLength * cos(radians(shadowDirection))) / m)
            y = round((point[1] + adjustedLength * sin(radians(shadowDirection))) / m)
            z = 0
            returnList.append([x, y, z])  # 这里先不取整
    else:
        if latitude not in dataDict:
            print("纬度 ", latitude, " 不在字典中")
            return INF, INF, []
    max_y, max_x, min_y, min_x = -INF, -INF, INF, INF

    tempAllArray = []
    for i in range(6):
        tempArray = findIntegerPointsInProjectedTriangle(returnList[i], returnList[i + 1], point)
        if len(tempArray) > 0:
            tempAllArray.append(tempArray)
    merged_array = np.concatenate(tempAllArray)

    for node in merged_array:
        min_x = min(min_x, node[0])
        max_x = max(max_x, node[0])
        min_y = min(min_y, node[1])
        max_y = max(max_y, node[1])
    final_list = []
    f = -1
    min_x, min_y, max_x, max_y = round(min_x), round(min_y), round(max_x), round(max_y)
    for x in range(round(min_x), round(max_x)):
        for y in range(round(min_y), round(max_y)):
            for node in merged_array:
                if node[0] == x and node[1] == y:
                    f = node[2]
                    break
            if f != -1:
                final_list.append([x, y, f])
                f = -1
    return min_x, min_y, np.array(final_list)


def getTriangleFlatNodes(node1, node2, node3):
    returnList = findIntegerPointsInProjectedTriangle(node1, node2, node3)
    min_x, min_y, max_x, max_y = INF, INF, -INF, -INF
    for node in returnList:
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
            for node in returnList:
                if node[0] == x and node[1] == y:
                    f = node[2]
                    break
            if f != -1:
                final_list.append([x, y, f])
                f = -1
    return np.array(final_list)


def calculateShadow(nodeArray, isRound, latitude, obstacleArray=None):
    minX, minY, maxX, maxY = INF, INF, -INF, -INF
    if not isRound:
        if not arePointsCoplanar(nodeArray):
            raise Exception("点不共面或者点的数量不为4")
        if obstacleArray is None:  # 返回阴影数组
            tempArray = [[min(nodeArray[0][0], nodeArray[1][0], nodeArray[2][0]),
                          min(nodeArray[0][1], nodeArray[1][1], nodeArray[2][1]),
                          getTriangleFlatNodes(nodeArray[0], nodeArray[1], nodeArray[2])],
                         [min(nodeArray[1][0], nodeArray[2][0], nodeArray[3][0]),
                          min(nodeArray[1][1], nodeArray[2][1], nodeArray[3][1]),
                          getTriangleFlatNodes(nodeArray[1], nodeArray[2], nodeArray[3])]]  # 把物体本体也加入阴影数组
            for i in range(len(nodeArray) - 1):
                lineSegmentNodes = getLineSegmentNodes(nodeArray[i], nodeArray[i + 1])
                for node in lineSegmentNodes:
                    startX, startY, tempShadowArray = getOnePointShadow(node, latitude)
                    if len(tempShadowArray) != 0:
                        tempArray.append([startX, startY, tempShadowArray])
                        minX, minY, maxX, maxY = min(minX, startX), min(minY, startY), max(maxX, startX + len(
                            tempShadowArray)), max(maxY, startY + len(tempShadowArray[0]))
            returnArray = np.array([[0 for _ in range(round(maxY - minY) + 1)] for _ in range(round(maxX - minX) + 1)])
            detaX = 0 if minX >= 0 else -minX
            detaY = 0 if minY >= 0 else -minY
            for startX, startY, tempShadowArray in tempArray:  # todo:可能有边界问题
                # 把tempShadowArray去掉detaX和detaY的部分加到returnArray上
                returnArray[startX + detaX:startX + tempShadowArray.shape[0] + detaX,
                startY + detaY:startY + tempShadowArray.shape[1] + detaY] = np.maximum(
                    returnArray[startX + detaX:startX + tempShadowArray.shape[0] + detaX,
                    startY + detaY:startY + tempShadowArray.shape[1] + detaY], tempShadowArray)
            # 返回returnArray的坐标和returnArray
            return minX, minY, returnArray

        else:  # 在obstacleArray上更新每个点的最高阴影
            # todo: 加一个判断，对于超出了obstacleArray的范围不更新
            # todo: 更改代码结构，适应后续可能变化的getTriangleFlatNodes
            tempArray = getTriangleFlatNodes(nodeArray[0], nodeArray[1], nodeArray[2])
            for tempNode in tempArray:  # 把物体本身的阴影加入阴影数组（第一个三角形）
                obstacleArray[round(tempNode[0])][round(tempNode[1])] = max(
                    obstacleArray[round(tempNode[0])][round(tempNode[1])], tempNode[2])
            tempArray = getTriangleFlatNodes(nodeArray[1], nodeArray[2], nodeArray[3])
            for tempNode in tempArray:  # 把物体本身的阴影加入阴影数组（第二个三角形）
                obstacleArray[round(tempNode[0])][round(tempNode[1])] = max(
                    obstacleArray[round(tempNode[0])][round(tempNode[1])], tempNode[2])

            for i in range(len(nodeArray) - 1):  # 把物体的边缘的阴影加入阴影数组
                lineSegmentNodes = getLineSegmentNodes(nodeArray[i], nodeArray[i + 1])  # 获取线段上的点
                for node in lineSegmentNodes:  # todo:可能有边界问题
                    startX, startY, tempShadowArray = getOnePointShadow(node, latitude)
                    if len(tempShadowArray) != 0:
                        # sX = max(0, startX)
                        sX, sY, = max(0, startX), max(0, startY)
                        eX = min(obstacleArray.shape[0], startX + tempShadowArray.shape[0])
                        eY = min(obstacleArray.shape[1], startY + tempShadowArray.shape[1])
                        obstacleArray[sX:eX, sY:eY] = np.maximum(obstacleArray[sX:eX, sY:eY],
                                                                 tempShadowArray[sX - startX:eX - startX,
                                                                 sY - startY:eY - startY])  # todo: 检查这里的边界问题
    else:
        pass  # 圆形的阴影暂时不做计算


if __name__ == '__main__':
    # 测试四点共面函数
    # print(arePointsCoplanar([[10, 0, 10], [30, 0, 10], [50, 0, 10], [70, 80, 1000]]))
    # 测试获取线段上的点函数
    # print(getLineSegmentNodes([0, 0, 0], [3, 3, 0]))
    # 测试calculateShadow函数
    # calculateShadow([[0, 0, 0], [3, 0, 0], [0, 3, 3], [3, 3, 3]], False, 0.5,
    #                 np.array([[0 for _ in range(100)] for _ in range(100)]))
    # 测试draw3dModel函数
    model3DArray = [[1, 1, 1], [2, 2, 2]]
    draw3dModel(model3DArray)
