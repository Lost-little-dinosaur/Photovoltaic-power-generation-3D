import multiprocessing
from PIL import Image
import numpy as np
import time
import matplotlib.pyplot as plt
from const.const import *
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
            self.obstacleArraySelf = []
        else:
            pass  # todo: 复杂屋顶的情况暂时不做处理
        self.roofAngle = jsonRoof["roofAngle"]
        self.roofDirection = jsonRoof["roofDirection"]
        self.latitude = latitude
        self.obstacles = []
        self.sceneObstacles = []
        # self.maxRects = []
        self.allPlacements = []
        # self.type = 0

    def calculateObstacleSelf(self):
        return_list = [[0] * (self.length + 1) for _ in range(self.width + 1)]
        for obstacle in self.obstacles:  # 有问题
            if obstacle.type == '有烟烟囱':
                x_min = 0
                x_max = 0
                y_min = 0
                y_max = 0
                x_min = max(0, obstacle.upLeftPosition[0] - int(round(100 / UNIT)))
                x_max = min(self.width, obstacle.upLeftPosition[0] + obstacle.width + int(round(100 / UNIT)))
                y_min = max(0, obstacle.upLeftPosition[1] - int(round(100 / UNIT)))
                y_max = min(self.length, obstacle.upLeftPosition[1] + obstacle.length + int(round(100 / UNIT)))
                for x in range(x_min, x_max):
                    for y in range(y_min, y_max):
                        return_list[x][y] = 1
        return return_list

    def addObstaclesConcern(self, obstacles, screenedArrangements):
        time1 = time.time()
        print("开始分析阴影并选出最佳方案，当前时间为", time.strftime('%m-%d %H:%M:%S', time.localtime()))
        nowMaxValue = -INF
        # placement中的元素意义为：[[放置的arrangement的ID和startXY],当前value,扣除前的obstacleArray,[扣除的光伏板下标(从左到右从上到下,长度和placement[0]一样),立柱排布]
        for placement in self.allPlacements:
            # if placement[0][0]['ID'] == 396 and placement[0][1]['ID'] == 321:
            #     print("debug")
            if placement[1] < nowMaxValue:
                continue
            for obstacle in obstacles:
                self.obstacles.append(Obstacle(obstacle, placement[2], self.roofArray, self.latitude))
            tempObstacleSumArray = np.cumsum(np.cumsum(placement[2], axis=0), axis=1)
            allDeletedIndices = []
            for arrange in placement[0]:
                arrangeStartX, arrangeStartY = arrange['start']
                screenedArrangements[arrange['ID']].calculateComponentPositionArray(arrangeStartX, arrangeStartY)
                tempArray = screenedArrangements[arrange['ID']].componentPositionArray
                deletedIndices = []
                for i in range(len(tempArray)):  # 判断每个光伏板是否有被遮挡（i是[[startX,startY],[endX,endY]]，是绝对于整个roof的位置）
                    # 用前缀和数组简单判断是否有遮挡，再用高度判断是否有遮挡
                    totalComponent = tempObstacleSumArray[tempArray[i][1][1], tempArray[i][0][0]]
                    if tempArray[i][0][0] > 0:
                        totalComponent -= tempObstacleSumArray[tempArray[i][1][1], tempArray[i][0][0] - 1]
                    if tempArray[i][0][1] > 0:
                        totalComponent -= tempObstacleSumArray[tempArray[i][0][1] - 1, tempArray[i][1][0]]
                    if tempArray[i][0][0] > 0 and tempArray[i][0][1] > 0:
                        totalComponent += tempObstacleSumArray[tempArray[i][0][1] - 1, tempArray[i][0][0] - 1]
                    if totalComponent == 0 or (placement[2][tempArray[i][0][1]:tempArray[i][1][1] + 1, tempArray[i][0][
                        0]:tempArray[i][1][0] + 1] <= screenedArrangements[arrange['ID']].componentHeightArray[
                                                      tempArray[i][0][1] - arrangeStartY:tempArray[i][1][
                                                                                             1] - arrangeStartY + 1,
                                                      tempArray[i][0][0] - arrangeStartX:tempArray[i][1][
                                                                                             0] - arrangeStartX + 1]).all():
                        continue
                    else:  # 有遮挡
                        deletedIndices.append(i)
                # screenedArrangements[arrange['ID']].componentPositionArray = []  # 清空componentPositionArray
                placement[1] -= len(deletedIndices) * screenedArrangements[arrange['ID']].component.power
                allDeletedIndices.append(deletedIndices)
            placement.append(allDeletedIndices)
            if placement[1] > nowMaxValue:
                nowMaxValue = placement[1]
                print(f"当前最大value为{nowMaxValue}，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}")
        i = 0
        while i < len(self.allPlacements):
            if self.allPlacements[i][1] < nowMaxValue:
                del self.allPlacements[i]
            else:
                i += 1
        print(
            f"分析阴影并选出最佳方案完成，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}，耗时{time.time() - time1}秒，共有{len(self.allPlacements)}个较优排布方案\n")

    # 多进程开始
    def search(self, ID, arrange, startX, startY, currentValue, placements, obstacleArray, screenedArrangements):
        for y in range(startY, self.length):
            for x in range(startX, self.width):
                if not self.overlaps(x, y, arrange, placements, screenedArrangements) and \
                        self.canPlaceArrangement(x, y, arrange, obstacleArray):
                    newPlacement = {'ID': ID, 'start': (x, y)}
                    placements.append(newPlacement)
                    currentValue += arrange.value
                    tempObstacleArray = np.array(obstacleArray)
                    arrange.calculateArrangementShadow(x, y, self.latitude, tempObstacleArray)
                    return [placements.copy(), currentValue, np.array(tempObstacleArray), x, y]
            startX = 0

    def canPlaceArrangement(self, x, y, arrange, obstacleArray):
        tempObstacleSumArray = np.cumsum(np.cumsum(obstacleArray, axis=0), axis=1)
        for eachRect in arrange.relativePositionArray:
            startX, startY = eachRect[0]
            endX, endY = eachRect[1]
            absoluteEndX, absoluteEndY = x + endX, y + endY
            if self.width > absoluteEndX and self.length > absoluteEndY:
                totalRoof = self.roofSumArray[absoluteEndY][absoluteEndX]
                totalObstacles = tempObstacleSumArray[absoluteEndY][absoluteEndX]
                if startX > 0:
                    totalRoof -= self.roofSumArray[absoluteEndY][x + startX - 1]
                    totalObstacles -= tempObstacleSumArray[absoluteEndY][x + startX - 1]
                if startY > 0:
                    totalRoof -= self.roofSumArray[y + startY - 1][absoluteEndX]
                    totalObstacles -= tempObstacleSumArray[y + startY - 1][absoluteEndX]
                if startX > 0 and startY > 0:
                    totalRoof += self.roofSumArray[y + startY - 1][x + startX - 1]
                    totalObstacles += tempObstacleSumArray[y + startY - 1][x + startX - 1]
                if totalRoof >= INF:
                    return False
            else:
                return False
            # 接下去检查是否被光伏板的阴影遮挡
            if totalObstacles > 0 and not (obstacleArray[y:y + endY - startY + 1, x:x + endX - startX + 1] <
                                           arrange.componentHeightArray[startY:endY + 1, startX:endX + 1]).all():
                return False
        return True

    def overlaps(self, x, y, arrange, placements, screenedArrangements):
        for eachRect in arrange.relativePositionArray:
            for placement in placements:
                startX, startY = placement['start']
                for eachPlacementRect in screenedArrangements[placement['ID']].relativePositionArray:
                    if not (x + eachRect[0][0] > startX + eachPlacementRect[1][0] or
                            x + eachRect[1][0] < startX + eachPlacementRect[0][0] or
                            y + eachRect[0][1] > startY + eachPlacementRect[1][1] or
                            y + eachRect[1][1] < startY + eachPlacementRect[0][1]):
                        return True
        return False

    def getValidOptions(self, screenedArrangements):
        time1 = time.time()
        print("开始计算排布方案，当前时间为", time.strftime('%m-%d %H:%M:%S', time.localtime()))
        # 输入限制条件
        maxArrangeCount = 2  # 最大阵列个数
        minComponent = 1  # 阵列中的最小组件数

        j = 0
        while j < len(list(screenedArrangements.keys())):
            if list(screenedArrangements.values())[j].value / list(screenedArrangements.values())[
                j].component.power < minComponent:
                del screenedArrangements[list(screenedArrangements.keys())[j]]
            else:
                j += 1
        screenedArrangements = dict(sorted(screenedArrangements.items(), key=lambda x: x[1].value, reverse=True))

        # 分割数据为多个子集，以便多进程处理
        def chunk_it(seq, num):
            avg, out, last = len(seq) / float(num), [], 0.0
            while last < len(seq):
                out.append(seq[int(last):int(last + avg)])
                last += avg
            return out

        arrangeArray = list(screenedArrangements.items())
        eachLayerPlacements = []
        diffLayerPlacements = []
        cpuCount = multiprocessing.cpu_count()
        chunks = chunk_it(range(len(arrangeArray)), cpuCount)
        with multiprocessing.Pool(processes=cpuCount) as pool:
            result = pool.map(computeMission, [(self, chunk, arrangeArray, screenedArrangements) for chunk in chunks])
            for r in result:
                for rr in r:
                    eachLayerPlacements.append(rr)
        diffLayerPlacements.append(eachLayerPlacements)

        for k in range(maxArrangeCount - 1):
            eachLayerPlacements = []
            for ii in diffLayerPlacements[k]:
                chunks = chunk_it(range(ii[1], len(arrangeArray)), cpuCount)
                with multiprocessing.Pool(processes=cpuCount) as pool:
                    result = pool.map(computeMission,
                                      [(self, chunk, arrangeArray, screenedArrangements) for chunk in chunks])
                    for r in result:
                        for rr in r:
                            eachLayerPlacements.append(rr)
            diffLayerPlacements.append(eachLayerPlacements)

        for eachLayerPlacements in diffLayerPlacements:
            for eachPlacement in eachLayerPlacements:
                self.allPlacements.append([eachPlacement[0][0], eachPlacement[0][1], eachPlacement[0][2]])
        print(
            f"排布方案计算完成，共有{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}，耗时{time.time() - time1}秒\n")

    # 多进程结束

    # def getValidOptions(self, screenedArrangements):
    #     time1 = time.time()
    #     print("开始计算排布方案，当前时间为", time.strftime('%m-%d %H:%M:%S', time.localtime()))
    #     # 输入限制条件
    #     maxArrangeCount = 2  # 最大组件个数
    #     minComponent = 1  # 最小组件数
    #
    #     def dfs(arrangeDict, startX, startY, startI, currentValue, placements, layer, obstacleArray):
    #         betterFlag = False
    #         IDArray = list(arrangeDict.keys())
    #         for y in range(startY, self.length):
    #             for x in range(startX, self.width):
    #                 for i in range(startI, len(list(arrangeDict))):
    #                     if canPlaceArrangement(x, y, arrangeDict[IDArray[i]], obstacleArray) and \
    #                             not overlaps(x, y, arrangeDict[IDArray[i]], placements):
    #                         newPlacement = {'ID': IDArray[i], 'start': (x, y)}
    #                         placements.append(newPlacement)
    #                         currentValue += arrangeDict[IDArray[i]].value
    #                         tempObstacleArray = np.array(obstacleArray)
    #                         arrangeDict[IDArray[i]].calculateArrangementShadow(x, y, self.latitude, tempObstacleArray)
    #                         if layer < maxArrangeCount:
    #                             temp = dfs(arrangeDict, x + arrangeDict[IDArray[i]].relativePositionArray[0][1][0], y,
    #                                        i, currentValue + arrangeDict[IDArray[i]].value, placements, layer + 1,
    #                                        np.array(tempObstacleArray))
    #                             if temp:  # 上面的dfs找到了更好的方案，则说明当前方案不是最好的
    #                                 betterFlag = True
    #                             else:  # 上面的dfs没有找到更好的方案，说明当前方案是最好的，将当前方案加入到allPlacements中
    #                                 self.allPlacements.append(
    #                                     [placements.copy(), currentValue, np.array(tempObstacleArray)])
    #                                 if len(self.allPlacements) % 1000 == 0:
    #                                     print(
    #                                         f"已经计算了{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}")
    #                             placements.pop()
    #                             currentValue -= arrangeDict[IDArray[i]].value
    #                         else:
    #                             self.allPlacements.append(
    #                                 [placements.copy(), currentValue, np.array(tempObstacleArray)])
    #                             if len(self.allPlacements) % 1000 == 0:
    #                                 print(
    #                                     f"已经计算了{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}")
    #             startX = 0
    #         return betterFlag
    #
    #     def canPlaceArrangement(x, y, arrange, obstacleArray):
    #         tempObstacleSumArray = np.cumsum(np.cumsum(obstacleArray, axis=0), axis=1)
    #         for eachRect in arrange.relativePositionArray:
    #             startX, startY = eachRect[0]
    #             endX, endY = eachRect[1]
    #             absoluteEndX, absoluteEndY = x + endX, y + endY
    #             if self.width > absoluteEndX and self.length > absoluteEndY:
    #                 totalRoof = self.roofSumArray[absoluteEndY][absoluteEndX]
    #                 totalObstacles = tempObstacleSumArray[absoluteEndY][absoluteEndX]
    #                 if startX > 0:
    #                     totalRoof -= self.roofSumArray[absoluteEndY][x + startX - 1]
    #                     totalObstacles -= tempObstacleSumArray[absoluteEndY][x + startX - 1]
    #                 if startY > 0:
    #                     totalRoof -= self.roofSumArray[y + startY - 1][absoluteEndX]
    #                     totalObstacles -= tempObstacleSumArray[y + startY - 1][absoluteEndX]
    #                 if startX > 0 and startY > 0:
    #                     totalRoof += self.roofSumArray[y + startY - 1][x + startX - 1]
    #                     totalObstacles += tempObstacleSumArray[y + startY - 1][x + startX - 1]
    #                 if totalRoof >= INF:
    #                     return False
    #             else:
    #                 return False
    #             # 接下去检查是否被光伏板的阴影遮挡
    #             if totalObstacles > 0 and not (obstacleArray[y:y + endY - startY + 1, x:x + endX - startX + 1] <
    #                                            arrange.componentHeightArray[startY:endY + 1, startX:endX + 1]).all():
    #                 return False
    #         return True
    #
    #     def overlaps(x, y, arrange, placements):
    #         for eachRect in arrange.relativePositionArray:
    #             for placement in placements:
    #                 startX, startY = placement['start']
    #                 for eachPlacementRect in screenedArrangements[placement['ID']].relativePositionArray:
    #                     if not (x + eachRect[0][0] > startX + eachPlacementRect[1][0] or
    #                             x + eachRect[1][0] < startX + eachPlacementRect[0][0] or
    #                             y + eachRect[0][1] > startY + eachPlacementRect[1][1] or
    #                             y + eachRect[1][1] < startY + eachPlacementRect[0][1]):
    #                         return True
    #         return False
    #
    #     j = 0
    #     while j < len(list(screenedArrangements.keys())):
    #         if list(screenedArrangements.values())[j].value / list(screenedArrangements.values())[
    #             j].component.power < minComponent:
    #             del screenedArrangements[list(screenedArrangements.keys())[j]]
    #         else:
    #             j += 1
    #     tempArray = sorted(screenedArrangements.items(), key=lambda x: x[1].value, reverse=True)
    #     screenedArrangements = dict(tempArray)
    #     # screenedArrangements = [screenedArrangements[0], screenedArrangements[-1]]
    #     dfs(screenedArrangements, 0, 0, 0, 0, [], 1, np.array(self.obstacleArray))
    #     print(
    #         f"排布方案计算完成，共有{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}，耗时{time.time() - time1}秒\n")

    def addSceneObstacles(self, obstacles):  # todo: 有可能没用
        for obstacle in obstacles:
            self.sceneObstacles.append(Obstacle(obstacle, self.obstacleArray, self.roofArray, self.latitude))
        self.obstacleSumArray = np.cumsum(np.cumsum(self.obstacleArray, axis=0), axis=1)

    def calculate_column(self, screenedArrangements):
        nowMaxValue = -INF
        for placement in self.allPlacements:
            allArrangement = placement[0]
            allTempArray = []
            for arrange in allArrangement:
                startX, startY = arrange['start']
                screenedArrangements[arrange['ID']].calculateComponentPositionArray(startX, startY)
                tempArray = screenedArrangements[arrange['ID']].calculateStandColumn(startX, startY, self.width,
                                                                                     self.obstacleArraySelf)
                if len(tempArray) > nowMaxValue:
                    nowMaxValue = len(tempArray)
                allTempArray.append(tempArray)
            placement.append(allTempArray)
        i = 0
        while i < len(self.allPlacements):
            if self.allPlacements[i][1] < nowMaxValue:
                del self.allPlacements[i]
            else:
                i += 1
        print(
            f"立柱排布计算完成，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}，共有{len(self.allPlacements)}个较优排布方案\n")
        return 0

    def drawPlacement(self, screenedArrangements):  # todo: numpy优化
        # 初始化一个全白色的三通道矩阵，用于支持彩色（RGB）
        allMatrix = []
        magnification = 5  # 放大倍数
        # placement中的元素意义为：[[放置的arrangement的ID和startXY],当前value,扣除前的obstacleArray,[扣除的光伏板下标(从左到右从上到下,长度和placement[0]一样),立柱排布]
        for placement in self.allPlacements:
            matrix = np.zeros((self.length * magnification, self.width * magnification, 3))

            # 首先填充上下边界
            matrix[:roofBoardLength, :, :] = RoofMarginColor  # 上边界
            matrix[-roofBoardLength:, :, :] = RoofMarginColor  # 下边界
            # 然后填充左右边界
            matrix[:, :roofBoardLength, :] = RoofMarginColor  # 左边界
            matrix[:, -roofBoardLength:, :] = RoofMarginColor  # 右边界
            for j in range(len(placement[0])):  # j表示第几个arrangement
                arrange = placement[0][j]
                start_x, start_y = arrange['start']
                screenedArrangements[arrange['ID']].calculateComponentPositionArray(start_x, start_y)
                for i in range(len(screenedArrangements[arrange['ID']].componentPositionArray)):  # todo: 为什么要扣除？
                    if i in placement[3][j]:  # 如果这个光伏板被删了，就不画了
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
                for column in placement[4][j]:  # column形式：[centerX,centerY]
                    matrix[
                    column[1] * magnification - standColumnPadding:column[1] * magnification + standColumnPadding + 1,
                    column[0] * magnification - standColumnPadding:
                    column[0] * magnification + standColumnPadding + 1] = StandColumnColor

            # 绘制图像
            plt.imshow(matrix.astype("uint8"))
            plt.axis('off')
            plt.tight_layout()
            # plt.show()

            # 获取当前的Figure对象
            fig = plt.gcf()

            # 获取绘图数据
            fig.canvas.draw()
            # 将绘图数据保存为PIL Image对象
            image = Image.frombytes('RGB', fig.canvas.get_width_height(), fig.canvas.tostring_rgb())
            # 将PIL Image对象转换为长x宽x3的矩阵变量
            image_array = np.array(image)
            # allMatrix.append(matrix)
            allMatrix.append(image_array)
        return allMatrix


# # 多进程开始
def computeMission(params):
    self, ss, arrangeArray, screenedArrangements = params
    eachLayerPlacements = []
    for s in ss:
        tempArray = self.search(arrangeArray[s][0], arrangeArray[s][1], 0, 0, 0, [], self.obstacleArray,
                                screenedArrangements)
        if tempArray is not None:
            eachLayerPlacements.append([tempArray, s])
    return eachLayerPlacements
# 多进程结束

# 尝试多进程并行：
#     def getValidOptions(self, screenedArrangements):
#         time1 = time.time()
#         print("开始计算排布方案，当前时间为", time.strftime('%m-%d %H:%M:%S', time.localtime()))
#         # 输入限制条件
#         maxArrangeCount = 2  # 最大阵列个数
#         minComponent = 1  # 阵列中的最小组件数
#
#         def dfs(arrangeArray, startX, startY, currentValue, placements, layer, obstacleArray):
#             betterFlag = False
#             for y in range(startY, self.length):
#                 for x in range(startX, self.width):
#                     arrange = arrangeArray[layer - 1][1]
#                     if not overlaps(x, y, arrange, placements) and canPlaceArrangement(x, y, arrange, obstacleArray) :
#                         newPlacement = {'ID': arrangeArray[layer - 1][0], 'start': (x, y)}
#                         placements.append(newPlacement)
#                         currentValue += arrange.value
#                         tempObstacleArray = np.array(obstacleArray)
#                         arrange.calculateArrangementShadow(x, y, self.latitude, tempObstacleArray)
#                         if layer < maxArrangeCount:
#                             temp = dfs(arrangeArray, x + arrange.relativePositionArray[0][1][0], y,
#                                        currentValue + arrange.value, placements, layer + 1,
#                                        np.array(tempObstacleArray))
#                             if temp:  # 上面的dfs找到了更好的方案，则说明当前方案不是最好的
#                                 betterFlag = True
#                             else:  # 上面的dfs没有找到更好的方案，说明当前方案是最好的，将当前方案加入到allPlacements中
#                                 self.allPlacements.append(
#                                     [placements.copy(), currentValue, np.array(tempObstacleArray)])
#
#                                 # if len(self.allPlacements) % 1000 == 0:
#                                 #     print(
#                                 #         f"已经计算了{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}")
#                             placements.pop()
#                             currentValue -= arrange.value
#                         else:
#                             self.allPlacements.append(
#                                 [placements.copy(), currentValue, np.array(tempObstacleArray)])
#                             # if len(self.allPlacements) % 1000 == 0:
#                             #     print(
#                             #         f"已经计算了{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}")
#                 startX = 0
#             return betterFlag
#
#         def canPlaceArrangement(x, y, arrange, obstacleArray):
#             tempObstacleSumArray = np.cumsum(np.cumsum(obstacleArray, axis=0), axis=1)
#             for eachRect in arrange.relativePositionArray:
#                 startX, startY = eachRect[0]
#                 endX, endY = eachRect[1]
#                 absoluteEndX, absoluteEndY = x + endX, y + endY
#                 if self.width > absoluteEndX and self.length > absoluteEndY:
#                     totalRoof = self.roofSumArray[absoluteEndY][absoluteEndX]
#                     totalObstacles = tempObstacleSumArray[absoluteEndY][absoluteEndX]
#                     if startX > 0:
#                         totalRoof -= self.roofSumArray[absoluteEndY][x + startX - 1]
#                         totalObstacles -= tempObstacleSumArray[absoluteEndY][x + startX - 1]
#                     if startY > 0:
#                         totalRoof -= self.roofSumArray[y + startY - 1][absoluteEndX]
#                         totalObstacles -= tempObstacleSumArray[y + startY - 1][absoluteEndX]
#                     if startX > 0 and startY > 0:
#                         totalRoof += self.roofSumArray[y + startY - 1][x + startX - 1]
#                         totalObstacles += tempObstacleSumArray[y + startY - 1][x + startX - 1]
#                     if totalRoof >= INF:
#                         return False
#                 else:
#                     return False
#                 # 接下去检查是否被光伏板的阴影遮挡
#                 if totalObstacles > 0 and not (obstacleArray[y:y + endY - startY + 1, x:x + endX - startX + 1] <
#                                                arrange.componentHeightArray[startY:endY + 1, startX:endX + 1]).all():
#                     return False
#             return True
#
#         def overlaps(x, y, arrange, placements):
#             for eachRect in arrange.relativePositionArray:
#                 for placement in placements:
#                     startX, startY = placement['start']
#                     for eachPlacementRect in screenedArrangements[placement['ID']].relativePositionArray:
#                         if not (x + eachRect[0][0] > startX + eachPlacementRect[1][0] or
#                                 x + eachRect[1][0] < startX + eachPlacementRect[0][0] or
#                                 y + eachRect[0][1] > startY + eachPlacementRect[1][1] or
#                                 y + eachRect[1][1] < startY + eachPlacementRect[0][1]):
#                             return True
#             return False
#
#         j = 0
#         while j < len(list(screenedArrangements.keys())):
#             if list(screenedArrangements.values())[j].value / list(screenedArrangements.values())[
#                 j].component.power < minComponent:
#                 del screenedArrangements[list(screenedArrangements.keys())[j]]
#             else:
#                 j += 1
#         screenedArrangements = dict(sorted(screenedArrangements.items(), key=lambda x: x[1].value, reverse=True))
#         multipleMissionArray = []
#         tempArray = list(screenedArrangements.keys())
#
#         def generatePermutation(startI, arr, targetArr):
#             for i in range(startI, len(arr)):
#                 targetArr.append(arr[i])
#                 if len(targetArr) < maxArrangeCount:
#                     generatePermutation(i, arr, targetArr)
#                     targetArr.pop()
#                 else:
#                     multipleMissionArray.append(targetArr.copy())  # todo: 可能可以用np.array()优化？
#                     targetArr.pop()
#
#         generatePermutation(0, tempArray, [])
#         print(len(multipleMissionArray))
#
#         for mission in multipleMissionArray:
#             dfs([[key, screenedArrangements[key]] for key in mission], 0, 0, 0, [], 1, self.obstacleArray)
#             if multipleMissionArray.index(mission) == 37:
#                 print("debug")
#             print(
#                 f"已经完成{multipleMissionArray.index(mission) + 1}/{len(multipleMissionArray)}个排布方案的计算，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}")
#         print(
#             f"排布方案计算完成，共有{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}，耗时{time.time() - time1}秒\n")


# 第一版可用dfs：
#     def getValidOptions(self, screenedArrangements):
#         time1 = time.time()
#         print("开始计算排布方案，当前时间为", time.strftime('%m-%d %H:%M:%S', time.localtime()))
#         # 输入限制条件
#         maxArrangeCount = 1  # 最大组件个数
#         minComponent = 1  # 最小组件数
#
#         def dfs(arrangeDict, startX, startY, startI, currentValue, placements, layer, obstacleArray):
#             betterFlag = False
#             IDArray = list(arrangeDict.keys())
#             for y in range(startY, self.length):
#                 for x in range(startX, self.width):
#                     for i in range(startI, len(list(arrangeDict))):
#                         if canPlaceArrangement(x, y, arrangeDict[IDArray[i]], obstacleArray) and \
#                                 not overlaps(x, y, arrangeDict[IDArray[i]], placements):
#                             newPlacement = {'ID': IDArray[i], 'start': (x, y)}
#                             placements.append(newPlacement)
#                             currentValue += arrangeDict[IDArray[i]].value
#                             tempObstacleArray = np.array(obstacleArray)
#                             arrangeDict[IDArray[i]].calculateArrangementShadow(x, y, self.latitude, tempObstacleArray)
#                             if layer < maxArrangeCount:
#                                 temp = dfs(arrangeDict, x + arrangeDict[IDArray[i]].relativePositionArray[0][1][0], y,
#                                            i, currentValue + arrangeDict[IDArray[i]].value, placements, layer + 1,
#                                            np.array(tempObstacleArray))
#                                 if temp:  # 上面的dfs找到了更好的方案，则说明当前方案不是最好的
#                                     betterFlag = True
#                                 else:  # 上面的dfs没有找到更好的方案，说明当前方案是最好的，将当前方案加入到allPlacements中
#                                     self.allPlacements.append(
#                                         [placements.copy(), currentValue, np.array(tempObstacleArray)])
#
#                                     if len(self.allPlacements) % 1000 == 0:
#                                         print(
#                                             f"已经计算了{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}")
#                                 placements.pop()
#                                 currentValue -= arrangeDict[IDArray[i]].value
#                             else:
#                                 self.allPlacements.append(
#                                     [placements.copy(), currentValue, np.array(tempObstacleArray)])
#                                 if len(self.allPlacements) % 1000 == 0:
#                                     print(
#                                         f"已经计算了{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}")
#                 startX = 0
#             return betterFlag
#
#         def canPlaceArrangement(x, y, arrange, obstacleArray):
#             tempObstacleSumArray = np.cumsum(np.cumsum(obstacleArray, axis=0), axis=1)
#             for eachRect in arrange.relativePositionArray:
#                 startX, startY = eachRect[0]
#                 endX, endY = eachRect[1]
#                 absoluteEndX, absoluteEndY = x + endX, y + endY
#                 if self.width > absoluteEndX and self.length > absoluteEndY:
#                     totalRoof = self.roofSumArray[absoluteEndY][absoluteEndX]
#                     totalObstacles = tempObstacleSumArray[absoluteEndY][absoluteEndX]
#                     if startX > 0:
#                         totalRoof -= self.roofSumArray[absoluteEndY][x + startX - 1]
#                         totalObstacles -= tempObstacleSumArray[absoluteEndY][x + startX - 1]
#                     if startY > 0:
#                         totalRoof -= self.roofSumArray[y + startY - 1][absoluteEndX]
#                         totalObstacles -= tempObstacleSumArray[y + startY - 1][absoluteEndX]
#                     if startX > 0 and startY > 0:
#                         totalRoof += self.roofSumArray[y + startY - 1][x + startX - 1]
#                         totalObstacles += tempObstacleSumArray[y + startY - 1][x + startX - 1]
#                     if totalRoof >= INF:
#                         return False
#                 else:
#                     return False
#                 # 接下去检查是否被光伏板的阴影遮挡
#                 if totalObstacles > 0 and not (obstacleArray[y:y + endY - startY + 1, x:x + endX - startX + 1] <
#                                                arrange.componentHeightArray[startY:endY + 1, startX:endX + 1]).all():
#                     return False
#             return True
#
#         def overlaps(x, y, arrange, placements):
#             for eachRect in arrange.relativePositionArray:
#                 for placement in placements:
#                     startX, startY = placement['start']
#                     for eachPlacementRect in screenedArrangements[placement['ID']].relativePositionArray:
#                         if not (x + eachRect[0][0] > startX + eachPlacementRect[1][0] or
#                                 x + eachRect[1][0] < startX + eachPlacementRect[0][0] or
#                                 y + eachRect[0][1] > startY + eachPlacementRect[1][1] or
#                                 y + eachRect[1][1] < startY + eachPlacementRect[0][1]):
#                             return True
#             return False
#
#         j = 0
#         while j < len(list(screenedArrangements.keys())):
#             if list(screenedArrangements.values())[j].value / list(screenedArrangements.values())[
#                 j].component.power < minComponent:
#                 del screenedArrangements[list(screenedArrangements.keys())[j]]
#             else:
#                 j += 1
#         tempArray = sorted(screenedArrangements.items(), key=lambda x: x[1].value, reverse=True)
#         screenedArrangements = dict(tempArray)
#         # screenedArrangements = [screenedArrangements[0], screenedArrangements[-1]]
#         dfs(screenedArrangements, 0, 0, 0, 0, [], 0, np.array(self.obstacleArray))
#         print(
#             f"排布方案计算完成，共有{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}，耗时{time.time() - time1}秒\n")