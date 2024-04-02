from PIL import Image
import numpy as np
import time
import matplotlib.pyplot as plt

from const import const
from const.const import *
from classes.obstacle import Obstacle
import functools
import collections


# import numexpr as ne

# 输入都是以毫米为单位的
class Roof:
    def __init__(self, jsonRoof, latitude, jsonLocation):
        UNIT = getUnit()
        self.eastExtend, self.westExtend, self.southExtend, self.northExtend = jsonRoof["extensibleDistance"]
        self.type = jsonRoof["roofSurfaceCategory"]
        if self.type == "矩形":
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
            self.obstaclerange = []
            self.realArea = self.realLength * self.realWidth
        elif self.type == "正7形":
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
            # 对roofArray做左右镜像翻转
            self.roofArray = np.fliplr(self.roofArray)
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.obstacleArraySelf = []
            self.obstaclerange = []
            self.realWidth = jsonRoof["D"]
            self.realLength = jsonRoof["A"] + jsonRoof["C"]
            self.realArea = jsonRoof["C"] * jsonRoof["D"] + jsonRoof["A"] * jsonRoof["F"]
        elif self.type == "反7形":
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
            self.obstaclerange = []
            self.realWidth = jsonRoof["B"]
            self.realLength = jsonRoof["A"]
            self.realArea = jsonRoof["A"] * jsonRoof["F"] + jsonRoof["C"] * jsonRoof["D"]
        elif self.type == "正L形":
            self.edgeA = round(jsonRoof["A"] / UNIT)
            self.edgeB = round(jsonRoof["B"] / UNIT)
            self.edgeC = round(jsonRoof["C"] / UNIT)
            self.edgeD = round(jsonRoof["D"] / UNIT)
            self.edgeE = self.edgeA - self.edgeC
            self.edgeF = self.edgeB + self.edgeC
            self.height = jsonRoof["height"]
            self.length = self.edgeA
            self.width = self.edgeF
            self.roofArray = np.zeros((self.length, self.width))
            self.roofArray[0:self.edgeC, self.edgeB:] = INF
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.obstacleArraySelf = []
            self.obstaclerange = []
            self.realWidth = jsonRoof["F"]
            self.realLength = jsonRoof["A"]
            self.realArea = jsonRoof["A"] * jsonRoof["B"] + jsonRoof["D"] * jsonRoof["E"]
        elif self.type == "反L形":
            self.edgeA = round(jsonRoof["A"] / UNIT)
            self.edgeB = round(jsonRoof["B"] / UNIT)
            self.edgeC = round(jsonRoof["C"] / UNIT)
            self.edgeD = round(jsonRoof["D"] / UNIT)
            self.edgeE = self.edgeA + self.edgeC
            self.edgeF = self.edgeB + self.edgeD
            self.height = jsonRoof["height"]
            self.length = self.edgeE
            self.width = self.edgeF
            self.roofArray = np.zeros((self.length, self.width))
            self.roofArray[0:self.edgeC, 0:self.edgeB] = INF
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.obstacleArraySelf = []
            self.obstaclerange = []
            self.realWidth = jsonRoof["F"]
            self.realLength = jsonRoof["A"] + jsonRoof["C"]
            self.realArea = jsonRoof["A"] * jsonRoof["B"] + jsonRoof["D"] * jsonRoof["E"]
        elif self.type == "上凸形":
            self.edgeA = round(jsonRoof["A"] / UNIT)
            self.edgeB = round(jsonRoof["B"] / UNIT)
            self.edgeC = round(jsonRoof["C"] / UNIT)
            self.edgeD = round(jsonRoof["D"] / UNIT)
            self.edgeE = round(jsonRoof["E"] / UNIT)
            self.edgeF = round(jsonRoof["F"] / UNIT)
            self.edgeH = self.edgeB + self.edgeD + self.edgeF
            self.edgeG = self.edgeA + self.edgeC - self.edgeE
            self.height = jsonRoof["height"]
            self.length = self.edgeA + self.edgeC
            self.width = self.edgeH
            self.roofArray = np.zeros((self.length, self.width))
            self.roofArray[0:self.edgeC, 0:self.edgeB] = INF
            self.roofArray[0:self.edgeE, self.edgeB + self.edgeD:] = INF
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.obstacleArraySelf = []
            self.obstaclerange = []
            self.realWidth = jsonRoof["B"] + jsonRoof["D"] + jsonRoof["F"]
            self.realLength = jsonRoof["A"] + jsonRoof["C"]
            self.realArea = jsonRoof["A"] * jsonRoof["B"] + jsonRoof["G"] * jsonRoof["F"] + \
                            (jsonRoof["A"] + jsonRoof["C"]) * jsonRoof["D"]
        elif self.type == "下凸形":
            self.edgeA = round(jsonRoof["A"] / UNIT)
            self.edgeB = round(jsonRoof["B"] / UNIT)
            self.edgeC = round(jsonRoof["C"] / UNIT)
            self.edgeD = round(jsonRoof["D"] / UNIT)
            self.edgeE = round(jsonRoof["E"] / UNIT)
            self.edgeF = round(jsonRoof["F"] / UNIT)
            self.edgeH = self.edgeD - self.edgeB - self.edgeF
            self.edgeG = self.edgeA + self.edgeC - self.edgeE
            self.height = jsonRoof["height"]
            self.length = self.edgeA + self.edgeC
            self.width = self.edgeD
            self.roofArray = np.zeros((self.length, self.width))
            self.roofArray[self.edgeC:, 0:self.edgeB] = INF
            self.roofArray[self.edgeE:, (self.edgeB + self.edgeH):] = INF
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.obstacleArraySelf = []
            self.obstaclerange = []
            self.realWidth = jsonRoof["D"]
            self.realLength = jsonRoof["A"] + jsonRoof["C"]
            self.realArea = jsonRoof["C"] * jsonRoof["B"] + jsonRoof["E"] * jsonRoof["F"] + \
                            (jsonRoof["A"] + jsonRoof["C"]) * jsonRoof["H"]
        elif self.type == "左凸形":
            self.edgeA = round(jsonRoof["A"] / UNIT)
            self.edgeB = round(jsonRoof["B"] / UNIT)
            self.edgeC = round(jsonRoof["C"] / UNIT)
            self.edgeD = round(jsonRoof["D"] / UNIT)
            self.edgeE = round(jsonRoof["E"] / UNIT)
            self.edgeF = round(jsonRoof["F"] / UNIT)
            self.edgeH = self.edgeF + self.edgeD - self.edgeB
            self.edgeG = self.edgeA + self.edgeC + self.edgeE
            self.height = jsonRoof["height"]
            self.length = self.edgeG
            self.width = self.edgeD + self.edgeF
            self.roofArray = np.zeros((self.length, self.width))
            self.roofArray[0:self.edgeE, 0:self.edgeD] = INF
            self.roofArray[(self.edgeE + self.edgeC):, 0:self.edgeB] = INF
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.obstacleArraySelf = []
            self.obstaclerange = []
            self.realWidth = jsonRoof["D"] + jsonRoof["F"]
            self.realLength = jsonRoof["E"] + jsonRoof["C"] + jsonRoof["A"]
            self.realArea = jsonRoof["E"] * jsonRoof["F"] + jsonRoof["A"] * jsonRoof["H"] + \
                            (jsonRoof["D"] + jsonRoof["F"]) * jsonRoof["C"]
        elif self.type == "右凸形":
            self.edgeA = round(jsonRoof["A"] / UNIT)
            self.edgeB = round(jsonRoof["B"] / UNIT)
            self.edgeC = round(jsonRoof["C"] / UNIT)
            self.edgeD = round(jsonRoof["D"] / UNIT)
            self.edgeE = round(jsonRoof["E"] / UNIT)
            self.edgeF = round(jsonRoof["F"] / UNIT)
            self.edgeH = self.edgeB + self.edgeD - self.edgeF
            self.edgeG = self.edgeA - self.edgeC - self.edgeE
            self.height = jsonRoof["height"]
            self.length = self.edgeA
            self.width = self.edgeB + self.edgeD
            self.roofArray = np.zeros((self.length, self.width))
            self.roofArray[0:self.edgeC, self.edgeB:] = INF
            self.roofArray[self.edgeC + self.edgeE:, self.edgeH:] = INF
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.obstacleArraySelf = []
            self.obstaclerange = []
            self.realWidth = jsonRoof["B"] + jsonRoof["D"]
            self.realLength = jsonRoof["A"]
            self.realArea = jsonRoof["B"] * jsonRoof["C"] + jsonRoof["G"] * jsonRoof["H"] + \
                            (jsonRoof["B"] + jsonRoof["D"]) * jsonRoof["E"]
        elif self.type == "上凹形":
            self.edgeA = round(jsonRoof["A"] / UNIT)
            self.edgeB = round(jsonRoof["B"] / UNIT)
            self.edgeC = round(jsonRoof["C"] / UNIT)
            self.edgeD = round(jsonRoof["D"] / UNIT)
            self.edgeE = round(jsonRoof["E"] / UNIT)
            self.edgeF = round(jsonRoof["F"] / UNIT)
            self.edgeH = self.edgeB + self.edgeD + self.edgeF
            self.edgeG = self.edgeA - self.edgeC + self.edgeE
            self.height = jsonRoof["height"]
            self.length = max(self.edgeA, self.edgeG)
            self.width = self.edgeH
            self.roofArray = np.zeros((self.length, self.width))
            if self.edgeA >= self.edgeG:
                self.roofArray[0:self.edgeC, self.edgeB:self.edgeB + self.edgeD] = INF
                self.roofArray[0:self.edgeA - self.edgeG, self.edgeB + self.edgeD:self.edgeH] = INF
            else:
                self.roofArray[0:self.edgeE, self.edgeB:self.edgeB + self.edgeD] = INF
                self.roofArray[0:self.edgeG - self.edgeA, 0:self.edgeB] = INF
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.obstacleArraySelf = []
            self.obstaclerange = []
            self.realWidth = jsonRoof["B"] + jsonRoof["D"] + jsonRoof["F"]
            self.realLength = jsonRoof["A"]
            self.realArea = jsonRoof["B"] * jsonRoof["A"] + jsonRoof["G"] * jsonRoof["F"] + \
                            (jsonRoof["A"] - jsonRoof["C"]) * jsonRoof["D"]
        elif self.type == "下凹形":
            self.edgeA = round(jsonRoof["A"] / UNIT)
            self.edgeB = round(jsonRoof["B"] / UNIT)
            self.edgeC = round(jsonRoof["C"] / UNIT)
            self.edgeD = round(jsonRoof["D"] / UNIT)
            self.edgeE = round(jsonRoof["E"] / UNIT)
            self.edgeF = round(jsonRoof["F"] / UNIT)
            self.edgeH = self.edgeB - self.edgeD - self.edgeF
            self.edgeG = self.edgeA - self.edgeC + self.edgeE
            self.height = jsonRoof["height"]
            self.length = max(self.edgeC, self.edgeA)
            self.width = self.edgeB
            self.roofArray = np.zeros((self.length, self.width))
            if self.edgeC >= self.edgeA:
                self.roofArray[self.edgeA:, 0:self.edgeH] = INF
                self.roofArray[self.edgeC - self.edgeE:, self.edgeH:self.edgeH + self.edgeF] = INF
            else:
                self.roofArray[self.edgeC:, self.edgeH + self.edgeF:] = INF
                self.roofArray[self.edgeC - self.edgeE:, self.edgeH:self.edgeH + self.edgeF] = INF
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.obstacleArraySelf = []
            self.obstaclerange = []
            self.realWidth = jsonRoof["B"]
            self.realLength = jsonRoof["C"]
            self.realArea = jsonRoof["H"] * jsonRoof["A"] + jsonRoof["D"] * jsonRoof["C"] + \
                            (jsonRoof["C"] - jsonRoof["E"]) * jsonRoof["F"]
        elif self.type == "左凹形":
            self.edgeA = round(jsonRoof["A"] / UNIT)
            self.edgeB = round(jsonRoof["B"] / UNIT)
            self.edgeC = round(jsonRoof["C"] / UNIT)
            self.edgeD = round(jsonRoof["D"] / UNIT)
            self.edgeE = round(jsonRoof["E"] / UNIT)
            self.edgeF = round(jsonRoof["F"] / UNIT)
            self.edgeH = self.edgeF - self.edgeD + self.edgeB
            self.edgeG = self.edgeA + self.edgeC + self.edgeE
            self.height = jsonRoof["height"]
            self.length = self.edgeG
            self.width = max(self.edgeH, self.edgeF)
            self.roofArray = np.zeros((self.length, self.width))
            if self.edgeH >= self.edgeF:
                self.roofArray[0:self.edgeE, 0:self.edgeB - self.edgeD] = INF
                self.roofArray[self.edgeE:self.edgeE + self.edgeC, 0:self.edgeB] = INF
            else:
                self.roofArray[self.edgeE + self.edgeC:, 0:self.edgeD - self.edgeB] = INF
                self.roofArray[self.edgeE:self.edgeE + self.edgeC, 0:self.edgeD] = INF
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.obstacleArraySelf = []
            self.obstaclerange = []
            self.realWidth = jsonRoof["H"]
            self.realLength = jsonRoof["G"]
            self.realArea = jsonRoof["H"] * jsonRoof["A"] + jsonRoof["E"] * jsonRoof["F"] + \
                            (jsonRoof["H"] - jsonRoof["B"]) * jsonRoof["C"]
        elif self.type == "右凹形":
            self.edgeA = round(jsonRoof["A"] / UNIT)
            self.edgeB = round(jsonRoof["B"] / UNIT)
            self.edgeC = round(jsonRoof["C"] / UNIT)
            self.edgeD = round(jsonRoof["D"] / UNIT)
            self.edgeE = round(jsonRoof["E"] / UNIT)
            self.edgeF = round(jsonRoof["F"] / UNIT)
            self.edgeH = self.edgeB - self.edgeD + self.edgeF
            self.edgeG = self.edgeA - self.edgeC - self.edgeE
            self.height = jsonRoof["height"]
            self.length = self.edgeA
            self.width = max(self.edgeB, self.edgeH)
            self.roofArray = np.zeros((self.length, self.width))
            if self.edgeB > self.edgeH:
                self.roofArray[self.edgeC:self.edgeC + self.edgeE, self.edgeB - self.edgeD:] = INF
                self.roofArray[self.edgeC + self.edgeE:, self.edgeH:] = INF
            else:
                self.roofArray[self.edgeC:self.edgeC + self.edgeE, self.edgeH - self.edgeF:] = INF
                self.roofArray[0:self.edgeC, self.edgeB:] = INF
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.obstacleArraySelf = []
            self.obstaclerange = []
            self.realWidth = jsonRoof["B"]
            self.realLength = jsonRoof["A"]
            self.realArea = jsonRoof["B"] * jsonRoof["C"] + jsonRoof["G"] * jsonRoof["H"] + \
                            (jsonRoof["B"] - jsonRoof["D"]) * jsonRoof["E"]
        else:
            pass  # todo: 复杂屋顶的情况暂时不做处理
        # self.roofAngle = jsonRoof["roofAngle"]
        # self.roofDirection = jsonRoof["roofDirection"]
        self.windPressure = jsonLocation["windPressure"]
        self.snowPressure = jsonLocation["snowPressure"]
        self.windSnowPressure = jsonLocation["windAndSnowPressure"]
        self.latitude = latitude
        self.obstacles = []
        self.sceneObstacles = []
        self.height = jsonRoof["height"]
        self.layer = jsonRoof["layer"]
        self.columnType = ""
        # self.maxRects = []
        # self.allPlacements = collections.deque()
        self.allPlacements = []
        # self.type = 0

    def calculateObstacleSelf(self):
        # zzp: numpy加速
        return_list = np.zeros((self.realWidth + 3000, self.realLength + 3000), dtype=np.int32)
        # return_list = [[0] * ((self.realLength + 1000)) for _ in range((self.realWidth + 1000))]
        for obstacle in self.obstacles:
            if obstacle.type == '有烟烟囱':
                x_min = max(0, obstacle.realUpLeftPosition[0] - 100)
                x_max = min(self.realWidth, obstacle.realUpLeftPosition[0] + obstacle.realwidth + 100)
                y_min = max(0, obstacle.realUpLeftPosition[1] - 100)
                y_max = min(self.realLength, obstacle.realUpLeftPosition[1] + obstacle.reallength + 100)
                return_list[x_min:x_max, y_min:y_max] = 1
                self.obstaclerange.append([x_min, x_max])
                # for x in range(x_min, x_max):
                #     for y in range(y_min, y_max):
                #         return_list[x][y] = 1
            if obstacle.type == "屋面扣除":
                x_min = obstacle.upLeftPosition[0]
                x_max = obstacle.upLeftPosition[0] + obstacle.width
                y_min = obstacle.upLeftPosition[1]
                y_max = obstacle.realUpLeftPosition[1] + obstacle.length
                return_list[x_min:x_max, y_min:y_max] = 1
                # for x in range(x_min, x_max):
                #     for y in range(y_min, y_max):
                #         return_list[x][y] = 1
            if obstacle.type == "无烟烟囱":
                x_min = max(0, obstacle.realUpLeftPosition[0] - 100)
                x_max = min(self.realWidth, obstacle.realUpLeftPosition[0] + obstacle.realwidth + 100)
                self.obstaclerange.append((x_min, x_max))
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

    def getBestOptions(self, screenedArrangements, maxArrangeCount=-1, maxValue=0, maxComponentCount=INF):
        time1 = time.time()
        print("开始计算排布方案，当前时间为", time.strftime('%m-%d %H:%M:%S', time.localtime()))
        if maxArrangeCount < 0:
            maxArrangeCount = getMaxArrangeCount()  # 最大排布数量
        nowMaxValue = maxValue  # todo: 待优化，不需要遍历所有arrangement
        # 全局变量就不要传参，节省内存
        # screenedArrangements = {k: v for k, v in screenedArrangements.items() if v.legal} # 在screenArrangements函数中已经过滤了
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
        obstacleAdditionalArray = np.array(obstacleAdditionalArray)

        def addObstaclesConcern(placement):
            if len(placement[0]) == 1:
                # if placement[0][0]['ID'] == 398 and placement[0][0]['start'] == (3, 0):
                #     print("debug")
                mergeObstacleArray = self.obstacleArray
                tempObstacleSumArray = self.obstacleSumArray
            else:
                mergeObstacleArray = np.array(self.obstacleArray)
                for arrange in placement[0]:
                    arrangement = screenedArrangements[arrange['ID']]
                    sRPX, sRPY = arrangement.shadowRelativePosition
                    sizeY, sizeX = arrangement.shadowArray.shape
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
                arrangement = screenedArrangements[arrange['ID']]
                arrangeStartX, arrangeStartY = arrange['start']
                arrangement.calculateComponentPositionArray(arrangeStartX, arrangeStartY)
                tempArray = arrangement.componentPositionArray
                deletedIndices = []
                raiseLevel = 0
                for i, ((p00, p01), (p10, p11)) in enumerate(tempArray):
                    # zzp: 重复索引使用数量少还好，数量多了就很吃时间
                    obstacleIntersected = any(
                        not (additionalObstacle[2] > p10 or p00 > additionalObstacle[0] or
                             additionalObstacle[3] > p11 or p01 > additionalObstacle[1])
                        for additionalObstacle in obstacleAdditionalArray
                    )
                    if obstacleIntersected:
                        deletedIndices.append(i)
                        continue
                    totalComponent = tempObstacleSumArray[p11, p00]
                    if p00 > 0:
                        totalComponent -= tempObstacleSumArray[p11, p00 - 1]
                    if p01 > 0:
                        totalComponent -= tempObstacleSumArray[p01 - 1, p10]
                    if p00 > 0 and p01 > 0:
                        totalComponent += tempObstacleSumArray[p01 - 1, p00 - 1]
                    if totalComponent == 0:
                        continue
                    mergeArraySlice = mergeObstacleArray[p01:p11 + 1, p00:p10 + 1]
                    heightArraySlice = arrangement.componentHeightArray[p01 - arrangeStartY:p11 - arrangeStartY + 1,
                                       p00 - arrangeStartX:p10 - arrangeStartX + 1]
                    # boolArray = ne.evaluate("mergeArraySlice <= heightArraySlice")
                    boolArray = mergeArraySlice <= heightArraySlice
                    if boolArray.all():
                        continue
                    else:  # 做抬高分析
                        # if not hasattr(arrangement, "componentHeightArray1"):
                        #     arrangement.componentHeightArray1 = arrangement.calculateComponentHeightArray(raiseLevel=1)
                        # if not (mergeObstacleArray[p01:p11 + 1, p00:p10 + 1] <=
                        #         arrangement.componentHeightArray1[
                        #         p01 - arrangeStartY:p11 - arrangeStartY + 1,
                        #         p00 - arrangeStartX:p10 - arrangeStartX + 1]).all():
                        #     if not hasattr(arrangement, "componentHeightArray2"):
                        #         arrangement.componentHeightArray2 = arrangement.calculateComponentHeightArray(
                        #             raiseLevel=2)
                        #     if not (mergeObstacleArray[p01:p11 + 1, p00:p10 + 1] <=
                        #             arrangement.componentHeightArray2
                        #             [p01 - arrangeStartY:p11 - arrangeStartY + 1,
                        #             p00 - arrangeStartX:p10 - arrangeStartX + 1]).all():
                        #         deletedIndices.append(i)
                        # 优化代码：只比较boolArray中为false的点加上540和1000的抬高后是否满足条件（不要再计算一遍calculateComponentHeightArray）
                        falsePosition = np.argwhere(~boolArray)
                        for y, x in falsePosition:
                            if mergeObstacleArray[p01 + y, p00 + x] > arrangement.componentHeightArray[
                                p01 - arrangeStartY + y, p00 - arrangeStartX + x] + 460:
                                deletedIndices.append(i)
                                raiseLevel = 0
                                break
                            else:
                                raiseLevel = 1
                arrange["raiseLevel"] = raiseLevel

                placement[1] -= len(deletedIndices) * arrangement.component.power
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

            currentPanelCount = sum([screenedArrangements[ii['ID']].componentNum for ii in placements])
            for i, ID in enumerate(IDArray[startI:]):
                for y in range(startY, self.length, 20):
                    for x in range(startX, self.width, 20):
                        # if screenedArrangements[ID].componentLayoutArray == [10, 10, 16, 16]:
                        #     print("debug1")
                        # zzp：摆了也不如nowMax，那就直接跳过
                        if layer == maxArrangeCount and currentValue + screenedArrangements[ID].value < nowMaxValue:
                            break
                        if maxComponentCount < currentPanelCount + screenedArrangements[ID].componentNum:
                            continue
                        if layer > 0 and overlaps(x, y, screenedArrangements[ID], placements):
                            continue
                        if not canPlaceArrangementRoof(x, y, screenedArrangements[ID]):
                            continue
                        if len(placements) >= 1 and not canPlaceArrangementObstacle(
                                x, y, screenedArrangements[ID], obstacleArray, tempObstacleSumArray):
                            continue
                        # if screenedArrangements[ID].componentLayoutArray == [10, 10, 16, 16]:
                        #     print("debug2")
                        newPlacement = {'ID': ID, 'start': (x, y)}
                        placements.append(newPlacement)
                        currentValue += screenedArrangements[ID].value
                        if layer < maxArrangeCount:
                            temp, nowMaxValue = dfs(x + screenedArrangements[ID].relativePositionArray[0][1][0], y,
                                                    i,
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
            self.obstacles.append(
                Obstacle(obstacle, self.obstacleArray, self.roofArray, self.latitude, self.type, self.realWidth))
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
            # allTxtArray = []
            allTxt = ""
            arrangeI = 0
            tempSum = 0
            for arrange in allArrangement:
                startX, startY = arrange['start']
                tempArray, tempTxt = screenedArrangements[arrange['ID']].calculateStandColumn(startX, startY,
                                                                                              self.realWidth,
                                                                                              self.obstacleArraySelf,
                                                                                              placement[2][arrangeI],
                                                                                              self.type,
                                                                                              self.obstaclerange,
                                                                                              self.columnType)
                tempTxt = f"第{arrangeI + 1}个阵列的立柱排布：\n" + tempTxt + "\n"
                tempSum += len(tempArray)
                allTempArray.append(tempArray)
                # allTxtArray.append(tempTxt)
                allTxt += tempTxt
                arrangeI += 1
            placement.extend([allTempArray, allTxt])

            if tempSum < nowMinValue:
                nowMinValue = tempSum

        self.allPlacements = [placement for placement in self.allPlacements if
                              sum([len(x) for x in placement[3]]) >= nowMinValue]
        print(
            f"立柱排布计算完成，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}，共有{len(self.allPlacements)}个较优排布方案\n")
        return nowMinValue

    def drawPlacement(self, screenedArrangements):  # todo: numpy优化
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
                    startX = round(obstacle.realUpLeftPosition[0] / UNIT) * magnification
                    startY = round(obstacle.realUpLeftPosition[1] / UNIT) * magnification
                    endX = round((obstacle.realUpLeftPosition[0] + obstacle.realwidth) / UNIT) * magnification
                    endY = round((obstacle.realUpLeftPosition[1] + obstacle.reallength) / UNIT) * magnification

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
            publicMatrix = np.fliplr(publicMatrix)
        elif self.type == "反7形":
            MA, MB, MC = self.edgeA * magnification, self.edgeB * magnification, self.edgeC * magnification
            MD, ME, MF = self.edgeD * magnification, self.edgeE * magnification, self.edgeF * magnification
            publicMatrix[:roofBoardLength, :MB, :] = RoofMarginColor
            publicMatrix[roofBoardLength:MC, MB - roofBoardLength:MB, :] = RoofMarginColor
            publicMatrix[MC - roofBoardLength:MC, MF - roofBoardLength:MB - roofBoardLength, :] = RoofMarginColor
            publicMatrix[MC:MA, MF - roofBoardLength:MF, :] = RoofMarginColor
            publicMatrix[MA - roofBoardLength:MA, :MF - roofBoardLength, :] = RoofMarginColor
            publicMatrix[roofBoardLength:MA - roofBoardLength, :roofBoardLength, :] = RoofMarginColor
        elif self.type == "正L形":  # ok
            MA, MB, MC, MD, ME = self.edgeA * magnification, self.edgeB * magnification, self.edgeC * magnification, self.edgeD * magnification, self.edgeE * magnification
            publicMatrix[:, :roofBoardLength, :] = RoofMarginColor  # 左边界
            publicMatrix[-roofBoardLength:, :, :] = RoofMarginColor  # 下边界
            publicMatrix[-ME:, -roofBoardLength:, :] = RoofMarginColor  # 右边界
            publicMatrix[MC:MC + roofBoardLength, MB - roofBoardLength:, :] = RoofMarginColor  # D边
            publicMatrix[:MC, MB - roofBoardLength:MB, :] = RoofMarginColor  # C边
            publicMatrix[:roofBoardLength, :MB, :] = RoofMarginColor  # B边
        elif self.type == "反L形":  # ok1
            MA, MB, MC, MD, ME = self.edgeA * magnification, self.edgeB * magnification, self.edgeC * magnification, self.edgeD * magnification, self.edgeE * magnification
            publicMatrix[MC:MC + roofBoardLength, :MB + roofBoardLength, :] = RoofMarginColor  # B边
            publicMatrix[:MC, MB:MB + roofBoardLength, :] = RoofMarginColor  # C边
            publicMatrix[:roofBoardLength, MB + roofBoardLength:, :] = RoofMarginColor  # D边
            publicMatrix[roofBoardLength:, -roofBoardLength:, :] = RoofMarginColor  # E边
            publicMatrix[-roofBoardLength:, :-roofBoardLength, :] = RoofMarginColor  # F边
            publicMatrix[MC + roofBoardLength:-roofBoardLength, :roofBoardLength, :] = RoofMarginColor  # C边
        elif self.type == "上凸形":  # ok
            MA, MB, MC, MD = self.edgeA * magnification, self.edgeB * magnification, self.edgeC * magnification, self.edgeD * magnification
            ME, MF, MG, MH = self.edgeE * magnification, self.edgeF * magnification, self.edgeG * magnification, self.edgeH * magnification
            publicMatrix[MC:, :roofBoardLength, :] = RoofMarginColor  # A边界
            publicMatrix[MC:MC + roofBoardLength, roofBoardLength:MB, :] = RoofMarginColor  # B边界
            publicMatrix[:MC + roofBoardLength, MB:MB + roofBoardLength, :] = RoofMarginColor  # C边界
            publicMatrix[:roofBoardLength, MB + roofBoardLength:MB + MD, :] = RoofMarginColor  # D边界
            publicMatrix[roofBoardLength:ME + roofBoardLength, MB + MD - roofBoardLength:MB + MD, :] = RoofMarginColor
            publicMatrix[ME:ME + roofBoardLength, MB + MD:MB + MD + MF, :] = RoofMarginColor  # F边界
            publicMatrix[ME + roofBoardLength:, MB + MD + MF - roofBoardLength:, :] = RoofMarginColor  # G边界
            publicMatrix[-roofBoardLength:, roofBoardLength:MH - roofBoardLength, :] = RoofMarginColor  # H边界
        elif self.type == "下凸形":  # ok1
            MA, MB, MC, MD, ME, MF, MG, MH = self.edgeA * magnification, self.edgeB * magnification, self.edgeC * magnification, self.edgeD * magnification, self.edgeE * magnification, self.edgeF * magnification, self.edgeG * magnification, self.edgeH * magnification
            # 边界赋值逻辑
            publicMatrix[:roofBoardLength, :, :] = RoofMarginColor  # D边
            publicMatrix[roofBoardLength:ME, -roofBoardLength:, :] = RoofMarginColor  # E边
            publicMatrix[ME - roofBoardLength:ME, MD - MF:MD - roofBoardLength, :] = RoofMarginColor  # F边
            publicMatrix[-MG - roofBoardLength:, -roofBoardLength - MF:-MF, :] = RoofMarginColor  # G边
            publicMatrix[-roofBoardLength:, MB:MB + MH - roofBoardLength, :] = RoofMarginColor  # H边
            publicMatrix[-MA - roofBoardLength: - roofBoardLength, MB:MB + roofBoardLength, :] = RoofMarginColor  # A边
            publicMatrix[MC - roofBoardLength:MC, :MB, :] = RoofMarginColor  # B边
            publicMatrix[roofBoardLength:MC - roofBoardLength, :roofBoardLength, :] = RoofMarginColor  # A边
        elif self.type == "左凸形":  # ok1
            MA, MB, MC, MD, ME, MF, MH, MG = self.edgeA * magnification, self.edgeB * magnification, self.edgeC * magnification, self.edgeD * magnification, self.edgeE * magnification, self.edgeF * magnification, self.edgeH * magnification, self.edgeG * magnification
            # 边界赋值逻辑
            publicMatrix[ME:ME + roofBoardLength, :MD, :] = RoofMarginColor  # D边
            publicMatrix[ME + roofBoardLength:MC + ME, :roofBoardLength, :] = RoofMarginColor  # C边
            publicMatrix[MC + ME - roofBoardLength:MC + ME, roofBoardLength:roofBoardLength + MB,
            :] = RoofMarginColor  # B边
            publicMatrix[MC + ME:, MB:MB + roofBoardLength, :] = RoofMarginColor  # A边
            publicMatrix[-roofBoardLength:, MB + roofBoardLength:, :] = RoofMarginColor  # H边
            publicMatrix[:-roofBoardLength, -roofBoardLength:, :] = RoofMarginColor  # G边
            publicMatrix[:roofBoardLength, MD:-roofBoardLength, :] = RoofMarginColor  # F边
            publicMatrix[roofBoardLength:ME + roofBoardLength, MD:MD + roofBoardLength, :] = RoofMarginColor  # E边
        elif self.type == "右凸形":  # ok1
            MA, MB, MC, MD, ME, MF, MG, MH = self.edgeA * magnification, self.edgeB * magnification, self.edgeC * magnification, self.edgeD * magnification, self.edgeE * magnification, self.edgeF * magnification, self.edgeG * magnification, self.edgeH * magnification
            publicMatrix[roofBoardLength:, :roofBoardLength, :] = RoofMarginColor  # A边
            publicMatrix[:roofBoardLength, :MB, :] = RoofMarginColor  # B边
            publicMatrix[roofBoardLength:MC, MB - roofBoardLength:MB, :] = RoofMarginColor  # C边
            publicMatrix[MC:MC + roofBoardLength, MB - roofBoardLength:, :] = RoofMarginColor  # D边
            publicMatrix[MC + roofBoardLength:MC + ME, -roofBoardLength:, :] = RoofMarginColor  # E边
            publicMatrix[MC + ME - roofBoardLength:MC + ME, -MF - roofBoardLength:-roofBoardLength,
            :] = RoofMarginColor  # F边
            publicMatrix[-MG:, -MF - roofBoardLength:-MF, :] = RoofMarginColor  # G边
            publicMatrix[-roofBoardLength:, roofBoardLength:-MF - roofBoardLength, :] = RoofMarginColor  # H边
        elif self.type == "上凹形":  # ok1
            MA, MB, MC, MD, ME, MF, MG, MH = self.edgeA * magnification, self.edgeB * magnification, self.edgeC * magnification, self.edgeD * magnification, self.edgeE * magnification, self.edgeF * magnification, self.edgeG * magnification, self.edgeH * magnification
            if MC >= ME:
                publicMatrix[:, :roofBoardLength, :] = RoofMarginColor  # A边
                publicMatrix[:roofBoardLength, roofBoardLength:MB, :] = RoofMarginColor  # B边
                publicMatrix[roofBoardLength:MC + roofBoardLength, MB - roofBoardLength:MB, :] = RoofMarginColor  # C边
                publicMatrix[MC:MC + roofBoardLength, MB:MB + MD + roofBoardLength, :] = RoofMarginColor  # D边
                publicMatrix[MC - ME:MC, MB + MD:MB + MD + roofBoardLength, :] = RoofMarginColor  # E边
                publicMatrix[MC - ME:MC - ME + roofBoardLength, MB + MD + roofBoardLength:, :] = RoofMarginColor  # F边
                publicMatrix[MC - ME + roofBoardLength:, -roofBoardLength:, :] = RoofMarginColor  # G边
            else:
                publicMatrix[ME - MC:, :roofBoardLength, :] = RoofMarginColor  # A边
                publicMatrix[ME - MC:ME - MC + roofBoardLength, roofBoardLength:MB, :] = RoofMarginColor  # B边
                publicMatrix[ME - MC + roofBoardLength:ME + roofBoardLength, MB - roofBoardLength:MB,
                :] = RoofMarginColor  # C边
                publicMatrix[ME:ME + roofBoardLength, MB:MB + MD + roofBoardLength, :] = RoofMarginColor  # D边
                publicMatrix[:ME, MB + MD:MB + MD + roofBoardLength, :] = RoofMarginColor  # E边
                publicMatrix[:roofBoardLength, MB + MD + roofBoardLength:, :] = RoofMarginColor  # F边
                publicMatrix[roofBoardLength:, -roofBoardLength:, :] = RoofMarginColor  # G边
            publicMatrix[-roofBoardLength:, roofBoardLength:-roofBoardLength, :] = RoofMarginColor  # H边
        elif self.type == "下凹形":  # ok1
            MA, MB, MC, MD, ME, MF, MG, MH = self.edgeA * magnification, self.edgeB * magnification, self.edgeC * magnification, self.edgeD * magnification, self.edgeE * magnification, self.edgeF * magnification, self.edgeG * magnification, self.edgeH * magnification
            if MG <= ME:
                publicMatrix[MA - roofBoardLength:MA, roofBoardLength:MH, :] = RoofMarginColor  # H边
                publicMatrix[MA - MG:MA - roofBoardLength, MH - roofBoardLength:MH, :] = RoofMarginColor  # G边
                publicMatrix[MA - MG - roofBoardLength:MA - MG, MH:MH + MF + roofBoardLength, :] = RoofMarginColor  # F边
                publicMatrix[-ME:, MH + MF:MH + MF + roofBoardLength, :] = RoofMarginColor  # E边
                publicMatrix[-roofBoardLength:, MH + MF + roofBoardLength:, :] = RoofMarginColor  # D边
                publicMatrix[:-roofBoardLength, -roofBoardLength:, :] = RoofMarginColor  # C边
            else:
                publicMatrix[-roofBoardLength:, roofBoardLength:MH, :] = RoofMarginColor  # H边
                publicMatrix[-roofBoardLength - MG:, MH - roofBoardLength:MH, :] = RoofMarginColor  # G边
                publicMatrix[-MG - roofBoardLength:-MG, MH:MH + MF + roofBoardLength, :] = RoofMarginColor  # F边
                publicMatrix[-MG:-MG + ME, MH + MF:MH + MF + roofBoardLength, :] = RoofMarginColor  # E边
                publicMatrix[-MG + ME - roofBoardLength:-MG + ME, MH + MF + roofBoardLength:, :] = RoofMarginColor  # D边
                publicMatrix[:MC - roofBoardLength, -roofBoardLength:, :] = RoofMarginColor  # C边
            publicMatrix[:MA, :roofBoardLength, :] = RoofMarginColor  # A边
            publicMatrix[:roofBoardLength, roofBoardLength:-roofBoardLength, :] = RoofMarginColor  # B边
        elif self.type == "左凹形":  # ok1
            MA, MB, MC, MD, ME, MF, MG, MH = self.edgeA * magnification, self.edgeB * magnification, self.edgeC * magnification, self.edgeD * magnification, self.edgeE * magnification, self.edgeF * magnification, self.edgeG * magnification, self.edgeH * magnification
            if MB >= MD:
                publicMatrix[-MA:, :roofBoardLength, :] = RoofMarginColor  # A边
                publicMatrix[-MA:-MA + roofBoardLength, roofBoardLength:MB + roofBoardLength, :] = RoofMarginColor  # B边
                publicMatrix[ME - roofBoardLength:ME + MC, MB:MB + roofBoardLength, :] = RoofMarginColor  # C边
                publicMatrix[ME - roofBoardLength:ME, MB - MD:MB, :] = RoofMarginColor  # D边
                publicMatrix[:ME - roofBoardLength, MB - MD:MB - MD + roofBoardLength, :] = RoofMarginColor  # E边
                publicMatrix[:roofBoardLength, MB - MD:, :] = RoofMarginColor  # F边
                publicMatrix[-roofBoardLength:, roofBoardLength:-roofBoardLength, :] = RoofMarginColor  # H边
            else:
                publicMatrix[-MA:, MD - MB:MD - MB + roofBoardLength, :] = RoofMarginColor  # A边
                publicMatrix[-MA:-MA + roofBoardLength, MD - MB + roofBoardLength:MD + roofBoardLength,
                :] = RoofMarginColor  # B边
                publicMatrix[ME - roofBoardLength:ME + MC, MD:MD + roofBoardLength, :] = RoofMarginColor  # C边
                publicMatrix[ME - roofBoardLength:ME, :MD, :] = RoofMarginColor  # D边
                publicMatrix[:ME - roofBoardLength, :roofBoardLength, :] = RoofMarginColor  # E边
                publicMatrix[:roofBoardLength, roofBoardLength:MF, :] = RoofMarginColor  # F边
                publicMatrix[-roofBoardLength:, MD - MB:, :] = RoofMarginColor  # H边
            publicMatrix[roofBoardLength:, -roofBoardLength:, :] = RoofMarginColor  # G边
        elif self.type == "右凹形":
            MA, MB, MC, MD, ME, MF, MG, MH = self.edgeA * magnification, self.edgeB * magnification, self.edgeC * magnification, self.edgeD * magnification, self.edgeE * magnification, self.edgeF * magnification, self.edgeG * magnification, self.edgeH * magnification
            publicMatrix[:, :roofBoardLength, :] = RoofMarginColor  # A边
            if MD >= MF:
                publicMatrix[:roofBoardLength, roofBoardLength:, :] = RoofMarginColor  # B边
                publicMatrix[roofBoardLength:MC, -roofBoardLength:, :] = RoofMarginColor  # C边
                publicMatrix[MC - roofBoardLength:MC, -MD - roofBoardLength:-roofBoardLength, :] = RoofMarginColor  # D边
                publicMatrix[MC:MC + ME + roofBoardLength, -MD - roofBoardLength:-MD, :] = RoofMarginColor  # E边
                publicMatrix[MC + ME:MC + ME + roofBoardLength, -MD:-MD - MF, :] = RoofMarginColor  # F边
                publicMatrix[-MG + roofBoardLength:, -MD + MF - roofBoardLength:-MD + MF, :] = RoofMarginColor  # G边
                publicMatrix[-roofBoardLength:, roofBoardLength:MH - roofBoardLength, :] = RoofMarginColor  # H边
            else:
                publicMatrix[:roofBoardLength, roofBoardLength:MB, :] = RoofMarginColor  # B边
                publicMatrix[roofBoardLength:MC, MB - roofBoardLength:MB, :] = RoofMarginColor  # C边
                publicMatrix[MC - roofBoardLength:MC, MB - MD - roofBoardLength:MB - roofBoardLength,
                :] = RoofMarginColor  # D边
                publicMatrix[MC:MC + ME + roofBoardLength, MB - MD - roofBoardLength:MB - MD, :] = RoofMarginColor  # E边
                publicMatrix[MC + ME:MC + ME + roofBoardLength, -MF:, :] = RoofMarginColor  # F边
                publicMatrix[-MG + roofBoardLength:, -roofBoardLength:, :] = RoofMarginColor  # G边
                publicMatrix[-roofBoardLength:, roofBoardLength:-roofBoardLength, :] = RoofMarginColor  # H边

        for point in obstaclePointArray:
            publicMatrix[point[1], point[0]] = ObstacleColor

        for placement in self.allPlacements[:outputPlacementCount]:
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
            # 判断屋面类型，决定是否要左右镜像翻转
            if self.type == "正7形":
                image_array = np.fliplr(image_array)

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
