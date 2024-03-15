import multiprocessing
from PIL import Image
import numpy as np
import time
import matplotlib.pyplot as plt

from const import const
from const.const import *
from classes.obstacle import Obstacle
import functools
import collections


def calculate_execution_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} 函数执行时间为：{execution_time} 秒")
        return result

    return wrapper


# 输入都是以毫米为单位的
class Roof:
    def __init__(self, jsonRoof, latitude):
        UNIT = getUnit()
        self.eastExtend, self.westExtend, self.southExtend, self.northExtend = jsonRoof["extensibleDistance"]
        self.type = jsonRoof["roofSurfaceCategory"]
        if not jsonRoof["isComplex"]:
            # self.length = round((jsonRoof["length"] + self.southExtend + self.northExtend) / UNIT)
            # self.width = round((jsonRoof["width"] + self.eastExtend + self.westExtend) / UNIT)
            # self.realLength = jsonRoof["length"] + self.southExtend + self.northExtend
            # self.realWidth = jsonRoof["width"] + self.eastExtend + self.westExtend
            self.length = round((jsonRoof["A"] + self.southExtend + self.northExtend) / UNIT)
            self.width = round((jsonRoof["B"] + self.eastExtend + self.westExtend) / UNIT)
            self.realLength = jsonRoof["A"] + self.southExtend + self.northExtend
            self.realWidth = jsonRoof["B"] + self.eastExtend + self.westExtend
            self.height = jsonRoof["height"]
            self.roofArray = np.full((self.length, self.width), 0)
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.obstacleArraySelf = []
            self.realArea = self.realLength * self.realWidth
        elif jsonRoof["isComplex"] and self.type == "正7形":
            self.edgeA = round(jsonRoof["A"] / UNIT)
            self.edgeB = round(jsonRoof["B"] / UNIT)
            self.edgeC = round(jsonRoof["C"] / UNIT)
            self.edgeD = round(jsonRoof["D"] / UNIT)
            self.edgeE = self.edgeA + self.edgeC
            self.edgeF = self.edgeD - self.edgeB
            self.height = jsonRoof["height"]
            self.length = self.edgeE
            self.width = self.edgeD
            self.roofArray = np.zeros((self.length, self.width))
            self.roofArray[self.edgeC:, 0:self.edgeB] = INF
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.obstacleArraySelf = []
            self.realWidth = jsonRoof["D"]
            self.realLength = jsonRoof["A"] + jsonRoof["C"]
            self.realArea = jsonRoof["C"] * jsonRoof["D"] + jsonRoof["A"] * jsonRoof["F"]
        elif jsonRoof["isComplex"] and self.type == "反7形":
            self.edgeA = round(jsonRoof["A"] / UNIT)
            self.edgeB = round(jsonRoof["B"] / UNIT)
            self.edgeC = round(jsonRoof["C"] / UNIT)
            self.edgeD = round(jsonRoof["D"] / UNIT)
            self.edgeE = self.edgeA - self.edgeC
            self.edgeF = self.edgeB - self.edgeD
            self.height = jsonRoof["height"]
            self.length = self.edgeA
            self.width = self.edgeB
            self.roofArray = np.zeros((self.length, self.width))
            self.roofArray[self.edgeC:, self.edgeF:] = INF
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.obstacleArraySelf = []
            self.realWidth = jsonRoof["B"]
            self.realLength = jsonRoof["A"]
            self.realArea = jsonRoof["A"] * jsonRoof["F"] + jsonRoof["C"] * jsonRoof["D"]
        else:
            pass  # todo: 复杂屋顶的情况暂时不做处理
        self.roofAngle = jsonRoof["roofAngle"]
        self.roofDirection = jsonRoof["roofDirection"]
        self.latitude = latitude
        self.obstacles = []
        self.sceneObstacles = []
        # self.maxRects = []
        # self.allPlacements = collections.deque()
        self.allPlacements = []
        # self.type = 0

    def calculateObstacleSelf(self):
        # zzp: numpy加速
        return_list = np.zeros((self.realWidth + 1000, self.realLength + 1000), dtype=np.int32)
        # return_list = [[0] * ((self.realLength + 1000)) for _ in range((self.realWidth + 1000))]
        for obstacle in self.obstacles:
            if obstacle.type == '有烟烟囱':
                x_min = max(0, obstacle.realupLeftPosition[0] - 100)
                x_max = min(self.realWidth, obstacle.realupLeftPosition[0] + obstacle.realwidth + 100)
                y_min = max(0, obstacle.realupLeftPosition[1] - 100)
                y_max = min(self.realLength, obstacle.realupLeftPosition[1] + obstacle.reallength + 100)
                return_list[x_min:x_max, y_min:y_max] = 1
                # for x in range(x_min, x_max):
                #     for y in range(y_min, y_max):
                #         return_list[x][y] = 1
            if obstacle.type == "屋面扣除":
                x_min = obstacle.upLeftPosition[0]
                x_max = obstacle.upLeftPosition[0] + obstacle.width
                y_min = obstacle.upLeftPosition[1]
                y_max = obstacle.realupLeftPosition[1] + obstacle.length
                return_list[x_min:x_max, y_min:y_max] = 1
                # for x in range(x_min, x_max):
                #     for y in range(y_min, y_max):
                #         return_list[x][y] = 1
        return return_list

    # def addObstaclesConcern(self, screenedArrangements):
    #     time1 = time.time()
    #     print("开始分析阴影并选出最佳方案，当前时间为", time.strftime('%m-%d %H:%M:%S', time.localtime()))
    #     nowMaxValue = -INF
    #     # placement中的元素意义为：[[放置的arrangement的ID和startXY],当前value,[扣除的光伏板下标(从左到右从上到下,长度和placement[0]一样),立柱排布]
    #     for placement in self.allPlacements:
    #         # if placement[0][0]['ID'] == 396 and placement[0][1]['ID'] == 321:
    #         #     print("debug")
    #         if placement[1] < nowMaxValue:
    #             continue
    #         if len(placement[0]) == 1:
    #             mergeObstacleArray = self.obstacleArray  # 这个self.obstacleArray已经更新了阴影的情况
    #             # zzp：没必要重复计算
    #             tempObstacleSumArray = self.obstacleSumArray
    #         else:  # 如果多于1个阵列，则要将所有阵列的阴影更新到tempObstacleSumArray里
    #             mergeObstacleArray = np.array(self.obstacleArray)
    #             for arrange in placement[0]:
    #                 sRPX, sRPY = screenedArrangements[arrange['ID']].shadowRelativePosition
    #                 sizeY, sizeX = screenedArrangements[arrange['ID']].shadowArray.shape
    #                 sX, sY = arrange['start']
    #                 rsX, rsY = max(0, sX - sRPX), max(0, sY - sRPY)
    #                 eX, eY = min(self.width, sX - sRPX + sizeX), min(self.length, sY - sRPY + sizeY)
    #                 rsX1, rsY1 = max(0, -sX + sRPX), max(0, -sY + sRPY)
    #                 mergeObstacleArray[rsY:eY, rsX:eX] = np.maximum(mergeObstacleArray[rsY:eY, rsX:eX],
    #                                                                 screenedArrangements[arrange['ID']].shadowArray[
    #                                                                 rsY1:rsY1 + eY - rsY,
    #                                                                 rsX1:rsX1 + eX - rsX])
    #             tempObstacleSumArray = np.cumsum(np.cumsum(mergeObstacleArray, axis=0), axis=1)
    #         allDeletedIndices = []
    #         for arrange in placement[0]:
    #             arrangeStartX, arrangeStartY = arrange['start']
    #             screenedArrangements[arrange['ID']].calculateComponentPositionArray(arrangeStartX, arrangeStartY)
    #             tempArray = screenedArrangements[arrange['ID']].componentPositionArray
    #             deletedIndices = []
    #             for i in range(len(tempArray)):  # 判断每个光伏板是否有被遮挡（i是[[startX,startY],[endX,endY]]，是绝对于整个roof的位置）
    #                 # 用前缀和数组简单判断是否有遮挡，再用高度判断是否有遮挡
    #                 totalComponent = tempObstacleSumArray[tempArray[i][1][1], tempArray[i][0][0]]
    #                 if tempArray[i][0][0] > 0:
    #                     totalComponent -= tempObstacleSumArray[tempArray[i][1][1], tempArray[i][0][0] - 1]
    #                 if tempArray[i][0][1] > 0:
    #                     totalComponent -= tempObstacleSumArray[tempArray[i][0][1] - 1, tempArray[i][1][0]]
    #                 if tempArray[i][0][0] > 0 and tempArray[i][0][1] > 0:
    #                     totalComponent += tempObstacleSumArray[tempArray[i][0][1] - 1, tempArray[i][0][0] - 1]
    #                 if totalComponent == 0 or (mergeObstacleArray[tempArray[i][0][1]:tempArray[i][1][1] + 1, tempArray
    #                 [i][0][0]:tempArray[i][1][0] + 1] <= screenedArrangements[arrange['ID']].componentHeightArray
    #                                            [tempArray[i][0][1] - arrangeStartY:tempArray[i][1][
    #                                                                                    1] - arrangeStartY + 1,
    #                                                      tempArray[i][0][0] - arrangeStartX:tempArray[i][1][
    #                                                                                             0] - arrangeStartX + 1]).all():
    #                     continue
    #                 else:  # 有遮挡
    #                     deletedIndices.append(i)
    #             # screenedArrangements[arrange['ID']].componentPositionArray = []  # 清空componentPositionArray
    #             placement[1] -= len(deletedIndices) * screenedArrangements[arrange['ID']].component.power
    #             allDeletedIndices.append(deletedIndices)
    #         placement.append(allDeletedIndices)
    #         # 判断组件是否被障碍物遮挡
    #         k = -1
    #         for arrange in placement[0]:
    #             k = k + 1
    #             for obstacle in self.obstacles:
    #                 if obstacle.type == '有烟烟囱':
    #                     x1 = max(obstacle.upLeftPosition[0] - (500 / UNIT), 0)
    #                     y1 = max(obstacle.upLeftPosition[1] - (500 / UNIT), 0)
    #                     x2 = x1 + obstacle.width + (500 / UNIT)
    #                     y2 = y1 + obstacle.length + (500 / UNIT)
    #                     for i in range(len(screenedArrangements[arrange['ID']].componentPositionArray)):
    #                         component = screenedArrangements[arrange['ID']].componentPositionArray[i]
    #                         x3 = component[0][0]
    #                         y3 = component[0][1]
    #                         x4 = component[1][0]
    #                         y4 = component[1][1]
    #                         if x1 > x4 or x3 > x2 or y1 > y4 or y3 > y2:
    #                             overcheck = False
    #                         else:
    #                             overcheck = True
    #                         if overcheck == True:
    #                             if i not in placement[2][k]:
    #                                 placement[2][k].append(i)
    #         if placement[1] > nowMaxValue:
    #             nowMaxValue = placement[1]
    #             print(f"当前最大value为{nowMaxValue}，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}")
    #     i = 0
    #     self.allPlacements = [placement for placement in self.allPlacements if placement[1] >= nowMaxValue]
    #     # 不要用while 一个一个删，这样内存会不断重组
    #     # while i < len(self.allPlacements):
    #     #     if self.allPlacements[i][1] < nowMaxValue:
    #     #         del self.allPlacements[i]
    #     #     else:
    #     #         i += 1
    #     print(
    #         f"分析阴影并选出最佳方案完成，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}，耗时{time.time() - time1}秒，共有{len(self.allPlacements)}个较优排布方案\n")
    #     return int(nowMaxValue / screenedArrangements[self.allPlacements[0][0][0]['ID']].component.power)

    def getBestOptions(self, screenedArrangements):
        time1 = time.time()
        print("开始计算排布方案，当前时间为", time.strftime('%m-%d %H:%M:%S', time.localtime()))
        # 输入限制条件
        # minComponent = getMinComponent()  # 最小光伏板个数
        maxArrangeCount = getMaxArrangeCount()  # 最大排布数量
        nowMaxValue = -INF  # todo: 待优化，不需要遍历所有arrangement
        # 全局变量就不要传参，节省内存
        # screenedArrangements = {k: v for k, v in screenedArrangements.items() if v.legal} # 在screenArrangements函数中已经过滤了
        screenedArrangements = dict(sorted(screenedArrangements.items(), key=lambda x: x[1].value, reverse=True))
        IDArray = list(screenedArrangements.keys())

        # 计算obstacle的额外扣除范围
        UNIT = const.getUnit()
        obstacleAdditionalArray = []
        for obstacle in self.obstacles:
            if obstacle.type == '有烟烟囱':
                obstacleAdditionalArray.append([obstacle.upLeftPosition[0] + obstacle.width + (500 / UNIT),
                                                obstacle.upLeftPosition[1] + obstacle.length + (500 / UNIT),
                                                max(obstacle.upLeftPosition[0] - (500 / UNIT), 0),
                                                max(obstacle.upLeftPosition[1] - (500 / UNIT), 0)])

        def addObstaclesConcern(placement):
            if len(placement[0]) == 1:
                # if placement[0][0]['ID'] == 398 and placement[0][0]['start'] == (3, 0):
                #     print("debug")
                mergeObstacleArray = self.obstacleArray
                tempObstacleSumArray = self.obstacleSumArray
            else:
                mergeObstacleArray = np.array(self.obstacleArray)
                for arrange in placement[0]:
                    sRPX, sRPY = screenedArrangements[arrange['ID']].shadowRelativePosition
                    sizeY, sizeX = screenedArrangements[arrange['ID']].shadowArray.shape
                    sX, sY = arrange['start']
                    rsX, rsY = max(0, sX - sRPX), max(0, sY - sRPY)
                    eX, eY = min(self.width, sX - sRPX + sizeX), min(self.length, sY - sRPY + sizeY)
                    rsX1, rsY1 = max(0, -sX + sRPX), max(0, -sY + sRPY)
                    mergeObstacleArray[rsY:eY, rsX:eX] = np.maximum(mergeObstacleArray[rsY:eY, rsX:eX],
                                                                    screenedArrangements[arrange['ID']].shadowArray[
                                                                    rsY1:rsY1 + eY - rsY,
                                                                    rsX1:rsX1 + eX - rsX])
                tempObstacleSumArray = np.cumsum(np.cumsum(mergeObstacleArray, axis=0), axis=1)
            allDeletedIndices = []
            for arrange in placement[0]:
                arrangeStartX, arrangeStartY = arrange['start']
                screenedArrangements[arrange['ID']].calculateComponentPositionArray(arrangeStartX, arrangeStartY)
                tempArray = screenedArrangements[arrange['ID']].componentPositionArray
                deletedIndices = []
                for i in range(len(tempArray)):
                    # zzp: 重复索引使用数量少还好，数量多了就很吃时间
                    p00 = tempArray[i][0][0]
                    p01 = tempArray[i][0][1]
                    p10 = tempArray[i][1][0]
                    p11 = tempArray[i][1][1]
                    for additionalObstacle in obstacleAdditionalArray:  # 额外扣除范围
                        if not (additionalObstacle[2] > p10 or p00 > additionalObstacle[0] or
                                additionalObstacle[3] > p11 or p01 > additionalObstacle[1]):
                            deletedIndices.append(i)
                            break
                    else:  # 额外扣除范围没有遮挡
                        totalComponent = tempObstacleSumArray[p11, p00]
                        if p00 > 0:
                            totalComponent -= tempObstacleSumArray[p11, p00 - 1]
                        if p01 > 0:
                            totalComponent -= tempObstacleSumArray[p01 - 1, p10]
                        if p00 > 0 and p01 > 0:
                            totalComponent += tempObstacleSumArray[p01 - 1, p00 - 1]
                        if totalComponent == 0 or (mergeObstacleArray[p01:p11 + 1, p00:p10 + 1] <=
                                                   screenedArrangements[arrange['ID']].componentHeightArray
                                                   [p01 - arrangeStartY:p11 - arrangeStartY + 1,
                                                   p00 - arrangeStartX:p10 - arrangeStartX + 1]).all():
                            continue
                        else:  # 做抬高分析
                            if not hasattr(screenedArrangements[arrange['ID']], "componentHeightArray1"):
                                screenedArrangements[arrange['ID']].componentHeightArray1 = screenedArrangements[
                                    arrange['ID']].calculateComponentHeightArray(raiseLevel=1)
                            if not (mergeObstacleArray[p01:p11 + 1, p00:p10 + 1] <=
                                    screenedArrangements[arrange['ID']].componentHeightArray1[
                                    p01 - arrangeStartY:p11 - arrangeStartY + 1,
                                    p00 - arrangeStartX:p10 - arrangeStartX + 1]).all():
                                if not hasattr(screenedArrangements[arrange['ID']], "componentHeightArray2"):
                                    screenedArrangements[arrange['ID']].componentHeightArray2 = screenedArrangements[
                                        arrange['ID']].calculateComponentHeightArray(raiseLevel=2)
                                if not (mergeObstacleArray[p01:p11 + 1, p00:p10 + 1] <=
                                        screenedArrangements[arrange['ID']].componentHeightArray2
                                        [p01 - arrangeStartY:p11 - arrangeStartY + 1,
                                        p00 - arrangeStartX:p10 - arrangeStartX + 1]).all():
                                    deletedIndices.append(i)

                placement[1] -= len(deletedIndices) * screenedArrangements[arrange['ID']].component.power
                allDeletedIndices.append(deletedIndices)
            placement.append(allDeletedIndices)

            return placement[1]

        def dfs(startX, startY, startI, currentValue, placements, layer, nowMaxValue):
            betterFlag = False
            obstacleArray = []
            tempObstacleSumArray = []
            if len(placements) >= 1:  # 如果此时已经有一个及以上的阵列了，则需要将所有阵列的阴影更新到obstacleArray中
                obstacleArray = np.zeros((self.length, self.width))
                for arrange in placements:
                    sRPX, sRPY = screenedArrangements[arrange['ID']].shadowRelativePosition
                    sizeY, sizeX = screenedArrangements[arrange['ID']].shadowArray.shape
                    sX, sY = arrange['start']
                    rsX, rsY = max(0, sX - sRPX), max(0, sY - sRPY)
                    eX, eY = min(self.width, sX - sRPX + sizeX), min(self.length, sY - sRPY + sizeY)
                    rsX1, rsY1 = max(0, -sX + sRPX), max(0, -sY + sRPY)
                    obstacleArray[rsY:eY, rsX:eX] = np.maximum(obstacleArray[rsY:eY, rsX:eX],
                                                               screenedArrangements[arrange['ID']].shadowArray[
                                                               rsY1:rsY1 + eY - rsY, rsX1:rsX1 + eX - rsX])
                tempObstacleSumArray = np.cumsum(np.cumsum(obstacleArray, axis=0), axis=1)

            for y in range(startY, self.length):
                for x in range(startX, self.width):
                    for i, ID in enumerate(IDArray[startI:]):
                        # zzp：摆了也不如nowMax，那就直接跳过
                        if layer == maxArrangeCount and currentValue + screenedArrangements[ID].value < nowMaxValue:
                            continue
                        if layer > 0 and overlaps(x, y, screenedArrangements[ID], placements):
                            continue
                        if not canPlaceArrangementRoof(x, y, screenedArrangements[ID]):
                            continue
                        if len(placements) >= 1 and not canPlaceArrangementObstacle(
                                x, y, screenedArrangements[ID], obstacleArray, tempObstacleSumArray):
                            continue
                        newPlacement = {'ID': ID, 'start': (x, y)}
                        placements.append(newPlacement)
                        currentValue += screenedArrangements[ID].value
                        if layer < maxArrangeCount:
                            temp, nowMaxValue = dfs(x + screenedArrangements[ID].relativePositionArray[0][1][0], y, i,
                                                    currentValue, placements, layer + 1, nowMaxValue)
                            if temp:  # 上面的dfs找到了更好的方案，则说明当前方案不是最好的 todo:这一点存疑？
                                betterFlag = True
                            else:  # 上面的dfs没有找到更好的方案，说明当前方案是最好的，将当前方案加入到allPlacements中
                                if currentValue >= nowMaxValue:
                                    tempPlacement = [placements.copy(), currentValue]
                                    tempPlacementValue = addObstaclesConcern(tempPlacement)
                                    if tempPlacementValue > nowMaxValue:
                                        nowMaxValue = tempPlacementValue
                                        self.allPlacements = [tempPlacement]
                                    elif tempPlacementValue == nowMaxValue:
                                        self.allPlacements.append(tempPlacement)
                        else:
                            if currentValue >= nowMaxValue:
                                tempPlacement = [placements.copy(), currentValue]
                                tempPlacementValue = addObstaclesConcern(tempPlacement)
                                if tempPlacementValue > nowMaxValue:
                                    nowMaxValue = tempPlacementValue
                                    self.allPlacements = [tempPlacement]
                                    print(
                                        f"更新当前最大value为{nowMaxValue}，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}")
                                elif tempPlacementValue == nowMaxValue:
                                    self.allPlacements.append(tempPlacement)
                        placements.pop()
                        currentValue -= screenedArrangements[ID].value
                startX = 0
            return betterFlag, nowMaxValue

        def canPlaceArrangementRoof(x, y, arrange):
            # zzp: 提前判断，提前退出
            # numpy版本未必有优势，数据量较少，先留着
            # end_positions = arrange.relativePositionArray[:, 1] + [x, y]
            # absoluteEndX = end_positions[:, 0]
            # absoluteEndY = end_positions[:, 1]
            # within_bounds = (self.width > absoluteEndX) & (self.length > absoluteEndY)
            # if np.any(~within_bounds):
            #     return False

            # totalRoof = self.roofSumArray[absoluteEndY, absoluteEndX]
            # flag_x = np.where(arrange.relativePositionArray[:, 0, 0] > 0)[0]
            # flag_y = np.where(arrange.relativePositionArray[:, 0, 1] > 0)[0]
            # flag_xy = np.intersect1d(flag_x, flag_y)

            # precal_x = x + arrange.relativePositionArray[:, 0, 0] - 1
            # precal_y = y + arrange.relativePositionArray[:, 0, 1] - 1

            # if flag_x.shape[0] > 0:
            #     totalRoof[flag_x] -= self.roofSumArray[absoluteEndY,precal_x][flag_x]
            # if flag_y.shape[0] > 0:
            #     totalRoof[flag_y] -= self.roofSumArray[precal_y,absoluteEndX][flag_y]
            # if flag_xy.shape[0] > 0:
            #     totalRoof[flag_xy] -= self.roofSumArray[precal_y,precal_x][flag_xy]
            # return np.all(totalRoof < INF)

            for eachRect in arrange.relativePositionArray:
                p0, p1 = eachRect
                p00, p01 = p0
                p10, p11 = p1
                absoluteStartX, absoluteStartY = x + p00, y + p01
                absoluteEndX, absoluteEndY = x + p10, y + p11
                absoluteStartX_1 = absoluteStartX - 1
                absoluteStartY_1 = absoluteStartY - 1
                if self.width > absoluteEndX and self.length > absoluteEndY:
                    totalRoof = self.roofSumArray[absoluteEndY][absoluteEndX]
                    if absoluteStartX > 0:
                        totalRoof -= self.roofSumArray[absoluteEndY][absoluteStartX_1]
                    if absoluteStartY > 0:
                        totalRoof -= self.roofSumArray[absoluteStartY_1][absoluteEndX]
                    if absoluteStartX > 0 and absoluteStartY > 0:
                        totalRoof += self.roofSumArray[absoluteStartY_1][absoluteStartX_1]
                    if totalRoof >= INF:
                        return False
                else:
                    return False
            return True

        def canPlaceArrangementObstacle(x, y, arrange, obstacleArray, tempObstacleSumArray):
            for eachRect in arrange.relativePositionArray:
                startX, startY = eachRect[0]
                endX, endY = eachRect[1]
                absoluteEndX, absoluteEndY = x + endX, y + endY
                if self.width > absoluteEndX and self.length > absoluteEndY:
                    totalObstacles = tempObstacleSumArray[absoluteEndY][absoluteEndX]
                    if startX > 0:
                        totalObstacles -= tempObstacleSumArray[absoluteEndY][x + startX - 1]
                    if startY > 0:
                        totalObstacles -= tempObstacleSumArray[y + startY - 1][absoluteEndX]
                    if startX > 0 and startY > 0:
                        totalObstacles += tempObstacleSumArray[y + startY - 1][x + startX - 1]
                else:
                    return False
                # 接下去检查是否被光伏板的阴影遮挡
                if totalObstacles > 0 and not (obstacleArray[y:y + endY - startY + 1, x:x + endX - startX + 1] <
                                               arrange.componentHeightArray[startY:endY + 1, startX:endX + 1]).all():
                    return False
            return True

        def overlaps(x, y, arrange, placements):
            for eachRect in arrange.relativePositionArray:
                p0, p1 = eachRect
                p00, p01 = p0
                p10, p11 = p1
                for placement in placements:
                    startX, startY = placement['start']
                    for eachPlacementRect in screenedArrangements[placement['ID']].relativePositionArray:
                        p2 = eachPlacementRect[0]
                        p3 = eachPlacementRect[1]
                        if not (x + p00 > startX + p3[0] or
                                x + p10 < startX + p2[0] or
                                y + p01 > startY + p3[1] or
                                y + p11 < startY + p2[1]):
                            return True
            return False

        flag, nowMaxValue = dfs(0, 0, 0, 0, [], 1, nowMaxValue)
        # tempTest = []
        # for placement in self.allPlacements:
        #     if len(placement[0]) == 2 and placement[0][1]["start"][1] >= 10:
        #         tempTest.append(placement)
        print(
            f"排布方案计算完成，共有{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}，耗时{time.time() - time1}秒\n")
        return int(nowMaxValue / screenedArrangements[list(screenedArrangements.keys())[0]].component.power)

    def addObstacles(self, obstacles):
        for obstacle in obstacles:  # todo: 待优化，可以多进程计算
            self.obstacles.append(Obstacle(obstacle, self.obstacleArray, self.roofArray, self.latitude))
        self.obstacleSumArray = np.cumsum(np.cumsum(self.obstacleArray, axis=0), axis=1)
        # if self.type == "正7形":
        #     obstacle = {"id": "屋面扣除1", "type": "屋面扣除", "isRound": False, "length": self.edgeA,
        #                 "width": self.edgeB, "height": INF, "upLeftPosition": [0, self.edgeC],
        #                 }
        #     self.obstacles.append(Obstacle(obstacle, self.obstacleArray, self.roofArray, self.latitude))

    def calculate_column(self, screenedArrangements):
        nowMinValue = INF
        for placement in self.allPlacements:
            allArrangement = placement[0]
            allTempArray = []
            allTxtArray = []
            arrangeI = 0
            tempSum = 0
            for arrange in allArrangement:
                startX, startY = arrange['start']
                tempArray, tempTxt = screenedArrangements[arrange['ID']].calculateStandColumn(startX, startY,
                                                                                              self.realWidth,
                                                                                              self.obstacleArraySelf,
                                                                                              placement[2][arrangeI])
                tempTxt = f"第{arrangeI + 1}个阵列的立柱排布：\n" + tempTxt + "\n"
                tempSum += len(tempArray)
                allTempArray.append(tempArray)
                allTxtArray.append(tempTxt)
                arrangeI += 1
            placement.extend([allTempArray, allTxtArray])

            if tempSum < nowMinValue:
                nowMinValue = tempSum

        self.allPlacements = [placement for placement in self.allPlacements if
                              sum([len(x) for x in placement[3]]) >= nowMinValue]
        print(
            f"立柱排布计算完成，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}，共有{len(self.allPlacements)}个较优排布方案\n")
        return nowMinValue

    def drawPlacement(self, screenedArrangements, maxDraw=5):  # todo: numpy优化
        # 初始化一个全白色的三通道矩阵，用于支持彩色（RGB）
        allMatrix = []
        UNIT = getUnit()
        if UNIT <= 25:
            roofBoardLength, PhotovoltaicPanelBoardLength, standColumnPadding, obstaclePadding = 3, 3, 4, 3
            magnification = 1  # 放大倍数
        elif 25 < UNIT <= 50:
            roofBoardLength, PhotovoltaicPanelBoardLength, standColumnPadding, obstaclePadding = 2, 2, 2, 2
            magnification = 2
        elif 50 < UNIT <= 100:
            roofBoardLength, PhotovoltaicPanelBoardLength, standColumnPadding, obstaclePadding = 1, 1, 1, 1
            magnification = 3
        elif 100 < UNIT <= 200:
            roofBoardLength, PhotovoltaicPanelBoardLength, standColumnPadding, obstaclePadding = 1, 1, 1, 1
            magnification = 4
        else:
            roofBoardLength, PhotovoltaicPanelBoardLength, standColumnPadding, obstaclePadding = 1, 1, 1, 1
            magnification = 5
        publicMatrix = np.zeros((self.length * magnification, self.width * magnification, 3))
        # 画障碍物（只需要轮廓就行）
        obstaclePointArray = np.empty((0, 2), dtype=np.int32)
        for obstacle in self.obstacles:
            if obstacle.type == '无烟烟囱' or obstacle.type == '有烟烟囱':
                if not obstacle.isRound:
                    startX = round(obstacle.realupLeftPosition[0] / UNIT) * magnification
                    startY = round(obstacle.realupLeftPosition[1] / UNIT) * magnification
                    endX = round((obstacle.realupLeftPosition[0] + obstacle.realwidth) / UNIT) * magnification
                    endY = round((obstacle.realupLeftPosition[1] + obstacle.reallength) / UNIT) * magnification

                    # 处理障碍物的外轮廓
                    for pad in range(obstaclePadding + 1):  # +1是为了包括外轮廓本身和内部的padding
                        # 处理水平边
                        lenY = endY + 1 - startY - pad * 2  # 调整长度以考虑内部padding
                        if lenY > 0:  # 确保不是负数
                            column = np.tile([startX + pad, endX - pad], lenY)
                            tempMatrix = np.column_stack(
                                (column, np.repeat(np.array(list(range(startY + pad, endY + 1 - pad))), 2)))
                            obstaclePointArray = np.concatenate((obstaclePointArray, tempMatrix), axis=0)

                        # 处理垂直边
                        lenX = endX + 1 - startX - pad * 2  # 调整宽度以考虑内部padding
                        if lenX > 0:  # 确保不是负数
                            column = np.tile([startY + pad, endY - pad], lenX)
                            tempMatrix = np.column_stack(
                                (np.repeat(np.array(list(range(startX + pad, endX + 1 - pad))), 2), column))
                            obstaclePointArray = np.concatenate((obstaclePointArray, tempMatrix), axis=0)

        # 先画障碍物
        for point in obstaclePointArray:
            publicMatrix[point[1], point[0]] = ObstacleColor
        if self.type == "矩形":
            # 首先填充上下边界
            publicMatrix[:roofBoardLength, :, :] = RoofMarginColor  # 上边界
            publicMatrix[-roofBoardLength:, :, :] = RoofMarginColor  # 下边界
            # 然后填充左右边界
            publicMatrix[:, :roofBoardLength, :] = RoofMarginColor  # 左边界
            publicMatrix[:, -roofBoardLength:, :] = RoofMarginColor  # 右边界
        elif self.type == "正7形":
            MA, MB, MC = self.edgeA * magnification, self.edgeB * magnification, self.edgeC * magnification
            MD, ME, MF = self.edgeD * magnification, self.edgeE * magnification, self.edgeF * magnification
            publicMatrix[:MC, :roofBoardLength, :] = RoofMarginColor  # C边界
            publicMatrix[MC - roofBoardLength:MC, :MB, :] = RoofMarginColor  # B边界
            publicMatrix[MC - roofBoardLength:, MB:MB + roofBoardLength, :] = RoofMarginColor  # A边界
            publicMatrix[MC + MA - roofBoardLength:, MB + roofBoardLength:, :] = RoofMarginColor  # F边界
            publicMatrix[:ME - roofBoardLength, MD - roofBoardLength:, :] = RoofMarginColor  # E边界
            publicMatrix[:roofBoardLength, roofBoardLength:MD - roofBoardLength, :] = RoofMarginColor  # D边界
        elif self.type == "反7形":
            MA, MB, MC = self.edgeA * magnification, self.edgeB * magnification, self.edgeC * magnification
            MD, ME, MF = self.edgeD * magnification, self.edgeE * magnification, self.edgeF * magnification
            publicMatrix[:roofBoardLength, :MB, :] = RoofMarginColor
            publicMatrix[roofBoardLength:MC, MB - roofBoardLength:MB, :] = RoofMarginColor
            publicMatrix[MC - roofBoardLength:MC, MF - roofBoardLength:MB - roofBoardLength, :] = RoofMarginColor
            publicMatrix[MC:MA, MF - roofBoardLength:MF, :] = RoofMarginColor
            publicMatrix[MA - roofBoardLength:MA, :MF - roofBoardLength, :] = RoofMarginColor
            publicMatrix[roofBoardLength:MA - roofBoardLength, :roofBoardLength, :] = RoofMarginColor
        for placement in self.allPlacements[:maxDraw]:
            matrix = np.array(publicMatrix)
            for j in range(len(placement[0])):  # j表示第几个arrangement
                arrange = placement[0][j]
                start_x, start_y = arrange['start']
                screenedArrangements[arrange['ID']].calculateComponentPositionArray(start_x, start_y)
                for i in range(len(screenedArrangements[arrange['ID']].componentPositionArray)):  # todo: 为什么要扣除？
                    if i in placement[2][j]:  # 如果这个光伏板被删了，就不画了
                        continue
                    top_left, bottom_right = screenedArrangements[arrange['ID']].componentPositionArray[i]
                    top_left[0], top_left[1] = top_left[0] * magnification, top_left[1] * magnification
                    bottom_right[0], bottom_right[1] = bottom_right[0] * magnification, bottom_right[1] * magnification
                    # 绘制边界（保证边界在光伏板内部）
                    matrix[top_left[1]:top_left[1] + PhotovoltaicPanelBoardLength,
                    top_left[0]:bottom_right[0] + 1] = PhotovoltaicPanelBordColor
                    matrix[bottom_right[1] - PhotovoltaicPanelBoardLength + 1:bottom_right[1] + 1,
                    top_left[0]:bottom_right[0] + 1] = PhotovoltaicPanelBordColor
                    matrix[
                    top_left[1] + PhotovoltaicPanelBoardLength:bottom_right[1] - PhotovoltaicPanelBoardLength + 1,
                    top_left[0]:top_left[0] + PhotovoltaicPanelBoardLength] = PhotovoltaicPanelBordColor
                    matrix[
                    top_left[1] + PhotovoltaicPanelBoardLength:bottom_right[1] - PhotovoltaicPanelBoardLength + 1,
                    bottom_right[0] - PhotovoltaicPanelBoardLength + 1:bottom_right[0] + 1] = PhotovoltaicPanelBordColor

                    # 填充光伏板内部
                    # matrix[
                    # top_left[1] + PhotovoltaicPanelBoardLength:bottom_right[1] - PhotovoltaicPanelBoardLength + 1,
                    # top_left[0] + PhotovoltaicPanelBoardLength:bottom_right[0]] = PhotovoltaicPanelColor

                # 接下去画立柱
                for column in placement[3][j]:  # column形式：[centerX,centerY]
                    matrix[round(column[1] * magnification / UNIT) - standColumnPadding:
                           round(column[1] * magnification / UNIT) + standColumnPadding + 1,
                    round(column[0] * magnification / UNIT) - standColumnPadding:
                    round(column[0] * magnification / UNIT) + standColumnPadding + 1] = StandColumnColor

            # 绘制图像
            plt.imshow(matrix.astype("uint8"))
            plt.axis('off')
            plt.tight_layout()
            # plt.show()

            # 获取当前的Figure对象
            fig = plt.gcf()
            fig.patch.set_facecolor('black')  # 设置背景颜色为黑色

            # 获取绘图数据
            fig.canvas.draw()
            # 将绘图数据保存为PIL Image对象
            image = Image.frombytes('RGB', fig.canvas.get_width_height(), fig.canvas.tostring_rgb())
            # 将PIL Image对象转换为长x宽x3的矩阵变量
            image_array = np.array(image)
            # allMatrix.append(matrix)
            allMatrix.append(image_array)
        return allMatrix


def computeMission(params):
    self, ss, arrangeArray, screenedArrangements = params
    eachLayerPlacements = []
    for s in ss:
        tempArray = self.search(arrangeArray[s][0], arrangeArray[s][1], 0, 0, 0, [], self.obstacleArray,
                                screenedArrangements)
        if tempArray is not None:
            eachLayerPlacements.append([tempArray, s])
    return eachLayerPlacements
