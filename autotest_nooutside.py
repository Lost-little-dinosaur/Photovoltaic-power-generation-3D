import sys, os
import const.const
from tools.mutiProcessing import *

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import classes.roof
from classes.arrangement import estimateComponentCount, screenArrangements
from classes.component import assignComponentParameters
import json
from PIL import Image, ImageTk
from functools import partial
import time
import random
import numpy as np
from scipy.spatial import Delaunay
from shapely.geometry import Polygon, Point
from shapely.ops import cascaded_union

import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
from matplotlib import patches

import math
from typing import List, Tuple
import signal

random.seed(0)

def cAS(params):
    chunk, latitude, screenedArrangements = params
    retultArray = []
    for ID in chunk:
        screenedArrangements[ID].calculateArrangementShadow(latitude)
        retultArray.append([ID, screenedArrangements[ID].shadowRelativePosition, screenedArrangements[ID].shadowArray])
    return retultArray



def draw_polygon(poly_vertices, save_path=None):
    fig, ax = plt.subplots()
    polygon = patches.Polygon(poly_vertices, closed=True, edgecolor='black', facecolor='lightgrey')
    ax.add_patch(polygon)
    ax.autoscale()
    ax.set_aspect('equal', 'box')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.grid(True)
    
    if save_path:
        plt.savefig(save_path, format='jpg')
        print(f"图像已保存为 {save_path}")
    else:
        pass
        # plt.show()


"""https://stackoverflow.com/questions/8997099/algorithm-to-generate-random-2d-polygon"""
def clip(value, lower, upper):
    """
    Given an interval, values outside the interval are clipped to the interval
    edges.
    """
    return min(upper, max(value, lower))

def random_angle_steps(steps: int, irregularity: float):
    """Generates the division of a circumference in random angles.

    Args:
        steps (int):
            the number of angles to generate.
        irregularity (float):
            variance of the spacing of the angles between consecutive vertices.
    Returns:
        List[float]: the list of the random angles.
    """
    # generate n angle steps
    angles = []
    lower = (2 * math.pi / steps) - irregularity
    upper = (2 * math.pi / steps) + irregularity
    cumsum = 0
    for i in range(steps):
        angle = random.uniform(lower, upper)
        angles.append(angle)
        cumsum += angle

    # normalize the steps so that point 0 and point n+1 are the same
    cumsum /= (2 * math.pi)
    for i in range(steps):
        angles[i] /= cumsum
    return angles

def generate_polygon(center: Tuple[float, float], avg_radius: float,
                     irregularity: float, spikiness: float,
                     num_vertices: int):
    """
    Start with the center of the polygon at center, then creates the
    polygon by sampling points on a circle around the center.
    Random noise is added by varying the angular spacing between
    sequential points, and by varying the radial distance of each
    point from the centre.

    Args:
        center (Tuple[float, float]):
            a pair representing the center of the circumference used
            to generate the polygon.
        avg_radius (float):
            the average radius (distance of each generated vertex to
            the center of the circumference) used to generate points
            with a normal distribution.
        irregularity (float):
            variance of the spacing of the angles between consecutive
            vertices.
        spikiness (float):
            variance of the distance of each vertex to the center of
            the circumference.
        num_vertices (int):
            the number of vertices of the polygon.
    Returns:
        List[Tuple[float, float]]: list of vertices, in CCW order.
    """
    # Parameter check
    if irregularity < 0 or irregularity > 1:
        raise ValueError("Irregularity must be between 0 and 1.")
    if spikiness < 0 or spikiness > 1:
        raise ValueError("Spikiness must be between 0 and 1.")

    irregularity *= 2 * math.pi / num_vertices
    spikiness *= avg_radius
    angle_steps = random_angle_steps(num_vertices, irregularity)

    # now generate the points
    points = []
    angle = random.uniform(0, 2 * math.pi)
    for i in range(num_vertices):
        radius = clip(random.gauss(avg_radius, spikiness), 0, 2 * avg_radius)
        point = (center[0] + radius * math.cos(angle),
                 center[1] + radius * math.sin(angle))
        points.append(point)
        angle += angle_steps[i]

    min_x = min(points, key=lambda p: p[0])[0]
    # max_x = max(points, key=lambda p: p[0])[0]
    min_y = min(points, key=lambda p: p[1])[1]
    # max_y = max(points, key=lambda p: p[1])[1]
    return [(int(p[0] - min_x), int(p[1] - min_y)) for p in points]
    
def get_random_sample():
    def get_random_rectangle_inside_polygon(poly_vertices, num_rectangles, min_width, max_width, min_height, max_height, existing_shapes=None):
        # 创建多边形对象
        polygon = Polygon(poly_vertices)
        # 获取多边形的边界框
        min_x, min_y, max_x, max_y = polygon.bounds
        rectangles = []
        ans = []
        while len(rectangles) < num_rectangles:
            # 随机生成矩形的位置和大小
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)
            width = random.randint(min_width, max_width)
            height = random.randint(min_height, max_height)
            # 创建矩形对象
            rectangle = Polygon([(x, y), (x + width, y), (x + width, y + height), (x, y + height)])
            # 检查矩形是否在多边形内部且不与其他矩形相交
            if polygon.contains(rectangle):
                if existing_shapes is None:
                    if not any(rectangle.intersects(existing_rect) for existing_rect in rectangles):
                        rectangles.append(rectangle)
                        ans.append([x,y,width,height])
                else:
                    if not any(rectangle.intersects(existing_rect) for existing_rect in rectangles) and not any(rectangle.intersects(existing_shape) for existing_shape in existing_shapes) :
                        rectangles.append(rectangle)
                        ans.append([x,y,width,height])
        return rectangles, ans

    def get_random_circle_inside_polygon(poly_vertices, num_circles, min_radius, max_radius, existing_shapes=None):
        # 创建多边形对象
        polygon = Polygon(poly_vertices)
        # 获取多边形的边界框
        min_x, min_y, max_x, max_y = polygon.bounds
        circles = []
        ans = []
        while len(circles) < num_circles:
            # 随机生成圆心的位置
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)
            # 随机生成圆的半径
            radius = random.randint(min_radius, max_radius)
            # 创建圆对象
            circle = Point(x, y).buffer(radius)
            # 检查圆是否在多边形内部
            if polygon.contains(circle):
                if existing_shapes is None:
                    if not any(circle.intersects(existing_circle) for existing_circle in circles):
                        circles.append(circle)
                        ans.append([(x,y),radius])
                else:
                    if not any(circle.intersects(existing_circle) for existing_circle in circles) and not any(circle.intersects(existing_shape) for existing_shape in existing_shapes) :
                        circles.append(circle)
                        ans.append([(x,y),radius])
        return circles, ans

    jsonData = {}
    # guest
    jsonData["guest"] = {}
    jsonData["guest"]["name"] = "1234"
    jsonData["guest"]["phone"] = ""
    # scene
    jsonData["scene"] = {}
    jsonData["scene"]["location"] = {
      "province": "河北",
      "city": "沧州",
      "region": "新华",
      "longitude": 113.4,
      "latitude": 33.5,
      "heavySnow": False,
      "windPressure": "低压",
      "snowPressure": "低压",
      "windAndSnowPressure": "低压",
      "voltageLevel": 3,
      "distanceToGridConnection": 2000
    }
    jsonData["scene"]["roof"] = {
      "isComplex": False,
      "category": "平屋顶",
      "roofSurfaceCategory":"自定义多边形",
      "layer":2,
      "roofDirection": 0,
      "roofAngle": 0,
      "extensibleDistance": [
        0,
        0,
        0,
        0
      ],
      "maintenanceChannel": False,
      "haveParapetWall": False,
      "haveOverhangingEave": False,
    }
    num_vertices, x_range, y_range = random.choice([3,4,5,6,7,8,9,10]), (3000,20000), (3000,20000)
    
    polygon = generate_polygon(center=(250, 250),
                            avg_radius=5000,
                            irregularity=0.3,
                            spikiness=0.2,
                            num_vertices=num_vertices)

    draw_polygon(polygon,save_path="test_polygon.jpg")
    jsonData["scene"]["roof"]["vertexCount"] = num_vertices
    for i in range(num_vertices):
        jsonData["scene"]["roof"][f"vertex{i}_X"] = polygon[i][0]
        jsonData["scene"]["roof"][f"vertex{i}_Y"] = polygon[i][1]
    jsonData["scene"]["roof"]["height"] = random.randint(500,5000)
    jsonData["scene"]["roof"]["obstacles"] = []

    num_obstacles = random.choices([0,1,2,3],weights=[0.3,0.4,0.2,0.1],k=1)[0]
    num_rectangles = num_obstacles
    num_circles = 0
    # for i in range(num_obstacles):
    #     isRound = random.choice([0,1])
    #     if isRound:
    #         num_circles += 1
    #     else:
    #         num_rectangles += 1
    existing_rectangles, random_rectangles = get_random_rectangle_inside_polygon(polygon, num_rectangles, 
                            min_width=100,max_width=1000,min_height=100,max_height=1000)
  
    for rec in random_rectangles:
        obstacle = {}
        obstacle["type"] = random.choice(["有烟烟囱","无烟烟囱"])
        obstacle["id"] = obstacle["type"]
        obstacle["isRound"] = False
        obstacle["upLeftPosition"] = [rec[0], rec[1]]
        obstacle["length"] = rec[2]
        obstacle["width"] = rec[3]
        obstacle["height"] = random.randint(500,5000)
        obstacle["adjustedHeight"] = 0
        obstacle["removable"] = 1
        jsonData["scene"]["roof"]["obstacles"].append(obstacle)

    # 圆形障碍物暂时计算不了
    # existing_circles, random_circles = get_random_circle_inside_polygon(polygon, num_circles, min_radius=50,max_radius=1000,existing_shapes=existing_rectangles)
    # for cir in random_circles:
    #     obstacle = {}
    #     obstacle["type"] = random.choice(["有烟烟囱","无烟烟囱"])
    #     obstacle["id"] = obstacle["type"]
    #     obstacle["isRound"] = True
    #     obstacle["centerPosition"] = cir[0]
    #     obstacle["diameter"] = cir[1]
    #     obstacle["height"] = random.randint(500,5000)
    #     obstacle["adjustedHeight"] = 0
    #     obstacle["removable"] = 1
    #     jsonData["scene"]["roof"]["obstacles"].append(obstacle)

    jsonData["scene"]["obstacles"] = {}
    # jsonData["arrangeType"] = random.choice(["膨胀螺栓", "膨胀抬高", "基墩"])
    jsonData["arrangeType"] = random.choice(["膨胀螺栓"])
    jsonData["component"] = {
        "specification": "182-78",
        "power": 595,
        "thickness": 350
    }
    jsonData["algorithm"] = {
    "precision": 100,
    "maxArrangeCount": 2
    }
    return jsonData

def run_sample(sample_index):
    allTimeStart = time.time()
    jsonData = get_random_sample()
    # print(f"算法精度：{jsonData['algorithm']['precision']} mm，最大方案数量：{jsonData['algorithm']['maxArrangeCount']}")
    const.const.changeUnit(jsonData['algorithm']['precision'])
    #    const.const.changeMinComponent(jsonData['algorithm']['minComponent'])
    const.const.changeMaxArrangeCount(jsonData['algorithm']['maxArrangeCount'])

    roof = classes.roof.Roof(jsonData["scene"]["roof"], jsonData["scene"]["location"]["latitude"],jsonData["scene"]["location"])
    assignComponentParameters(jsonData["component"])

    start_time = time.time()
    roof.addObstacles(jsonData["scene"]["roof"]["obstacles"])
    end_time = time.time()
    execution_time = end_time - start_time
    # print(f"addObstacles 代码执行时间为：{execution_time} 秒")

    # zzp: 基于屋顶有效面积，估计光伏板数量，参数0.7，参数范围0-1，参数越高预估光伏板数量越多
    minComponentCount, maxComponentCount = estimateComponentCount(roof.realArea,
                                                                    jsonData["component"]["specification"],
                                                                    0.7 / jsonData['algorithm']['maxArrangeCount'])
    const.const.changeMinComponent(minComponentCount if jsonData['algorithm']['maxArrangeCount'] >= 2 else 1)
    const.const.changeMaxComponent(maxComponentCount)
    # print(f"自动估计最小光伏板数量:{minComponentCount}，最大光伏板数量:{maxComponentCount}")

    start_time = time.time()
    #    screenedArrangements = screenArrangements(roof.width, roof.length, jsonData["component"]["specification"],
    #                                              jsonData["arrangeType"],
    #                                              jsonData["scene"]["location"]["windPressure"])
    screenedArrangements = screenArrangements(roof.width, roof.length, jsonData["component"]["specification"],
                                                jsonData["arrangeType"],
                                                "低压")

    end_time = time.time()
    execution_time = end_time - start_time
    # print(f"screenArrangements 代码执行时间为：{execution_time} 秒")

    start_time = time.time()
    # 多进程计算阴影
    if jsonData["algorithm"]["maxArrangeCount"] > 1:
        chunks = chunk_it(list(screenedArrangements.keys()), cpuCount)
        allResultArray = []
        with multiprocessing.Pool(processes=cpuCount) as pool:
            resultArray = pool.map(cAS, [(chunk, roof.latitude, screenedArrangements) for chunk in chunks])
            for r in resultArray:
                for rr in r:
                    allResultArray.append(rr)
        for result in allResultArray:
            screenedArrangements[result[0]].shadowRelativePosition = result[1]
            screenedArrangements[result[0]].shadowArray = result[2]

    # zzp:提前排序
    screenedArrangements = dict(sorted(screenedArrangements.items(), key=lambda x: x[1].value, reverse=True))
    end_time = time.time()
    execution_time = end_time - start_time
    # print(f"calculateArrangementShadow代码执行时间为：{execution_time} 秒")

    start_time = time.time()
    maxValue = 0
    panelValue = -1
    for i in range(1, jsonData['algorithm']['maxArrangeCount'] + 1):
        panelValue = roof.getBestOptions(screenedArrangements, i, maxValue, maxComponentCount)  # 计算铺设光伏板的最佳方案
        # print(f"{i}阵列下得到的最大光伏板:{panelValue}")
        if i == jsonData['algorithm']['maxArrangeCount']:
            break
        if maxValue < panelValue:
            maxValue = panelValue

        # zzp:剪枝过大的方案
        IDArray = list(screenedArrangements.keys())
        original_length = len(IDArray)
        cut_index = len(IDArray)
        for j in range(cut_index):
            if screenedArrangements[IDArray[j]].componentNum <= maxValue:
                cut_index = j
                break
        screenedArrangements = {IDArray[j]: screenedArrangements[IDArray[j]] for j in
                                range(cut_index, original_length)}

        # print(f"计算{i}阵列对方案进行剪枝，剪枝前方案数量：{original_length}，剪枝后方案数量：{len(list(screenedArrangements.keys()))}")

    end_time = time.time()
    execution_time = end_time - start_time
    # print(f"getBestOptions 代码执行时间为：{execution_time} 秒")

    start_time = time.time()
    roof.obstacleArraySelf = roof.calculateObstacleSelf()
    end_time = time.time()
    execution_time = end_time - start_time
    # print(f"calculateObstacleSelf 代码执行时间为：{execution_time} 秒")

    start_time = time.time()
    columnValue = roof.calculate_column(screenedArrangements)
    end_time = time.time()
    execution_time = end_time - start_time
    # print(f"calculate_column 代码执行时间为：{execution_time} 秒")

    # 按是否抬高筛选出更优的排布方案
    # minRaiseLevel = const.const.INF
    for placement in roof.allPlacements:
        raiseText = ""
        for i, arrangement in enumerate(placement[0]):
            if arrangement["raiseLevel"] == 1:
                raiseText += f"第{i + 1}阵列高度为{1000}mm\n"
            else:
                raiseText += f"第{i + 1}阵列高度为{540}mm\n"
        placement[4] += raiseText + "\n\n"

    # return roof.drawPlacement(screenedArrangements)
    start_time = time.time()
    tempArray = [roof.drawPlacement(screenedArrangements),
                    [placement[4] for placement in roof.allPlacements[:const.const.outputPlacementCount]]]
    # tempArray = roof.drawPlacement(screenedArrangements), ["", "", "", "", ""]
    end_time = time.time()
    execution_time = end_time - start_time
    # print("drawPlacement 代码执行时间为：", execution_time, "秒\n")
    # print(f"一共排布了{panelValue}块光伏板，{columnValue}根立柱")
    # print("总代码执行时间为：", time.time() - allTimeStart, "秒\n")
    tempArray.append({
        "精度": f"{jsonData['algorithm']['precision']}mm",
        "最大阵列数量": f"{jsonData['algorithm']['maxArrangeCount']}种",
        "基于面积推算的最大光伏板数量": f"{maxComponentCount}块",
        "最终排布的方案种类数": f"{len(roof.allPlacements)}种",
        "最终排布的光伏板数量": f"{panelValue}块",
        "最终排布的立柱数量": f"{columnValue}根",
        "总耗时": "{:.2f}s".format(time.time() - allTimeStart)
    })

    image_matrix = tempArray[0][0]
    image = Image.fromarray(image_matrix)
    scaled_image = image.resize((420, 320))

    ratio = float(panelValue) / maxComponentCount
    if ratio < 0.2:
        folder = 0
    elif ratio < 0.4:
        folder = 1
    elif ratio < 0.6:
        folder = 2
    elif ratio < 0.8:
        folder = 3
    else:
        folder = 4 
    folder_path = os.path.join("test_imgs",f"ArrangementCount_{jsonData['algorithm']['maxArrangeCount']}", f"{folder}",f"{sample_index}.jpg")
    file_path = os.path.join(folder_path, f"{sample_index}.jpg")
    os.makedirs(folder_path,exist_ok=True)
    scaled_image.save(file_path)
    plt.close('all')
    json_file_path = os.path.join(folder_path,f"{sample_index}.json")
    with open(json_file_path, "w") as json_file:
        json.dump(jsonData, json_file)
    
    # return tempArray

def timeout_handler(signum, frame):
    print("运行超时，自动退出")
    raise TimeoutError("Function execution timed out")

if __name__ == "__main__":
    const.const.changeOutputPlacementCount(1)
    num_samples = 1000000
    count = 0
    
    timeout_seconds = 300 # 一个样例跑300s以上，认为是样本有问题，
    signal.signal(signal.SIGALRM, timeout_handler)
    while count < num_samples:
        signal.alarm(timeout_seconds)
        try:
            run_sample(count)
            count += 1
            if count % 10 == 0:
                print(f"——————————————————————————————")
                print(f"已经完成{count}个")
                print(f"——————————————————————————————")
        except:
            pass