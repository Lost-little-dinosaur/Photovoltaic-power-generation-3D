from PIL import Image
import numpy as np
import time
import matplotlib.pyplot as plt
from const.const import *
from tools.getData import dataDict
from tools.hullCalculation import getConvexHull, isPointInsideConvexHull
from math import tan, radians, cos, sin, sqrt
from classes.component import Component
from classes.obstacle import Obstacle


# 输入都是以毫米为单位的
class Roof:
    def __init__(self, jsonRoof, latitude):
        self.eastExtend, self.westExtend, self.southExtend, self.northExtend = jsonRoof["extensibleDistance"]
        if not jsonRoof["isComplex"]:
            self.length = round((jsonRoof["length"] + self.southExtend + self.northExtend) / UNIT)
            self.width = round((jsonRoof["width"] + self.eastExtend + self.westExtend) / UNIT)
            self.height = jsonRoof["height"]
            self.roofArray = np.full((self.length, self.width), 0)
            self.roofSumArray = np.cumsum(np.cumsum(self.roofArray, axis=0), axis=1)
            self.obstacleArray = np.full((self.length, self.width), 0)
            self.standColumnArray = np.full((self.length, self.width), 0)
            self.showArray = np.full((self.length, self.width, 4), EmptyColor)
        else:
            pass  # todo: 复杂屋顶的情况暂时不做处理
        self.roofAngle = jsonRoof["roofAngle"]
        self.roofDirection = jsonRoof["roofDirection"]
        self.latitude = latitude
        self.obstacles = []
        self.sceneObstacles = []
        # self.maxRects = []
        self.allPlacements = []

    def addObstacle(self, obstacle):
        self.obstacles.append(Obstacle(obstacle, self.obstacleArray, self.roofArray, self.latitude))

    def addSceneObstacle(self, obstacle):  # todo: 有可能没用
        self.sceneObstacles.append(Obstacle(obstacle, self.obstacleArray, self.roofArray, self.latitude))

    def paintBoolArray(self, lib):
        time1 = time.time()
        # 额外加上roofBoardLength的屋顶边缘（不要删，留着备用！！！）
        # tempArr = np.pad(self.showArray, ((roofBoardLength, roofBoardLength), (roofBoardLength, roofBoardLength),
        #                                   (0, 0)), 'constant', constant_values=RoofMargin)
        # rgb_array = np.array([[ColorDict[value] for value in row] for row in tempArr])
        height, width, channels = self.showArray.shape
        tempArr = np.zeros((height + 2 * roofBoardLength, width + 2 * roofBoardLength, channels))
        # 设置边界值
        for i in range(channels):
            tempArr[:, :, i] = RoofMarginColor[i]
        # 填充中间区域
        tempArr[roofBoardLength:-roofBoardLength, roofBoardLength:-roofBoardLength, :] = self.showArray
        if lib == "plt":
            plt.imshow(tempArr)
            plt.axis('off')
            plt.show()
        elif lib == "img":
            img = Image.fromarray((tempArr * 255).astype(np.uint8))
            img.show()
        else:
            raise Exception("lib参数错误: ", lib)
        print("屋顶排布示意图绘制完成，耗时", time.time() - time1, "秒\n")

    def getValidOptions(self, arrangements):
        def dfs(arrangeArray, startX=0, startY=0, currentValue=0, placements=None):
            if placements is None:
                placements = []
            betterFlag = False
            for y in range(startY, self.length):
                for x in range(startX, self.width):
                    for arrangement in arrangeArray:
                        if canPlaceArrangement(x, y, arrangement) and not overlaps(x, y, arrangement, placements):
                            newPlacement = {'ID': arrangement.ID, 'start': [x, y],
                                            "relativePositionArray": arrangement.relativePositionArray}
                            placements.append(newPlacement)
                            # print("当前placements的ID为：", [placement['ID'] for placement in placements], "startX为：",
                            #       x, "startY为：", y)
                            temp = dfs(arrangeArray, x + arrangement.relativePositionArray[0][1][0], y,
                                       currentValue + arrangement.value, placements)
                            if temp:
                                betterFlag = True
                            else:
                                # print("得到一个排布方案：", [placement['ID'] for placement in placements],
                                #       "，当前value为", currentValue,
                                #       "，时间为", time.strftime("%m-%d %H:%M:%S", time.localtime()))
                                self.allPlacements.append((placements.copy(), currentValue))
                                if len(self.allPlacements) % 100000 == 0:
                                    print(
                                        f"已经计算了{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}")
                            placements.pop()
                startX = 0
            return betterFlag

        def canPlaceArrangement(x, y, arrange):
            for eachRect in arrange.relativePositionArray:
                startX, startY = eachRect[0]
                endX, endY = eachRect[1]
                absoluteEndX, absoluteEndY = x + endX, y + endY
                if self.width > absoluteEndX and self.length > absoluteEndY:
                    total = self.roofSumArray[absoluteEndY][absoluteEndX]
                    if startX > 0:
                        total -= self.roofSumArray[absoluteEndY][x + startX - 1]
                    if startY > 0:
                        total -= self.roofSumArray[y + startY - 1][absoluteEndX]
                    if startX > 0 and startY > 0:
                        total += self.roofSumArray[y + startY - 1][x + startX - 1]
                    if total >= INF:
                        return False
                else:
                    return False
            return True

        def overlaps(x, y, arrange, placements):
            for eachRect in arrange.relativePositionArray:
                for placement in placements:
                    startX, startY = placement['start']
                    for eachPlacementRect in placement["relativePositionArray"]:
                        if not (x + eachRect[0][0] > startX + eachPlacementRect[1][0] or
                                x + eachRect[1][0] < startX + eachPlacementRect[0][0] or
                                y + eachRect[0][1] > startY + eachPlacementRect[1][1] or
                                y + eachRect[1][1] < startY + eachPlacementRect[0][1]):
                            return True
            return False

        arrangements.sort(key=lambda x: x.value, reverse=True)
        dfs(arrangements)
        print(self.allPlacements)
        print(f"共有{len(self.allPlacements)}个排布方案")
        exit(0)
        return self.allPlacements

    def removeComponentsWithFalseFool(self):
        # 创建一个新的列表用于存储要保留的元素
        updatedRects = []
        for rect in self.maxRects:
            if self.canPlaceComponent(rect.endY, rect.endX, rect.endY - rect.startY + 1, rect.endX - rect.startX + 1):
                updatedRects.append(rect)
        print(f"删除了{len(self.maxRects) - len(updatedRects)}个组件，剩余{len(updatedRects)}个组件")
        self.maxRects = updatedRects  # 更新 maxRects 列表为新列表

    def renewRects2Array(self):
        time1 = time.time()
        for rect1 in self.maxRects:  # todo: 还需要考虑一下万一PhotovoltaicPanelBoardLength超过了start和end的范围的情况
            self.obstacleArray[rect1.startY:rect1.endY + 1, rect1.startX:rect1.endX + 1] = False
            # 修边
            rect1.marginRight, rect1.marginBottom = PhotovoltaicPanelCrossMargin, PhotovoltaicPanelVerticalMargin

        for rect1 in self.maxRects:
            # 修边
            if rect1.direction == 1:
                for rect2 in self.maxRects:
                    if rect2.direction == 2:
                        # 如果rect1下方+round(PhotovoltaicPanelVerticalDiffMargin / UNIT)+1的位置有rect2，那么rect1的下边距就要加上这个间距
                        tempY = rect1.endY + rect1.marginBottom + PhotovoltaicPanelVerticalDiffMargin + 1
                        for tempX in range(rect1.startX, rect1.endX + 1):
                            if rect2.startX <= tempX <= rect2.endX and rect2.startY <= tempY <= rect2.endY:
                                rect1.marginBottom += PhotovoltaicPanelVerticalDiffMargin
                                break
            else:
                for rect2 in self.maxRects:
                    if rect2.direction == 1:
                        # 如果rect1下方+round(PhotovoltaicPanelVerticalDiffMargin / UNIT)+1的位置有rect2，那么rect1的下边距就要加上这个间距
                        tempY = rect1.endY + rect1.marginBottom + PhotovoltaicPanelVerticalDiffMargin + 1
                        for tempX in range(rect1.startX, rect1.endX + 1):
                            if rect2.startX <= tempX <= rect2.endX and rect2.startY <= tempY <= rect2.endY:
                                rect1.marginBottom += PhotovoltaicPanelVerticalDiffMargin
                                break

            if rect1.marginRight + rect1.endX + 1 < self.width and np.sum(
                    self.obstacleArray[rect1.startY:rect1.endY + 1, rect1.endX + rect1.marginRight + 1:
                    rect1.endX + rect1.marginRight + 2]) == rect1.endY - rect1.startY + 1:
                rect1.marginRight = 0
            if rect1.marginBottom + rect1.endY + 1 < self.length and np.sum(
                    self.obstacleArray[rect1.endY + rect1.marginBottom + 1:rect1.endY + rect1.marginBottom + 2,
                    rect1.startX:rect1.endX + 1]) == rect1.endX - rect1.startX + 1:
                rect1.marginBottom = 0

            self.showArray[rect1.startY:rect1.endY + 1,
            rect1.startX:rect1.startX + PhotovoltaicPanelBoardLength] = PhotovoltaicPanelBorderColor
            self.showArray[rect1.startY:rect1.endY + 1,
            rect1.endX - PhotovoltaicPanelBoardLength + 1:rect1.endX + 1] = PhotovoltaicPanelBorderColor
            self.showArray[rect1.startY:rect1.startY + PhotovoltaicPanelBoardLength,
            rect1.startX + PhotovoltaicPanelBoardLength:rect1.endX - PhotovoltaicPanelBoardLength + 1] = PhotovoltaicPanelBorderColor
            self.showArray[rect1.endY - PhotovoltaicPanelBoardLength + 1:rect1.endY + 1,
            rect1.startX + PhotovoltaicPanelBoardLength:rect1.endX - PhotovoltaicPanelBoardLength + 1] = PhotovoltaicPanelBorderColor
            self.showArray[rect1.startY + PhotovoltaicPanelBoardLength:rect1.endY - PhotovoltaicPanelBoardLength + 1,
            rect1.startX + PhotovoltaicPanelBoardLength:rect1.endX - PhotovoltaicPanelBoardLength + 1] = PhotovoltaicPanelColor

            self.showArray[rect1.endY + 1:rect1.endY + rect1.marginBottom + 1,
            rect1.startX:rect1.endX + rect1.marginRight + 1] = PhotovoltaicPanelMarginColor
            self.showArray[rect1.startY:rect1.endY + 1,
            rect1.endX + 1:rect1.endX + rect1.marginRight + 1] = PhotovoltaicPanelMarginColor

            # 再次更新bool_array
            self.obstacleArray[rect1.startY:rect1.endY + rect1.marginBottom + 1,
            rect1.startX:rect1.endX + rect1.marginRight + 1] = False

        print("已更新show_array和bool_array，耗时", time.time() - time1, "秒\n")

# dp排布的arrangement排布函数1（留着备用！！！）
# time1 = time.time()
#         print("正在计算最佳方案...当前时间为", time.strftime("%m-%d %H:%M:%S", time.localtime()))
#
#         def updateMaxRects(arrange, sY, sX, maxRects, max_count):  # 用于竖排放置方式的更新
#             def overlaps(rect1, rect2):
#                 return not (
#                         rect1.endX < rect2.startX or rect1.endY < rect2.startY or rect2.endX < rect1.startX or rect2.endY < rect1.startY)
#
#             for eachRect in arrange.relativePositionArray:
#                 # 判断是否和maxRects中的矩形重叠
#                 startX, startY = eachRect[0]
#                 endX, endY = eachRect[1]
#                 absoluteEndX, absoluteEndY = sX + endX, sY + endY
#                 newRect = Component("tmp", INF, INF, INF, INF, sX + startX, sY + startY, absoluteEndX, absoluteEndY,
#                                     1, 0, 0)
#                 if any(overlaps(existingRect, newRect) for existingRect in maxRects):
#                     return max_count, False
#             arrange.calculateComponentArray(sX, sY)
#             maxRects.extend(arrange.componentArray)
#             return max_count + len(arrange.componentArray), True
#
#         # 先对arrangements按不同关键字排序，verticalCount从大到小，crossCount从大到小
#         arrangements.sort(key=lambda x: x.value, reverse=True)
#         maxCount = 0
#         self.maxRects = []
#         breakFlag = False
#         for k in range(len(arrangements)):
#             print("正在计算第", k + 1, "/", len(arrangements), "个组件的最佳方案，当前时间为",
#                   time.strftime("%m-%d %H:%M:%S", time.localtime()))
#             i = 0
#             while i < self.length:
#                 j = 0
#                 while j < self.width:
#                     if self.canPlaceArrangement(i, j, arrangements[k]):
#                         maxCount, addFlag = updateMaxRects(arrangements[k], i, j, self.maxRects, maxCount)
#                         # 更新光伏板之间的间距（在最后利用maxRects一起更新bool数组和show数组）
#                         if addFlag:
#                             # j += width - 2
#                             breakFlag = True
#                             break
#                     # j += renewJ(i - length + 1, j - width + 1, self.maxRects)  # 快速更新j（非常重要！！！）
#                     j += 1
#                 if breakFlag:
#                     break
#                 i += 1
#         print("最佳方案计算完成，耗时", time.time() - time1, "秒，最多可以放置", maxCount, "块光伏板" + "，当前精度为",
#               UNIT, "米\n")
#         return self.maxRects

# dp排布的arrangement排布函数2（留着备用！！！）
#     def getBestOption(self, arrangements):
#         time1 = time.time()
#         print("正在计算最佳方案...当前时间为", time.strftime("%m-%d %H:%M:%S", time.localtime()))
#         self.maxRects = []
#         dp = np.zeros((self.length, self.width), dtype=int)
#         choice = np.full((self.length, self.width), None, dtype=object)  # 存储选择的arrangement和位置信息
#         overlapCache = {}  # 用于缓存overlaps函数的结果
#         minLength, minWidth = INF, INF
#
#         # def overlaps(rect1, rect2):
#         #     r1EndX = rect1.startX + rect1.width - 1
#         #     r1EndY = rect1.startY + rect1.length - 1
#         #     r2EndX = rect2.startX + rect2.width - 1
#         #     r2EndY = rect2.startY + rect2.length - 1
#         #     return not (
#         #             r1EndX < rect2.startX or r1EndY < rect2.startY or r2EndX < rect1.startX or r2EndY < rect1.startY)
#
#         for arrangement in arrangements:
#             minLength = min(minLength, arrangement.length)
#             minWidth = min(minWidth, arrangement.width)
#         # 给左上角的dp数组赋值为0
#         minLength, minWidth = minLength - 1, minWidth - 1
#         dp[0:minLength, :] = 0
#         for i in range(minLength, self.length):
#             for j in range(minWidth, self.width):
#                 for arrangement in arrangements:
#                     if i - arrangement.length + 1 >= 0 and j - arrangement.width + 1 >= 0 and \
#                             self.canPlaceRectangle(i, j, arrangement.length, arrangement.width):
#                         newValue = dp[i - arrangement.length + 1, j - arrangement.width + 1] + arrangement.value
#                         if newValue > dp[i, j]:
#                             dp[i, j] = newValue
#                             # choice[i, j] = (str(choice[i - arrangement.length + 1, j - arrangement.width + 1]) + "+" +
#                             #                 str(arrangement.ID)) if choice[i - arrangement.length + 1, j - arrangement.
#                             # width + 1] is not None else arrangement.ID
#                             choice[i, j] = arrangement.ID
#             print("正在计算第", i + 1, "/", self.length, "行，时间", time.strftime("%m-%d %H:%M:%S", time.localtime()))
#
#         # 回溯找出放置的arrangement和位置
#         i, j = self.length - 1, self.width - 1
#         usedArrangements = []
#         arrangement = None
#         maxValue = 0
#         while i >= 0:
#             j = self.width - 1
#             while j >= 0:
#                 if choice[i, j] is not None:
#                     for tempArrangement in arrangements:
#                         if tempArrangement.ID == choice[i, j]:
#                             arrangement = tempArrangement  # 如果要加overlaps判断，记得在这里给startXY赋值
#                             break
#                     if arrangement is not None:  # 暂时不加overlaps判断，要加的话记得在前面给startXY赋值（and (len(usedArrangements) == 0 or any(not overlaps(arrangement, usedArrangement) for usedArrangement in usedArrangements))）
#                         choice[i - arrangement.length + 1:i + 1, j - arrangement.width + 1:j + 1] = None  # 非常重要！！！
#                         arrangement.calculateComponentArray(j - arrangement.width + 1, i - arrangement.length + 1)
#                         maxValue += arrangement.value
#                         self.maxRects.extend(arrangement.componentArray)
#                         tempArrangement = deepcopy(arrangement)
#                         tempArrangement.startY, tempArrangement.startX = i - arrangement.length + 1, j - arrangement.width + 1
#                         usedArrangements.append(tempArrangement)
#                         j -= arrangement.width
#                         arrangement = None
#                 else:
#                     j -= 1
#             i -= 1
#         print("最佳方案计算耗时", time.time() - time1, "秒，最大价值为", maxValue, "铺设了", len(self.maxRects),
#               "块组件\n")

# 贪心排布的arrangement排布函数（留着备用！！！）
#     def getBestOption(self, arrangements):
#         time1 = time.time()
#         print("正在计算最佳方案...当前时间为", time.strftime("%m-%d %H:%M:%S", time.localtime()))
#
#         def updateMaxRects(arrange, mY, mX, Len, Wid, maxRects, max_count, now_y, direct):  # 用于竖排放置方式的更新
#             newRect = Component("tmp", INF, INF, INF, INF, INF, INF, mX - Wid + 1, mY - Len + 1, mX, mY, direct,
#                                 round(PhotovoltaicPanelCrossMargin / UNIT),
#                                 round(PhotovoltaicPanelVerticalMargin / UNIT))  # 先假装是一个组件，方便排布
#
#             def overlaps(rect1, rect2):
#                 return not (
#                         rect1.endX < rect2.startX or rect1.endY < rect2.startY or rect2.endX < rect1.startX or rect2.endY < rect1.startY)
#
#             if not any(overlaps(existingRect, newRect) for existingRect in maxRects):
#                 arrange.calculateComponentArray(newRect.startX, newRect.startY)
#                 maxRects.extend(arrange.componentArray)
#                 max_count += 1
#                 return max_count, mY, True
#             else:
#                 return max_count, now_y, False
#
#         def renewJ(y, x, maxRects):
#             for r in maxRects:
#                 if r.startY <= y <= r.endY and r.startX <= x <= r.endX:
#                     return r.endX - x + 1
#             return 1
#
#         # 先对arrangements按不同关键字排序，verticalCount从大到小，crossCount从大到小
#         arrangements.sort(key=lambda x: (x.verticalCount, x.verticalNum, x.crossCount, x.crossNum), reverse=True)
#         maxCount = 0
#         self.maxRects = []
#         for k in range(len(arrangements)):
#             print("正在计算第", k + 1, "/", len(arrangements), "个组件的最佳方案，当前时间为",
#                   time.strftime("%m-%d %H:%M:%S", time.localtime()))
#             # if k == 29:
#             #     break
#             component_length_units = round(arrangements[k].length / UNIT)
#             component_width_units = round(arrangements[k].width / UNIT)
#             # if component_length_units < component_width_units:  # 确保length大于width（不需要额外判断了）
#             #     component_length_units, component_width_units = component_width_units, component_length_units
#             direction, length, width = 1, component_length_units, component_width_units
#             i, nowY = length - 1, -INF
#             if length > self.length or width > self.width:
#                 continue
#             while i < self.length:
#                 j = width - 1
#                 while j < self.width:
#                     if self.canPlaceRectangle(i, j, length, width):
#                         maxCount, nowY, addFlag = updateMaxRects(arrangements[k], i, j, length, width, self.maxRects,
#                                                                  maxCount, nowY, direction)
#                         # 更新光伏板之间的间距（在最后利用maxRects一起更新bool数组和show数组）
#                         if addFlag:
#                             j += width - 2
#                     j += renewJ(i - length + 1, j - width + 1, self.maxRects)  # 快速更新j（非常重要！！！）
#                 i += 1
#
#         print("最佳方案计算完成，耗时", time.time() - time1, "秒，最多可以放置", maxCount, "块光伏板" + "，当前精度为",
#               UNIT, "米\n")
#         return self.maxRects


# 单个组件的排布函数（留着备用！！！）
#     def getBestOption(self, component):
#         time1 = time.time()
#         print("正在计算最佳方案...当前时间为", time.strftime("%m-%d %H:%M:%S", time.localtime()))
#         component_length_units = round(component.length / UNIT)
#         component_width_units = round(component.width / UNIT)
#         if component_length_units < component_width_units:  # 确保length大于width
#             component_length_units, component_width_units = component_width_units, component_length_units
#
#         maxCount = 0
#         self.maxRects = []
#
#         def updateMaxRects1(mY, mX, Len, Wid, maxRects, max_count, now_row, now_y, direct):  # 用于竖排放置方式的更新
#             newRect = Rectangle(mY - Len + 1, mX - Wid + 1, mY, mX, direct, now_row,
#                                 round(PhotovoltaicPanelCrossMargin / UNIT),
#                                 round(PhotovoltaicPanelVerticalMargin / UNIT))
#
#             def overlaps(rect1, rect2):
#                 return not (
#                         rect1.endX + rect1.marginRight < rect2.startX or rect1.endY + rect1.marginBottom <
#                         rect2.startY or rect2.endX + rect2.marginRight < rect1.startX or rect2.endY +
#                         rect2.marginBottom < rect1.startY)
#
#             if not any(overlaps(existing_rect, newRect) for existing_rect in maxRects):
#                 maxRects.append(newRect)
#                 max_count += 1
#                 if now_y != mY and now_y != -INF:
#                     now_row += 1
#                 return max_count, now_row, mY, True
#             else:
#                 return max_count, now_row, now_y, False
#
#         def updateMaxRects2(mY, mX, Len, Wid, maxRects, max_count, now_row, now_y, direct):  # 用于竖排放置方式的更新
#             newRect = Rectangle(mY - Len + 1, mX - Wid + 1, mY, mX, direct, now_row,
#                                 round(PhotovoltaicPanelCrossMargin / UNIT),
#                                 round(PhotovoltaicPanelVerticalMargin / UNIT))
#
#             def overlaps(rect1, rect2):
#                 if rect1.direction != rect2.direction:
#                     return not (
#                             rect1.endX + rect1.marginRight < rect2.startX or rect1.endY + rect1.marginBottom +
#                             round(PhotovoltaicPanelVerticalDiffMargin / UNIT) < rect2.startY or rect2.endX + rect2.
#                             marginRight < rect1.startX or rect2.endY + rect2.marginBottom +
#                             round(PhotovoltaicPanelVerticalDiffMargin / UNIT) < rect1.startY)
#                 else:
#                     return not (
#                             rect1.endX + rect1.marginRight < rect2.startX or rect1.endY + rect1.marginBottom <
#                             rect2.startY or rect2.endX + rect2.marginRight < rect1.startX or rect2.endY +
#                             rect2.marginBottom < rect1.startY)
#
#             if not any(overlaps(existingRect, newRect) for existingRect in maxRects):
#                 maxRects.append(newRect)
#                 max_count += 1
#                 if now_y != mY and now_y != -INF:
#                     now_row += 1
#                 return max_count, now_row, mY, True
#             else:
#                 return max_count, now_row, now_y, False
#
#         def renewJ(y, x, maxRects):
#             for r in maxRects:
#                 if r.startY <= y <= r.endY and r.startX <= x <= r.endX:
#                     return r.endX - x + 1
#             return 1
#
#         # 先检查竖排放置方式
#         addFlag = False
#         direction, length, width = 1, component_length_units, component_width_units
#         i, nowRow, nowY = length - 1, 1, -INF
#         while i < self.length:
#             j = width - 1
#             while j < self.width:
#                 if self.canPlaceRectangle(i, j, length, width):
#                     maxCount, nowRow, nowY, addFlag = updateMaxRects1(i, j, length, width, self.maxRects, maxCount,
#                                                                       nowRow, nowY, direction)
#                     # 更新光伏板之间的间距（在最后利用maxRects一起更新bool数组和show数组）
#                     if addFlag:
#                         j += width - 2 + round(PhotovoltaicPanelCrossMargin / UNIT)
#                 j += renewJ(i - length + 1, j - width + 1, self.maxRects)  # 快速更新j（非常重要！！！）
#             if not addFlag:
#                 i += 1
#             else:
#                 i += round(PhotovoltaicPanelVerticalMargin / UNIT) + 1
#                 addFlag = False
#         # 再检查横排放置方式（只能放一行）
#         addFlag = False
#         direction, length, width = 2, component_width_units, component_length_units
#         i, nowRow, nowY = length - 1, 1, -INF
#         while i < self.length:
#             j = width - 1
#             while j < self.width:
#                 if self.canPlaceRectangle(i, j, length, width):
#                     maxCount, nowRow, nowY, addFlag = updateMaxRects2(i, j, length, width, self.maxRects, maxCount,
#                                                                       nowRow, nowY, direction)
#                     if nowRow == 2:  # 只能放一行横排
#                         break
#                     # 更新光伏板之间的间距（在最后利用maxRects一起更新bool数组和show数组）
#                     if addFlag:
#                         j += width - 2 + round(PhotovoltaicPanelCrossMargin / UNIT)
#                 j += renewJ(i - length + 1, j - width + 1, self.maxRects)
#             if nowRow == 2:  # 只能放一行横排
#                 break
#             if not addFlag:
#                 i += 1
#             else:
#                 i += round(PhotovoltaicPanelVerticalMargin / UNIT) + 1
#                 addFlag = False
#
#         print("最佳方案计算完成，耗时", time.time() - time1, "秒，最多可以放置", maxCount,
#               "块光伏板" + "，光伏组件规格为", component.specification, "，当前精度为", UNIT, "米\n")
#         return self.maxRects
