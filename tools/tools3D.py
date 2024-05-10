from const.const import INF, getUnit
import time
import matplotlib.pyplot as plt
from math import tan, radians, cos, sin, sqrt
import numpy as np
from tools.getData import dataDict
from typing import List
from copy import deepcopy
import multiprocessing

def multiprocess_func(func, args_list, timeout=600):
    processes = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=processes)
    results = []
    for args in args_list:
        result = pool.apply_async(func, args)
        try:
            result = result.get(timeout=timeout)  # 设置超时时间
            results.append(result)
        except multiprocessing.TimeoutError:
            # 如果超时，抛出异常
            raise TimeoutError("Multiprocessing function execution timed out")
    pool.close()
    pool.join()
    return results

def multiprocess_func(func, iter):
    processes = multiprocessing.cpu_count()
    # pool = multiprocessing.Pool(processes=processes)
    with multiprocessing.Pool(processes=processes) as pool:
        results = pool.map(func=func,iterable=iter)
    # pool.close()
    # pool.join()
    return results


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
    UNIT = getUnit()
    # 确保nodeArray的长度为4，且每个元素长度为3
    if len(nodeArray) != 4 or any(len(node) != 3 for node in nodeArray):
        return False

    tempNodeArray = deepcopy(nodeArray)  # 要把z坐标转换成UNIT单位
    tempNodeArray[0][2] /= UNIT
    tempNodeArray[1][2] /= UNIT
    tempNodeArray[2][2] /= UNIT
    tempNodeArray[3][2] /= UNIT

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
    for i in range(len(tempNodeArray)):
        node1, node2, node3 = tempNodeArray[i], tempNodeArray[(i + 1) % 4], tempNodeArray[(i + 2) % 4]
        if isCollinear(node1, node2, node3):
            raise Exception("物体有三点共线！")

    # 如果行列式的值为零，则点共面，否则不共面
    return abs(np.linalg.det(np.array([node + [1] for node in tempNodeArray]))) < 1e-6  # 使用小的阈值来处理浮点数的精度问题


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
        if max_steps < 50:
            for step in range(max_steps + 1):
                t = step / max_steps
                x = round(x0 + t * dx)
                y = round(y0 + t * dy)
                z = z0 + t * dz
                points.append([x, y, z])
        else:
            ### swap to numpy function if too many steps
            points = np.linspace(start=start,stop=end,num=(max_steps+1),endpoint=True,dtype=np.int32)
    return points


def isPointInTriangle(p, p0, p1, p2):
    """
    判断点p是否在由p0, p1, p2构成的三角形内部（包括边上）
    """

    def vec(a, b):
        return [b[0] - a[0], b[1] - a[1]]

    def cross(v1, v2):
        return v1[0] * v2[1] - v1[1] * v2[0]

    def same_side(v1, v2, p1, p2):
        cross1 = cross(v1, vec(p1, p2))
        cross2 = cross(v1, vec(p2, p2))
        return cross1 * cross2 >= 0

    v0 = vec(p0, p)
    v1 = vec(p1, p)
    v2 = vec(p2, p)
    b1 = cross(v0, v1) <= 0.0
    b2 = cross(v1, v2) <= 0.0
    b3 = cross(v2, v0) <= 0.0

    # 判断点是否在边上
    on_edge = (cross(v0, v1) == 0.0) or (cross(v1, v2) == 0.0) or (cross(v2, v0) == 0.0)

    return ((b1 == b2) and (b2 == b3)) or on_edge


def findIntegerPointsInProjectedTriangle(node1, node2, node3):
    """
    找到投影到xy平面上的三角形内所有整数坐标点
    """
    # 忽略z坐标，直接投影到xy平面
    p1, p2, p3 = [node1[:2], node2[:2], node3[:2]]

    # 求三个点的所构成的空间三角形的方程
    node1 = np.array(node1)
    node2 = np.array(node2)
    node3 = np.array(node3)

    v1 = node2 - node1
    v2 = node3 - node1
    normal = np.cross(v1, v2)

    A, B, C = normal
    ### 提前计算，提前结束
    if C == 0:
        return []

    D = -np.dot(normal, node1)
    points_in_triangle_heigh = []

    # 寻找边界
    min_x = min(p1[0], p2[0], p3[0])
    max_x = max(p1[0], p2[0], p3[0])
    min_y = min(p1[1], p2[1], p3[1])
    max_y = max(p1[1], p2[1], p3[1])

    # 存储所有在三角形内的整数坐标点
    points_in_triangle = []

    # 遍历边界框内的所有点
    # for x in range(int(min_x), int(max_x) + 1):
    #     for y in range(int(min_y), int(max_y) + 1):
    #         if isPointInTriangle([x, y], p1, p2, p3):
    #             points_in_triangle.append((x, y))

    ### 切换到扫描线算法，稍微快点，总复杂度还是O(N^2)
    triangle = [p1, p2, p3]
    for y in range(int(min_y), int(max_y)+1):
        for i in range(3):
            x0, y0 = triangle[i]
            x1, y1 = triangle[(i+1)%3]
            x2, y2 = triangle[(i+2)%3]
            if y0 > y1:
                x0, x1, y0, y1 = x1, x0, y1, y0
            if y0 <= y < y1:
                if y1 != y0:
                    x_inline = x0 + (x1 - x0) * (y - y0) // (y1 - y0)
                    points_in_triangle.append([x_inline,y])
                    if isPointInTriangle((x_inline+1,y),p1,p2,p3): # 往右扫描
                        for x in range(int(x_inline), int(max_x)):
                            if isPointInTriangle((x,y),p1,p2,p3):
                                points_in_triangle.append([x,y])
                            else:
                                break
                    else: # 往左扫描
                        for x in range(int(min_x), int(x_inline)):
                            if isPointInTriangle((x,y),p1,p2,p3):
                                points_in_triangle.append([x,y])
                            else:
                                break




    for [x, y] in points_in_triangle:
        z = -(A * x + B * y + D) / C
        points_in_triangle_heigh.append((x, y, z))

    return points_in_triangle_heigh


def getOnePointShadow(point: List[int], latitude):  # x,y,z
    UNIT = getUnit()
    if point[2] == 0:  # 如果点在地面上，阴影长度为0
        return INF, INF, []
    returnList = []
    h = point[2]
    # 检查纬度是否在字典中
    if latitude in dataDict:
        for k, v in dataDict[latitude].items():
            # 获取阴影长度和方向
            shadowLength, shadowDirection = v
            shadowLength = h * shadowLength / 1000
            shadowLength /= UNIT
            x = round(point[0] + shadowLength * cos(radians(shadowDirection)))
            y = round(point[1] + shadowLength * sin(radians(shadowDirection)))
            z = 0
            returnList.append([x, y, z])  # 这里先不取整
    else:
        print("纬度 ", latitude, " 不在字典中")
        return INF, INF, []
    max_y, max_x, min_y, min_x = -INF, -INF, INF, INF

    tempAllArray = []
    for i in range(6):
        tempArray = findIntegerPointsInProjectedTriangle(returnList[i], returnList[i + 1], point)
        if len(tempArray) > 0:
            tempAllArray.append(tempArray)
    merged_array = np.concatenate(tempAllArray)

    min_x = int(min(min_x, np.min(merged_array[:,0])))
    max_x = int(max(max_x, np.max(merged_array[:,0])))
    min_y = int(min(min_y, np.min(merged_array[:,1])))
    max_y = int(max(max_y, np.max(merged_array[:,1])))

    ### 换矩阵操作
    # for node in merged_array:
    #     min_x = int(min(min_x, node[0]))
    #     max_x = int(max(max_x, node[0]))
    #     min_y = int(min(min_y, node[1]))
    #     max_y = int(max(max_y, node[1]))
    node_dict = {(node[0], node[1]): node[2] for node in merged_array}
    
    # 转化成字典查询，用字典替换一个for循环
    final_list = [[0] * (max_x - min_x) for _ in range(max_y - min_y)]
    for y in range(0, max_y - min_y):
        for x in range(0, max_x - min_x):
            f = node_dict.get((x + min_x, y + min_y), -1)
            final_list[y][x] = f if f != -1 else 0
    # f = -1
    # final_list = [[0] * (max_x - min_x + 1) for _ in range(max_y - min_y + 1)]
    # for y in range(0, max_y - min_y + 1):
    #     for x in range(0, max_x - min_x + 1):
    #         for node in merged_array:
    #             if node[0] == x + min_x and node[1] == y + min_y:
    #                 f = node[2]
    #                 break
    #         if f != -1:
    #             final_list[y][x] = f
    #             f = -1
    #         else:
    #             final_list[y][x] = 0
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
    final_list = [[0] * (max_x - min_x + 1) for _ in range(max_y - min_y + 1)]
    # f = -1
    for node in returnList:
        x = node[0] - min_x
        y = node[1] - min_y
        if(0 <= x <= (max_x - min_x)) and (0 <= y <= (max_y - min_y)):
            final_list[y][x] = node[2]

    # for y in range(0, max_y - min_y + 1):
    #    for x in range(0, max_x - min_x + 1):
    #        for node in returnList:
    #            if node[0] == x + min_x and node[1] == y + min_y:
    #                f = node[2]
    #                break
    #        if f != -1:
    #            final_list[y][x] = f
    #            f = -1
    #        else:
    #            final_list[y][x] = 0
    return min_x, min_y, np.array(final_list)


def calculateShadow(nodeArray, isRound, latitude, addSelfFlag, obstacleArray=None):
    minX, minY, maxX, maxY = INF, INF, -INF, -INF
    if not isRound:
        if not arePointsCoplanar(nodeArray):
            raise Exception("点不共面或者点的数量不为4")
        if obstacleArray is None:  # 返回阴影数组
            if addSelfFlag:
                tempArray = [getTriangleFlatNodes(nodeArray[0], nodeArray[1], nodeArray[2]),
                             getTriangleFlatNodes(nodeArray[2], nodeArray[3], nodeArray[0])]  # 把物体本体也加入阴影数组
                minX, maxX = tempArray[0][0], tempArray[0][0] + tempArray[0][2].shape[1]
                minY, maxY = tempArray[0][1], tempArray[0][1] + tempArray[0][2].shape[0]
            else:
                tempArray = []
                for node in nodeArray:
                    minX, minY = min(minX, node[0]), min(minY, node[1])
                    maxX, maxY = max(maxX, node[0]), max(maxY, node[1])

            for i in range(len(nodeArray)):
                lineSegmentNodes = getLineSegmentNodes(nodeArray[i], nodeArray[(i + 1) % len(nodeArray)])
                if abs(nodeArray[i][2] - nodeArray[(i + 1) % len(nodeArray)][2]) < 1e-6:
                    publicStartX, publicStartY, publicShadowArray = getOnePointShadow(nodeArray[i], latitude)
                    if len(publicShadowArray) == 0:
                        continue
                    tempArray.append([publicStartX, publicStartY, publicShadowArray])
                    for j in range(1, len(lineSegmentNodes)):
                        tempArray.append([publicStartX + lineSegmentNodes[j][0] - lineSegmentNodes[0][0],
                                          publicStartY + lineSegmentNodes[j][1] - lineSegmentNodes[0][1],
                                          publicShadowArray])
                else:
                    for node in lineSegmentNodes:  # node形式是[x, y, z]
                        startX, startY, tempShadowArray = getOnePointShadow(node, latitude)
                        if len(tempShadowArray) == 0:
                            continue
                        tempArray.append([startX, startY, tempShadowArray])
                        minX, minY, maxX, maxY = min(minX, startX), min(minY, startY), max(
                            maxX, startX + tempShadowArray.shape[1]), max(maxY, startY + tempShadowArray.shape[0])

            returnArray = np.zeros((round(maxY - minY) + 1, round(maxX - minX) + 1))
            for startX, startY, tempShadowArray in tempArray:  # todo:可能有边界问题
                returnArray[startY - minY:startY + tempShadowArray.shape[0] - minY,
                startX - minX:startX + tempShadowArray.shape[1] - minX] = np.maximum(
                    returnArray[startY - minY:startY + tempShadowArray.shape[0] - minY,
                    startX - minX:startX + tempShadowArray.shape[1] - minX], tempShadowArray)
            # 返回returnArray的坐标和returnArray
            return minX, minY, returnArray

        else:  # 在obstacleArray上更新每个点的最高阴影
            if addSelfFlag:
                selfStartX, selfStartY, selfHeightArray = getTriangleFlatNodes(nodeArray[0], nodeArray[1], nodeArray[2])
                sX, sY = max(0, selfStartX), max(0, selfStartY)
                eX = min(obstacleArray.shape[1], selfStartX + selfHeightArray.shape[1])
                eY = min(obstacleArray.shape[0], selfStartY + selfHeightArray.shape[0])
                rsX1, rsY1 = max(0, -selfStartX), max(0, -selfStartY)
                obstacleArray[sY:eY, sX:eX] = np.maximum(obstacleArray[sY:eY, sX:eX],
                                                         selfHeightArray[rsY1:rsY1 + eY - sY, rsX1:rsX1 + eX - sX])
                selfStartX, selfStartY, selfHeightArray = getTriangleFlatNodes(nodeArray[2], nodeArray[3], nodeArray[0])
                sX, sY = max(0, selfStartX), max(0, selfStartY)
                eX = min(obstacleArray.shape[1], selfStartX + selfHeightArray.shape[1])
                eY = min(obstacleArray.shape[0], selfStartY + selfHeightArray.shape[0])
                rsX1, rsY1 = max(0, -selfStartX), max(0, -selfStartY)
                obstacleArray[sY:eY, sX:eX] = np.maximum(obstacleArray[sY:eY, sX:eX],
                                                         selfHeightArray[rsY1:rsY1 + eY - sY, rsX1:rsX1 + eX - sX])
            for i in range(len(nodeArray)):  # 把物体的边缘的阴影加入阴影数组
                lineSegmentNodes = getLineSegmentNodes(nodeArray[i], nodeArray[(i + 1) % len(nodeArray)])
                if abs(nodeArray[i][2] - nodeArray[(i + 1) % len(nodeArray)][2]) < 1e-6:
                    publicStartX, publicStartY, publicShadowArray = getOnePointShadow(nodeArray[i], latitude)
                    if len(publicShadowArray) == 0:
                        continue
                    sX, sY, = max(0, publicStartX), max(0, publicStartY)
                    if sX < obstacleArray.shape[1] and sY < obstacleArray.shape[0]:
                        eX = min(obstacleArray.shape[1], publicStartX + publicShadowArray.shape[1])
                        eY = min(obstacleArray.shape[0], publicStartY + publicShadowArray.shape[0])
                        rsX1, rsY1 = max(0, -publicStartX), max(0, -publicStartY)
                        obstacleArray[sY:eY, sX:eX] = np.maximum(obstacleArray[sY:eY, sX:eX],
                                                                 publicShadowArray[rsY1:rsY1 + eY - sY,
                                                                 rsX1:rsX1 + eX - sX])
                    for j in range(1, len(lineSegmentNodes)):
                        nowStartX = publicStartX + lineSegmentNodes[j][0] - lineSegmentNodes[0][0]
                        nowStartY = publicStartY + lineSegmentNodes[j][1] - lineSegmentNodes[0][1]
                        sX, sY, = max(0, nowStartX), max(0, nowStartY)
                        if sX < obstacleArray.shape[1] and sY < obstacleArray.shape[0]:
                            eX = min(obstacleArray.shape[1], nowStartX + publicShadowArray.shape[1])
                            eY = min(obstacleArray.shape[0], nowStartY + publicShadowArray.shape[0])
                            rsX1, rsY1 = max(0, -nowStartX), max(0, -nowStartY)
                            obstacleArray[sY:eY, sX:eX] = np.maximum(obstacleArray[sY:eY, sX:eX],
                                                                     publicShadowArray[rsY1:rsY1 + eY - sY,
                                                                     rsX1:rsX1 + eX - sX])
                else:
                    for node in lineSegmentNodes:  # todo:可能有边界问题
                        startX, startY, tempShadowArray = getOnePointShadow(node, latitude)
                        if len(tempShadowArray) == 0:
                            continue
                        sX, sY, = max(0, startX), max(0, startY)
                        if sX < obstacleArray.shape[1] and sY < obstacleArray.shape[0]:
                            eX = min(obstacleArray.shape[1], startX + tempShadowArray.shape[1])
                            eY = min(obstacleArray.shape[0], startY + tempShadowArray.shape[0])
                            rsX1, rsY1 = max(0, -startX), max(0, -startY)
                            obstacleArray[sY:eY, sX:eX] = np.maximum(obstacleArray[sY:eY, sX:eX],
                                                                     tempShadowArray[rsY1:rsY1 + eY - sY,
                                                                     rsX1:rsX1 + eX - sX])
    else:
        pass  # 圆形的阴影暂时不做计算


def point_in_polygon(point, polygon):
    x, y = point
    num_vertices = len(polygon)
    inside = False
    j = num_vertices - 1
    for i in range(num_vertices):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi < y and yj >= y or yj < y and yi >= y) and (xi <= x or xj <= x):
            if xi + (y - yi) / (yj - yi) * (xj - xi) < x:
                inside = not inside
        j = i
    return inside

def check_point_in_polygon(args):
    point, polygon = args
    return point_in_polygon(point, polygon)

def create_bounding_box_with_holes(polygon):
    min_x = min(polygon, key=lambda p: p[0])[0]
    max_x = max(polygon, key=lambda p: p[0])[0]
    min_y = min(polygon, key=lambda p: p[1])[1]
    max_y = max(polygon, key=lambda p: p[1])[1]
    
    bounding_box = np.zeros((max_y - min_y + 1, max_x - min_x + 1))
    points_to_check = [(x, y) for y in range(min_y, max_y + 1) for x in range(min_x, max_x + 1)]
    
    try:
        results = multiprocess_func(check_point_in_polygon, [(point, polygon) for point in points_to_check])
    except TimeoutError as e:
        # 处理超时异常
        print("Error:", e)
        raise
    
    for idx, inside in enumerate(results):
        y, x = divmod(idx, max_x - min_x + 1)
        if not inside:
            bounding_box[y, x] = INF
    
    return bounding_box

# def create_bounding_box_with_holes(polygon):
#     # 获取多边形的边界框
#     min_x = min(polygon, key=lambda p: p[0])[0]
#     max_x = max(polygon, key=lambda p: p[0])[0]
#     min_y = min(polygon, key=lambda p: p[1])[1]
#     max_y = max(polygon, key=lambda p: p[1])[1]
    
#     bounding_box = np.zeros((max_y - min_y + 1, max_x - min_x + 1))
#     points_to_check = [(x, y) for y in range(min_y, max_y + 1) for x in range(min_x, max_x + 1)]
    
#     # 使用多进程池进行并行计算
#     results = multiprocess_func(check_point_in_polygon, [(point, polygon) for point in points_to_check])

#     for idx, inside in enumerate(results):
#         y, x = divmod(idx, max_x - min_x + 1)
#         if not inside:
#             bounding_box[y, x] = INF
    
#     return bounding_box


def get_polygon_area(vertices):
    # 初始化面积为0
    area = 0.0
    num_vertices = len(vertices)

    # 遍历多边形的每个顶点
    for i in range(num_vertices):
        # 当前顶点的坐标
        current_vertex = vertices[i]
        x1, y1 = current_vertex
        # 下一个顶点的坐标，如果当前顶点是最后一个，则下一个顶点是第一个顶点
        next_vertex = vertices[(i + 1) % num_vertices]
        x2, y2 = next_vertex
        # 使用叉积公式计算当前边和x轴之间的有向面积
        area += (x1 * y2 - x2 * y1)

    # 最终面积取绝对值并除以2
    area = abs(area) / 2.0
    return area

def mark_polygon_edges(vertices, bounding_box, color):
    num_vertices = len(vertices)
    # 遍历多边形的每个顶点，连接成边
    for i in range(num_vertices):
        start_point = vertices[i]
        end_point = vertices[(i + 1) % num_vertices]
        x1, y1 = start_point
        x2, y2 = end_point
        
        # 使用 Bresenham 算法计算边上的所有点
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while x1 != x2 or y1 != y2:
            if x1 < bounding_box.shape[1] and y1 < bounding_box.shape[0]:
                bounding_box[y1, x1, :] = color
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
    
    return bounding_box

if __name__ == '__main__':
    # 测试四点共面函数
    # print(arePointsCoplanar([[10, 0, 10], [30, 0, 10], [50, 0, 10], [70, 80, 1000]]))
    # 测试获取线段上的点函数
    # print(getLineSegmentNodes([0, 0, 0], [3, 3, 0]))
    # 测试calculateShadow函数
    # a, b, c = calculateShadow([[0, 0, 300], [30, 0, 300], [30, 30, 300], [0, 30, 300]], False, 0.5)
    tempObstacleArray = np.array([[0 for _ in range(60)] for _ in range(60)])
    # calculateShadow([[10, 10, 300], [40, 10, 300], [40, 40, 300], [10, 40, 300]], False, 0.5, tempObstacleArray)
    draw3dModel(tempObstacleArray)
    # 测试getOnePointShadow函数
    # a = getOnePointShadow([300, 300, 300.0], 0.5)
    # draw3dModel(a[2])
    # print(getOnePointShadow([2, 1, 1.0], 0.5))
    # 测试draw3dModel函数
    # model3DArray = [[1, 1, 1], [2, 2, 2]]
    # draw3dModel(model3DArray)
