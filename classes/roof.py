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
            self.standColumnArray = []
            self.showArray = np.full((self.length, self.width, 4), EmptyColor)
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
        #self.type = 0

    def calculateObstacleSelf(self):
        return_list = [[0] * (self.length + 1) for _ in range(self.width + 1)]
        for obstacle in self.obstacles:  # 有问题
            if obstacle.type == '有烟烟囱':
                for x in range(obstacle.upLeftPosition[0], obstacle.upLeftPosition[0] + obstacle.width):
                    for y in range(obstacle.upLeftPosition[1], obstacle.upLeftPosition[1] + obstacle.length):
                        return_list[x][y] = 1
        return return_list


    def addObstaclesConcern(self, obstacles, screenedArrangements):
        time1 = time.time()
        print("开始分析阴影并选出最佳方案，当前时间为", time.strftime('%m-%d %H:%M:%S', time.localtime()))
        nowMaxValue = -INF
        # placement中的元素意义为：[[放置的arrangement的ID和startXY],当前value,扣除前的obstacleArray,[扣除的光伏板下标(从左到右从上到下,长度和placement[0]一样)],
        for placement in self.allPlacements:
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
                        0]:tempArray[i][1][0] + 1] < screenedArrangements[arrange['ID']].componentHeightArray[
                                                     tempArray[i][0][1] - arrangeStartY:tempArray[i][1][
                                                                                            1] - arrangeStartY + 1,
                                                     tempArray[i][0][0] - arrangeStartX:tempArray[i][1][
                                                                                            0] - arrangeStartX + 1]).all():
                        continue
                    else:  # 有遮挡
                        deletedIndices.append(i)
                screenedArrangements[arrange['ID']].componentPositionArray = []  # 清空componentPositionArray
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

    def addSceneObstacles(self, obstacles):  # todo: 有可能没用
        for obstacle in obstacles:
            self.sceneObstacles.append(Obstacle(obstacle, self.obstacleArray, self.roofArray, self.latitude))
        self.obstacleSumArray = np.cumsum(np.cumsum(self.obstacleArray, axis=0), axis=1)

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

    def getValidOptions(self, screenedArrangements):
        time1 = time.time()
        print("开始计算排布方案，当前时间为", time.strftime('%m-%d %H:%M:%S', time.localtime()))
        # 输入限制条件
        maxLayer = 3  # 最大层数
        minComponent = 5  # 最小组件数

        def dfs(arrangeDict, startX, startY, startI, currentValue, placements, layer, obstacleArray):
            betterFlag = False
            IDArray = list(arrangeDict.keys())
            for y in range(startY, self.length):
                for x in range(startX, self.width):
                    for i in range(startI, len(list(arrangeDict))):
                        if canPlaceArrangement(x, y, arrangeDict[IDArray[i]], obstacleArray) and \
                                not overlaps(x, y, arrangeDict[IDArray[i]], placements):
                            newPlacement = {'ID': IDArray[i], 'start': (x, y)}
                            placements.append(newPlacement)
                            currentValue += arrangeDict[IDArray[i]].value
                            tempObstacleArray = np.array(obstacleArray)
                            arrangeDict[IDArray[i]].calculateArrangementShadow(x, y, self.latitude, tempObstacleArray)
                            if layer < maxLayer:
                                temp = dfs(arrangeDict, x + arrangeDict[IDArray[i]].relativePositionArray[0][1][0], y,
                                           i, currentValue + arrangeDict[IDArray[i]].value, placements, layer + 1,
                                           np.array(tempObstacleArray))
                                if temp:  # 上面的dfs找到了更好的方案，则说明当前方案不是最好的
                                    betterFlag = True
                                else:  # 上面的dfs没有找到更好的方案，说明当前方案是最好的，将当前方案加入到allPlacements中
                                    self.allPlacements.append(
                                        [placements.copy(), currentValue, np.array(tempObstacleArray)])

                                    if len(self.allPlacements) % 1000 == 0:
                                        print(
                                            f"已经计算了{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}")
                                placements.pop()
                                currentValue -= arrangeDict[IDArray[i]].value
                            else:
                                self.allPlacements.append(
                                    [placements.copy(), currentValue, np.array(tempObstacleArray)])
                                if len(self.allPlacements) % 1000 == 0:
                                    print(
                                        f"已经计算了{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}")
                startX = 0
            return betterFlag

        def canPlaceArrangement(x, y, arrange, obstacleArray):
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

        def overlaps(x, y, arrange, placements):
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

        j = 0
        while j < len(list(screenedArrangements.keys())):
            if list(screenedArrangements.values())[j].value / list(screenedArrangements.values())[
                j].component.power < minComponent:
                del screenedArrangements[list(screenedArrangements.keys())[j]]
            else:
                j += 1
        tempArray = sorted(screenedArrangements.items(), key=lambda x: x[1].value, reverse=True)
        screenedArrangements = dict(tempArray)
        # screenedArrangements = [screenedArrangements[0], screenedArrangements[-1]]
        dfs(screenedArrangements, 0, 0, 0, 0, [], 1, np.array(self.obstacleArray))
        print(
            f"排布方案计算完成，共有{len(self.allPlacements)}个排布方案，当前时间为{time.strftime('%m-%d %H:%M:%S', time.localtime())}，耗时{time.time() - time1}秒\n")
        # exit(0)
        return self.allPlacements

    def calculate_column(self, screenedArrangements):
        for node in self.allPlacements:
            startX, startY = node[0][0]['start']
            self.standColumnArray.append(screenedArrangements[node[0][0]['ID']].calculateStandColumn(startX, startY,
                                                                                                     self.length,
                                                                                                     self.width,
                                                                                                     self.obstacleArraySelf))
        return 0


def drawPlacement(data, width, length, borderN=1, borderM=1):
    # 初始化一个全白色的三通道矩阵，用于支持彩色（RGB）

    matrix = np.ones((length, width, 3))

    # 添加大矩阵的红色边界
    # 首先填充上下边界
    matrix[:borderM, :, :] = [1, 0, 0]  # 上边界
    matrix[-borderM:, :, :] = [1, 0, 0]  # 下边界
    # 然后填充左右边界
    matrix[:, :borderM, :] = [1, 0, 0]  # 左边界
    matrix[:, -borderM:, :] = [1, 0, 0]  # 右边界

    for group in data:
        start_x, start_y = group['start']
        for rect in group['relativePositionArray']:  # todo: 到时候再改
            top_left = rect[0]
            bottom_right = rect[1]

            # 绘制黄色边界
            for x in range(max(borderM, start_x + top_left[0] - borderN),
                           min(width - borderM, start_x + bottom_right[0] + borderN + 1)):
                for y in range(max(borderM, start_y + top_left[1] - borderN),
                               min(length - borderM, start_y + bottom_right[1] + borderN + 1)):
                    if (x < start_x + top_left[0] or x > start_x + bottom_right[0] or
                            y < start_y + top_left[1] or y > start_y + bottom_right[1]):
                        matrix[y, x] = [1, 1, 0]  # 黄色

            # 填充矩形内部为黑色
            for x in range(max(borderM, start_x + top_left[0]),
                           min(width - borderM, start_x + bottom_right[0] + 1)):
                for y in range(max(borderM, start_y + top_left[1]),
                               min(length - borderM, start_y + bottom_right[1] + 1)):
                    matrix[y, x] = [0, 0, 0]  # 黑色

    # 绘制图像
    plt.imshow(matrix)
    plt.axis('off')
    plt.show()
