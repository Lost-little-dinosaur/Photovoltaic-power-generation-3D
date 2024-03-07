import numpy as np

import const.const
from classes.component import Component, getAllComponents

from const.const import *
from math import radians, sin
from tools.tools3D import calculateShadow
import time

ID = 0


class Arrangement:

    def __init__(self, componentLayoutArray, crossPosition, component, arrangeType, maxWindPressure, isRule):
        for c in getAllComponents():
            if component == c.specification:
                self.component = c  # 使用组件的类型
                break
        else:
            raise Exception("组件'{}'不存在".format(component))
        self.componentLayoutArray = componentLayoutArray  # 是未扣除光伏板的arrangement
        # relativePositionArray是arrangement中尽可能多的组成矩形的光伏板的startXY
        tempStart, tempEnd, self.relativePositionArray, nowBottom = 0, 0, [], 0
        # 计算组件的相对位置，以[[[x1, y1], [x2, y2]], [[x1, y1], [x2, y2]]]的形式存储（只支持只有一排横排组件的情况）
        if crossPosition == INF:  # 没有横排
            while tempEnd < len(componentLayoutArray):
                while tempEnd < len(componentLayoutArray) and componentLayoutArray[tempEnd] == componentLayoutArray[
                    tempStart]:
                    tempEnd += 1
                self.relativePositionArray.append([[0, nowBottom], [
                    self.component.width * componentLayoutArray[tempStart] + (
                            componentLayoutArray[tempStart] - 1) * PhotovoltaicPanelCrossMargin - 1, nowBottom +
                    self.component.length * (tempEnd - tempStart) + (
                            tempEnd - tempStart - 1) * PhotovoltaicPanelVerticalMargin - 1]])
                nowBottom = self.relativePositionArray[-1][1][1] + 1
                tempStart = tempEnd
        elif crossPosition == 0:  # 只有横排
            self.relativePositionArray = [[[0, 0], [self.component.length * componentLayoutArray[0] + (
                    componentLayoutArray[0] - 1) * PhotovoltaicPanelCrossMargin - 1,
                                                    nowBottom + self.component.width - 1]]]
        else:
            while tempEnd < crossPosition:
                while tempEnd < crossPosition and componentLayoutArray[tempEnd] == componentLayoutArray[tempStart]:
                    tempEnd += 1
                self.relativePositionArray.append(
                    [[0, nowBottom], [self.component.width * componentLayoutArray[tempStart] + (
                            componentLayoutArray[tempStart] - 1) * PhotovoltaicPanelCrossMargin - 1, nowBottom +
                                      self.component.length * (tempEnd - tempStart) + (
                                              tempEnd - tempStart - 1) * PhotovoltaicPanelVerticalMargin - 1]])
                nowBottom = self.relativePositionArray[-1][1][1] + 1
                tempStart = tempEnd
            self.relativePositionArray[-1][1][1] += PhotovoltaicPanelVerticalDiffMargin
            nowBottom = self.relativePositionArray[-1][1][1] + 1
            if crossPosition == len(componentLayoutArray) - 2:  # 横排在倒数第二个
                self.relativePositionArray.append([[0, nowBottom], [self.component.length * componentLayoutArray[
                    crossPosition] + (componentLayoutArray[crossPosition] - 1) * PhotovoltaicPanelCrossMargin - 1,
                                                                    nowBottom + self.component.width - 1]])
                self.relativePositionArray.append([[0, self.relativePositionArray[-1][1][1] + 1], [
                    self.component.width * componentLayoutArray[-1] + (componentLayoutArray[-1] - 1)
                    * PhotovoltaicPanelCrossMargin - 1, self.relativePositionArray[-1][1][1] + self.component.length]])
            elif crossPosition == 1:  # 横排在最后
                self.relativePositionArray.append([[0, nowBottom], [self.component.length * componentLayoutArray[
                    crossPosition] + (componentLayoutArray[crossPosition] - 1) * PhotovoltaicPanelCrossMargin - 1,
                                                                    nowBottom + self.component.width + PhotovoltaicPanelVerticalDiffMargin - 1]])
            # else:  # 横排在中间
            #     raise Exception("横排在中间的情况还没有写")
        self.componentPositionArray = []  # 组合排布中组件的详细信息
        self.arrangeType = arrangeType  # 排布的类型：基墩，膨胀常规，膨胀抬高
        self.maxWindPressure = maxWindPressure  # 风压
        self.value = self.component.power * sum(componentLayoutArray)
        self.crossPosition = crossPosition  # 横排组件的位置
        self.isRule = isRule  # 是否是规则排布
        self.startX = 0  # 排布左上角坐标x
        self.startY = 0  # 排布左上角坐标y
        self.crossNum = 0
        self.crossCount = 0
        self.verticalCount = 0
        self.verticalNum = 0
        self.componentHeightArray = np.array(self.calculateComponentHeightArray())  # 每个光伏板具体高度（大小是这个arrangement的最小包络矩形）

        self.maxLength, self.maxWidth = -INF, -INF
        # zzp: 将 self.relativePositionArray 转换为 NumPy 数组，但效率没有提高，后面面对大数据可能才有用
        # self.relativePositionArray = np.array(self.relativePositionArray)

        # 找到最大宽度和最大长度
        # self.maxWidth = np.max(self.relativePositionArray[:, 1, 0])
        # self.maxLength = np.max(self.relativePositionArray[:, 1, 1])
        self.maxLength, self.maxWidth = -INF, -INF
        for tempElement in self.relativePositionArray:
            if tempElement[1][0] >= self.maxWidth:
                self.maxWidth = tempElement[1][0]
            if tempElement[1][1] >= self.maxLength:
                self.maxLength = tempElement[1][1]
        self.shadowArray = np.zeros((self.maxWidth + 1, self.maxLength + 1))  # 阴影数组

        self.columnArray_y = []  # 立柱南北间距
        self.columnArray_x = []  # 立柱东西间距
        self.edgeColumn = []  # 边缘立柱
        self.shadowRelativePosition = []

    def calculateStandColumn(self, startXunit, startYunit, roof_Width, obstacles, deletedIndices):
        UNIT = const.const.getUnit()
        column, limit_column, arrangement_height = const.const.getColumnsInformation()
        startX = startXunit * UNIT
        startY = startYunit * UNIT

        def generate_columns(n_columns, startY, startX, roof_width, width, length, max_spacing, array_iny, obstacles):
            column_positions = []
            self.columnArray_x = []
            ideal_spacing_min = int((width - 1400) / (n_columns - 1)) + 1  # 计算最小理想间距
            if ideal_spacing_min > max_spacing:
                return []
            ideal_spacing_max = int((width - 500) / (n_columns - 1))  # 计算最大理想间距
            ideal_spacing = min(max_spacing, ideal_spacing_max)
            column_positions.append(int((width - ideal_spacing * (n_columns - 1)) / 2))
            for i in range(1, n_columns):
                x = int(i * ideal_spacing + column_positions[0])
                column_positions.append(x)
                # todo 50整数修正需要修改
            #    precision = 50
            #    for i in range(len(column_positions)):
            #        if ((column_positions[i] % precision) != 0):
            #            column_positions[i] = int(column_positions[i] / precision) * precision
            # 调整立柱距离边缘的距离
            # min_edge_distance = round(250 / UNIT)
            # if column_positions[0] + startX < min_edge_distance:
            #     column_positions[0] = min_edge_distance
            # if column_positions[-1] + startX > roof_width - min_edge_distance:
            #     column_positions[-1] = roof_width - min_edge_distance - startX
            #     # 添加第一排立柱和最后一排立柱与边缘的间距限制
            # if column_positions[0] >= round(700 / UNIT):
            #     column_positions[0] = round(700 / UNIT)
            # if column_positions[-1] <= round(width - 700 / UNIT):
            #     column_positions[-1] = round(width - (700 / UNIT))
            self.columnArray_x.append(column_positions[0])
            for i in range(len(column_positions) - 1):
                self.columnArray_x.append(column_positions[i + 1] - column_positions[i])
            self.columnArray_x.append(width - column_positions[-1])
            result = []
            self.edgeColumn = []
            for x in column_positions:
                for y in array_iny:
                    if 0 <= x < width and 0 <= y< length:
                        if obstacles[x + startX][y + startY] != 1:
                            result.append([startX + x, startY + y])
                    if x == column_positions[0] or x == column_positions[-1]:
                        if y == array_iny[0] or y == array_iny[-1]:
                            self.edgeColumn.append([startX + x, startY + y])
            return result

        str_ar = self.component.specification + self.arrangeType
        if len(self.relativePositionArray) == 1 and self.crossPosition == INF:  # 规则且只包含竖排
            array_y = column[(str_ar, len(self.componentLayoutArray), 0, 0, 0, 0)].copy()
            array_limit = limit_column[(str_ar, len(self.componentLayoutArray), 0, 0, 0, 0)]
            # h_min = arrangement_height[("182-78膨胀常规", 2, 1, 0)]
        elif len(self.relativePositionArray) == 1 and self.crossPosition == 0:
            array_y = column[(str_ar, 0, 1, 0, 0, 0)].copy()
            array_limit = limit_column[(str_ar, 0, 1, 0, 0, 0)]
        else:
            if self.crossPosition == INF:  # 只有竖排
                first_element = self.componentLayoutArray[0]
                count = 0
                for num in self.componentLayoutArray:
                    if num == first_element:
                        count += 1
                if self.componentLayoutArray[0] < self.componentLayoutArray[-1]:  # 从上面扣除
                    array_y = column[(str_ar, len(self.componentLayoutArray), 0, count, 0, 0)].copy()
                    array_limit = limit_column[(str_ar, len(self.componentLayoutArray), 0, count, 0, 0)]
                else:
                    array_y = column[(str_ar, len(self.componentLayoutArray), 0, 0, 0, count)].copy()  # 从下面扣除
                    array_limit = limit_column[(str_ar, len(self.componentLayoutArray), 0, 0, 0, count)]

            elif len(self.componentLayoutArray) == 2 and (
                    self.componentLayoutArray[0] != self.componentLayoutArray[1]):  # 竖一横一
                array_y = column[(str_ar, 1, 1, 0, 0, 0)].copy()
                array_limit = limit_column[(str_ar, 1, 1, 0, 0, 0)]
            else:
                # 有竖有横且不规则
                normal_vertical = max(self.componentLayoutArray[0], self.componentLayoutArray[-1])  # 正常的一排列数
                normal_cross = int((normal_vertical * self.component.width + (normal_vertical - 1) *
                                    PhotovoltaicPanelCrossMargin) / self.component.length)
                count1 = 0
                count2 = 0
                count3 = 0
                for i in range(len(self.componentLayoutArray) - 2):
                    if self.componentLayoutArray[i] < normal_vertical:
                        count1 += 1
                if self.componentLayoutArray[-2] < normal_cross:
                    count2 = 1
                if self.componentLayoutArray[-1] < normal_vertical:
                    count3 = 1
                array_y = column[(str_ar, len(self.componentLayoutArray) - 1, 1, count1, count2, count3)].copy()
                array_limit = limit_column[(str_ar, len(self.componentLayoutArray) - 1, 1, count1, count2, count3)]
        self.calculateComponentPositionArrayreal(startX, startY)
        length = 0
        # for component in self.componentPositionArray:  # todo 更新
        #    if component[1][1] > length:
        #        length = component[1][1]
        length = self.componentPositionArray[-1][1][1] - self.componentPositionArray[0][0][1]
        length += 1
        le = length - sum(array_y) - array_limit[0]
        if (le + array_limit[0]) / 2 < array_limit[0]:
            array_y.append(int(array_limit[0]) + array_y[-1])
            array_y.insert(0, int(le - array_limit[0]))
        else:
            if (le + array_limit[0]) / 2 > array_limit[1]:
                array_y.append(int(array_limit[1]))
                array_y.insert(0, int(le - array_limit[1]))
            else:
                array_y.append(int((le + array_limit[0]) / 2))
                array_y.insert(0, int((le + array_limit[0]) / 2))
        self.columnArray_y = array_y
        result_y = []
        prefix_sum = 0
        for i in range(len(array_y) - 1, -1, -1):
            prefix_sum += array_y[i]
            result_y.append(prefix_sum - 1)

            '''       
            array_x = [250]
            for i in range(int((self.width - 500) / 700)):
                array_x.append(array_x[-1] + 700)
            if (self.width - array_x[-1]) < 250:
                array_x.pop()
            '''
        result_y.pop()
        max_spacing = 2000
        width = 0
        for component in self.componentPositionArray:
            if component[1][0] > width:
                width = component[1][0]
        width += 1
        width = width - self.componentPositionArray[0][0][0]
        column_min = int(width / max_spacing) + 1
        column_min = max(2, column_min)
        column_max = 1000
        for column_n in range(column_min, column_max):
            result = generate_columns(column_n, startY, startX, roof_Width, width, length, max_spacing, result_y,
                                      obstacles)
            if len(result) == 0:
                continue
            else:
                final_list = []
                for node in result:
                    flag = 0
                    for component in self.componentPositionArray:
                        if (component[0][0] <= node[0] <= component[1][0]
                                and component[0][1] <= node[1] <= component[1][1]):
                            flag = 1
                    for i in deletedIndices:
                        component = self.componentPositionArray[i]
                        if (component[0][0] <= node[0] <= component[1][0]
                                and component[0][1] <= node[1] <= component[1][1]):
                            flag = 0
                    if flag == 1:
                        final_list.append(node)
                txt = "边缘四个立柱的坐标为："
                for node in self.edgeColumn:
                    txt += str(node) + "、"
                txt = txt[:-1] + "\n"
                txt += "南北立柱间距为："
                for node in self.columnArray_y:
                    txt += str(node) + "、"
                txt = txt[:-1] + "\n"
                txt += "东西立柱间距为："
                for node in self.columnArray_x:
                    txt += str(node) + "、"
                return final_list, txt[:-1] + "\n"
        return [], ""

    def calculateComponentPositionArray(self, startX, startY):
        # 通过输入的startX, startY和Arrangement本就有的信息计算出组件的排布坐标，添加到self.componentArray里
        self.componentPositionArray = []
        if self.crossPosition == 0:  # 只有横排布（横一）
            self.crossNum = self.componentLayoutArray[0]
            self.crossCount = 1
            self.verticalCount = 0
            self.verticalNum = 0
            for i in range(self.crossNum):
                self.componentPositionArray.append([[startX, startY], [startX + self.component.length - 1,
                                                                       startY + self.component.width - 1]])
                startX += self.component.length + PhotovoltaicPanelCrossMargin  # 横横间隙
        elif self.crossPosition == INF:  # 只有竖排
            self.crossNum = 0
            self.crossCount = 0
            self.verticalCount = len(self.componentLayoutArray)
            self.verticalNum = self.componentLayoutArray[0]
            for i in range(self.verticalCount):
                for j in range(self.verticalNum):
                    self.componentPositionArray.append([[startX, startY], [startX + self.component.width - 1,
                                                                           startY + self.component.length - 1]])
                    startX += self.component.width + PhotovoltaicPanelCrossMargin
                startX -= (self.component.width + PhotovoltaicPanelCrossMargin) * self.verticalNum
                startY += self.component.length + PhotovoltaicPanelVerticalMargin
        elif len(self.componentLayoutArray) == 2 and (
                self.componentLayoutArray[0] != self.componentLayoutArray[1]):  # 竖一横一
            temp = startX
            self.crossNum = self.componentLayoutArray[1]
            self.crossCount = 1
            self.verticalCount = 1
            self.verticalNum = self.componentLayoutArray[0]
            for i in range(self.verticalNum):
                self.componentPositionArray.append([[startX, startY], [startX + self.component.width - 1,
                                                                       startY + self.component.length - 1]])
                startX += self.component.width + PhotovoltaicPanelCrossMargin
            startX = temp
            startY = startY + self.component.length + PhotovoltaicPanelVerticalDiffMargin
            for i in range(self.crossNum):
                self.componentPositionArray.append([[startX, startY], [startX + self.component.length - 1,
                                                                       startY + self.component.width - 1]])
                startX += self.component.length + PhotovoltaicPanelCrossMargin
        else:  # 其他横竖情况
            self.crossCount = 1
            self.crossNum = self.componentLayoutArray[-2]
            self.verticalCount = len(self.componentLayoutArray) - 1
            self.verticalNum = self.componentLayoutArray[0]
            for i in range(self.verticalCount - 1):
                for j in range(self.componentLayoutArray[i]):
                    self.componentPositionArray.append(
                        [[startX, startY], [startX + self.component.width - 1, startY + self.component.length - 1]])
                    startX += (self.component.width + PhotovoltaicPanelCrossMargin)
                startX -= (self.component.width + PhotovoltaicPanelCrossMargin) * self.componentLayoutArray[i]
                startY += (self.component.length + PhotovoltaicPanelVerticalMargin)
            startY += (self.component.width + PhotovoltaicPanelVerticalDiffMargin * 2 - PhotovoltaicPanelVerticalMargin)
            temp_X = startX
            temp = []
            for i in range(self.componentLayoutArray[-1]):  # 最后一排
                # self.componentPositionArray.append(
                #    [[startX, startY], [startX + self.component.width - 1, startY + self.component.length - 1]])
                temp.append([startX, startY])
                startX += (self.component.width + PhotovoltaicPanelCrossMargin)
            startX = temp_X
            startY -= (self.component.width + PhotovoltaicPanelVerticalDiffMargin)

            for i in range(self.componentLayoutArray[-2]):
                self.componentPositionArray.append(
                    [[startX, startY], [startX + self.component.length - 1, startY + self.component.width - 1]])
                startX += self.component.length + PhotovoltaicPanelCrossMargin
            for node_c in temp:
                self.componentPositionArray.append(
                    [[node_c[0], node_c[1]], [node_c[0] + self.component.width - 1,
                                              node_c[1] + self.component.length - 1]])

    def calculateComponentPositionArrayreal(self, startX, startY):
        # 通过输入的startX, startY和Arrangement本就有的信息计算出组件的排布坐标，添加到self.componentArray里
        self.componentPositionArray = []
        if self.crossPosition == 0:  # 只有横排布（横一）
            self.crossNum = self.componentLayoutArray[0]
            self.crossCount = 1
            self.verticalCount = 0
            self.verticalNum = 0
            for i in range(self.crossNum):
                self.componentPositionArray.append([[startX, startY], [startX + self.component.realLength - 1,
                                                                       startY + self.component.realWidth - 1]])
                startX += self.component.realLength + PhotovoltaicPanelCrossMargin  # 横横间隙
        elif self.crossPosition == INF:  # 只有竖排
            self.crossNum = 0
            self.crossCount = 0
            self.verticalCount = len(self.componentLayoutArray)
            self.verticalNum = self.componentLayoutArray[0]
            for i in range(self.verticalCount):
                for j in range(self.verticalNum):
                    self.componentPositionArray.append([[startX, startY], [startX + self.component.realWidth - 1,
                                                                           startY + self.component.realLength - 1]])
                    startX += self.component.realWidth + PhotovoltaicPanelCrossMargin
                startX -= (self.component.realWidth + PhotovoltaicPanelCrossMargin) * self.verticalNum
                startY += self.component.realLength + PhotovoltaicPanelVerticalMargin
        elif len(self.componentLayoutArray) == 2 and (
                self.componentLayoutArray[0] != self.componentLayoutArray[1]):  # 竖一横一
            temp = startX
            self.crossNum = self.componentLayoutArray[1]
            self.crossCount = 1
            self.verticalCount = 1
            self.verticalNum = self.componentLayoutArray[0]
            for i in range(self.verticalNum):
                self.componentPositionArray.append([[startX, startY], [startX + self.component.realWidth - 1,
                                                                       startY + self.component.realLength - 1]])
                startX += self.component.realWidth + PhotovoltaicPanelCrossMargin
            startX = temp
            startY = startY + self.component.realLength + PhotovoltaicPanelVerticalDiffMargin
            for i in range(self.crossNum):
                self.componentPositionArray.append([[startX, startY], [startX + self.component.realLength - 1,
                                                                       startY + self.component.realWidth - 1]])
                startX += self.component.realLength + PhotovoltaicPanelCrossMargin
        else:  # 其他横竖情况
            self.crossCount = 1
            self.crossNum = self.componentLayoutArray[-2]
            self.verticalCount = len(self.componentLayoutArray) - 1
            self.verticalNum = self.componentLayoutArray[0]
            for i in range(self.verticalCount - 1):
                for j in range(self.componentLayoutArray[i]):
                    self.componentPositionArray.append(
                        [[startX, startY],
                         [startX + self.component.realWidth - 1, startY + self.component.realLength - 1]])
                    startX += (self.component.realWidth + PhotovoltaicPanelCrossMargin)
                startX -= (self.component.realWidth + PhotovoltaicPanelCrossMargin) * self.componentLayoutArray[i]
                startY += (self.component.realLength + PhotovoltaicPanelVerticalMargin)
            startY += (
                    self.component.realWidth + PhotovoltaicPanelVerticalDiffMargin * 2 - PhotovoltaicPanelVerticalMargin)
            temp_X = startX
            temp = []
            for i in range(self.componentLayoutArray[-1]):  # 最后一排
                # self.componentPositionArray.append(
                #    [[startX, startY], [startX + self.component.width - 1, startY + self.component.length - 1]])
                temp.append([startX, startY])
                startX += (self.component.realWidth + PhotovoltaicPanelCrossMargin)
            startX = temp_X
            startY -= (self.component.realWidth + PhotovoltaicPanelVerticalDiffMargin)

            for i in range(self.componentLayoutArray[-2]):
                self.componentPositionArray.append(
                    [[startX, startY], [startX + self.component.realLength - 1, startY + self.component.realWidth - 1]])
                startX += self.component.realLength + PhotovoltaicPanelCrossMargin
            for node_c in temp:
                self.componentPositionArray.append(
                    [[node_c[0], node_c[1]], [node_c[0] + self.component.realWidth - 1,
                                              node_c[1] + self.component.realLength - 1]])

    # def chooseLayout(self):
    #     if self.specification == "竖二" and self.type == "基墩":
    #         array_x = [107, 1707, 3307]
    #         array_y = [459, 1859, 2706, 4135]
    #
    #     elif self.specification == "竖四横一" and self.type == "基墩":
    #         array_x = [417, 2417, 4417, 6417, 6834]
    #         array_y = [458, 1858, 2725, 4143, 5016, 6428, 6849, 8007, 8465, 9865]
    #     else:
    #         layout = "Default Layout"
    #
    #     return array_x, array_y
    def calculateArrangementShadow(self, latitude, obstacleArray=None):
        if obstacleArray is None:
            obstacleArray = []
        componentStr = self.component.specification + self.arrangeType

        if len(self.relativePositionArray) == 1:
            hMin = arrangementHeight[(componentStr, len(self.componentLayoutArray), 0, 0, 0, 0)]
            # hMin = arrangement_height[("182-78膨胀常规", 2, 1, 0)]
            hMax = hMin + (self.relativePositionArray[0][1][1] - self.relativePositionArray[0][0][1]) * sin(
                radians(20))
            nodeArray = [
                [self.relativePositionArray[0][0][0], self.relativePositionArray[0][0][1], hMax],
                [self.relativePositionArray[0][1][0], self.relativePositionArray[0][0][1], hMax],
                [self.relativePositionArray[0][1][0], self.relativePositionArray[0][1][1], hMin],
                [self.relativePositionArray[0][0][0], self.relativePositionArray[0][1][1], hMin],
            ]
            minX, minY, self.shadowArray = calculateShadow(nodeArray, False, latitude, False)
            self.shadowRelativePosition = [-minX, -minY]
        else:
            if self.crossPosition == INF:  # 只有竖排
                first_element = self.componentLayoutArray[0]
                count = 0
                for num in self.componentLayoutArray:
                    if num == first_element:
                        count += 1
                if self.componentLayoutArray[0] < self.componentLayoutArray[-1]:
                    hMin = arrangementHeight[(componentStr, len(self.componentLayoutArray), 0, count, 0, 0)]
                else:
                    hMin = arrangementHeight[(componentStr, len(self.componentLayoutArray), 0, 0, 0, count)]

            elif len(self.componentLayoutArray) == 2 and (
                    self.componentLayoutArray[0] != self.componentLayoutArray[1]):  # 竖一横一
                hMin = arrangementHeight[(componentStr, 1, 1, 0, 0, 0)]
            else:
                normal_vertical = max(self.componentLayoutArray[0], self.componentLayoutArray[-1])  # 正常的一排列数
                normal_cross = int((normal_vertical * self.component.width + (normal_vertical - 1) *
                                    PhotovoltaicPanelCrossMargin) / self.component.length)
                count1 = 0
                count2 = 0
                count3 = 0
                for i in range(len(self.componentLayoutArray) - 2):
                    if self.componentLayoutArray[i] < normal_vertical:
                        count1 += 1
                if self.componentLayoutArray[-2] < normal_cross:
                    count2 = 1
                if self.componentLayoutArray[-1] < normal_vertical:
                    count3 = 1
                hMin = arrangementHeight[(componentStr, len(self.componentLayoutArray) - 1, 1, count1, count2, count3)]
            for node in self.relativePositionArray:
                hMax = hMin + (node[1][1] - node[0][1]) * sin(radians(20))
                nodeArray = [
                    [node[0][0], node[0][1], hMax],
                    [node[1][0], node[0][1], hMax],
                    [node[1][0], node[1][1], hMin],
                    [node[0][0], node[1][1], hMin],
                ]
                minX, minY, self.shadowArray = calculateShadow(nodeArray, False, latitude, False)
                self.shadowRelativePosition = [-minX, -minY]

    def calculateComponentHeightArray(self):
        length = self.relativePositionArray[-1][1][1] - self.relativePositionArray[0][0][0] + 1
        width = 0
        for node in self.relativePositionArray:
            if width < node[1][0]:
                width = node[1][0]
        componentStr = self.component.specification + self.arrangeType
        if len(self.relativePositionArray) == 1:
            hMin = arrangementHeight[(componentStr, len(self.componentLayoutArray), 0, 0, 0, 0)]
            # hMin = arrangement_height[("182-78膨胀常规", 2, 1, 0)]
        else:
            if self.crossPosition == INF:  # 只有竖排
                first_element = self.componentLayoutArray[0]
                count = self.componentLayoutArray.count(first_element)
                # for num in self.componentLayoutArray:
                #     if num == first_element:
                #         count += 1
                if self.componentLayoutArray[0] < self.componentLayoutArray[-1]:
                    hMin = arrangementHeight[(componentStr, len(self.componentLayoutArray), 0, count, 0, 0)]
                else:
                    hMin = arrangementHeight[(componentStr, len(self.componentLayoutArray), 0, 0, 0, count)]
            elif len(self.componentLayoutArray) == 2 and (
                    self.componentLayoutArray[0] != self.componentLayoutArray[1]):  # 竖一横一
                hMin = arrangementHeight[(componentStr, 1, 1, 0, 0, 0)]
            else:
                normal_vertical = max(self.componentLayoutArray[0], self.componentLayoutArray[-1])  # 正常的一排列数
                normal_cross = int((normal_vertical * self.component.width + (normal_vertical - 1) *
                                    PhotovoltaicPanelCrossMargin) / self.component.length)
                # count1 = 0
                # count2 = 0
                # count3 = 0
                # for i in range(len(self.componentLayoutArray) - 2):
                #     if self.componentLayoutArray[i] < normal_vertical:
                #         count1 += 1
                # if self.componentLayoutArray[-2] < normal_cross:
                #     count2 = 1
                # if self.componentLayoutArray[-1] < normal_vertical:
                #     count3 = 1
                count1 = sum(1 for i in range(len(self.componentLayoutArray) - 2) if self.componentLayoutArray[i] < normal_vertical)
                count2 = 1 if self.componentLayoutArray[-2] < normal_cross else 0
                count3 = 1 if self.componentLayoutArray[-1] < normal_vertical else 0
                hMin = arrangementHeight[(componentStr, len(self.componentLayoutArray) - 1, 1, count1, count2, count3)]
        hMax = hMin + length * sin(radians(20))
        temp = (hMax - hMin) / length
        # return_list = [[0] * (width + 1) for _ in range(length + 1)]
        # for node in self.relativePositionArray:
        #     max_x = node[1][0]
        #     min_x = node[0][0]
        #     max_y = node[1][1]
        #     min_y = node[0][1]

        #     for y in range(min_y, max_y + 1):
        #         for x in range(min_x, max_x + 1):
        #             return_list[y][x] = hMin + temp * (length - y)
        
        # 换numpy
        return_list = np.zeros((length + 1, width + 1))
        for node in self.relativePositionArray:
            max_x = node[1][0]
            min_x = node[0][0]
            max_y = node[1][1]
            min_y = node[0][1]

            y_range = range(min_y, max_y + 1)
            x_range = range(min_x, max_x + 1)
            return_list[np.ix_(y_range, x_range)] = hMin + temp * (length - np.array(y_range)[:, np.newaxis])
        return return_list


def calculateVerticalWidth(verticalNum, componentWidth):
    return verticalNum * componentWidth + (verticalNum - 1) * PhotovoltaicPanelCrossMargin


def calculateCrossWidth(crossNum, componentLength):
    return crossNum * componentLength + (crossNum - 1) * PhotovoltaicPanelCrossMargin


def screenArrangements(roofWidth, roofLength, componentSpecification, arrangeType, windPressure):
    tempArrangements = [[1, 0, "182-78", "膨胀常规", "高压"], [1, 1, "182-78", "膨胀常规", "高压"],
                        [2, 0, "182-78", "膨胀常规", "高压"], [2, 1, "182-78", "膨胀常规", "高压"],
                        [3, 0, "182-78", "膨胀常规", "高压"], [3, 1, "182-78", "膨胀常规", "高压"],
                        [4, 0, "182-78", "膨胀常规", "高压"], [4, 1, "182-78", "膨胀常规", "高压"],
                        [5, 0, "182-78", "膨胀常规", "高压"],

                        # [1, 0, "210-60", "膨胀常规", "低压"], [1, 1, "210-60", "膨胀常规", "低压"],
                        # [0, 1, "210-60", "膨胀常规", "低压"], [2, 0, "210-60", "膨胀常规", "低压"],
                        # [2, 1, "210-60", "膨胀常规", "低压"], [3, 0, "210-60", "膨胀常规", "低压"],
                        # [3, 1, "210-60", "膨胀常规", "低压"], [4, 0, "210-60", "膨胀常规", "低压"],
                        # [4, 1, "210-60", "膨胀常规", "低压"], [5, 0, "210-60", "膨胀常规", "低压"],

                        # [0, 1, "210-60", "基墩", "低压"], [2, 0, "210-60", "基墩", "低压"],
                        # [3, 0, "210-60", "基墩", "低压"], [4, 0, "210-60", "基墩", "低压"],
                        # [1, 0, "210-60", "基墩", "低压"],

                        # [2, 0, "210-60", "膨胀抬高", "低压"], [2, 1, "210-60", "膨胀抬高", "低压"],
                        # [3, 0, "210-60", "膨胀抬高", "低压"], [3, 1, "210-60", "膨胀抬高", "低压"],
                        # [4, 0, "210-60", "膨胀抬高", "低压"], [4, 1, "210-60", "膨胀抬高", "低压"],
                        # [5, 0, "210-60", "膨胀抬高", "低压"],

                        # [0, 1, "182-72", "基墩", "低压"], [2, 0, "182-72", "基墩", "低压"],
                        # [3, 0, "182-72", "基墩", "低压"], [4, 0, "182-72", "基墩", "低压"],
                        # [1, 0, "182-72", "基墩", "低压"],

                        # [1, 0, "182-72", "膨胀常规", "低压"], [1, 1, "182-72", "膨胀常规", "低压"],
                        # [0, 1, "182-72", "膨胀常规", "低压"], [2, 0, "182-72", "膨胀常规", "低压"],
                        # [2, 1, "182-72", "膨胀常规", "低压"], [3, 0, "182-72", "膨胀常规", "低压"],
                        # [3, 1, "182-72", "膨胀常规", "低压"], [4, 0, "182-72", "膨胀常规", "低压"],
                        # [4, 1, "182-72", "膨胀常规", "低压"], [5, 0, "182-72", "膨胀常规", "低压"],

                        # [2, 0, "182-72", "膨胀抬高", "低压"], [2, 1, "182-72", "膨胀抬高", "低压"],
                        # [3, 0, "182-72", "膨胀抬高", "低压"], [3, 1, "182-72", "膨胀抬高", "低压"],
                        # [4, 0, "182-72", "膨胀抬高", "低压"], [4, 1, "182-72", "膨胀抬高", "低压"],
                        # [5, 0, "182-72", "膨胀抬高", "低压"],

                        [1, 0, "182-78", "膨胀常规", "低压"], [1, 1, "182-78", "膨胀常规", "低压"],
                        [0, 1, "182-78", "膨胀常规", "低压"], [2, 0, "182-78", "膨胀常规", "低压"],
                        [2, 1, "182-78", "膨胀常规", "低压"], [3, 0, "182-78", "膨胀常规", "低压"],
                        [3, 1, "182-78", "膨胀常规", "低压"], [4, 0, "182-78", "膨胀常规", "低压"],
                        [4, 1, "182-78", "膨胀常规", "低压"], [5, 0, "182-78", "膨胀常规", "低压"],

                        # [0, 1, "182-78", "基墩", "低压"], [2, 0, "182-78", "基墩", "低压"],
                        # [3, 0, "182-78", "基墩", "低压"], [4, 0, "182-78", "基墩", "低压"],
                        # [1, 0, "182-78", "基墩", "低压"],

                        # [2, 0, "182-78", "膨胀抬高", "低压"], [2, 1, "182-78", "膨胀抬高", "低压"],
                        # [3, 0, "182-78", "膨胀抬高", "低压"], [3, 1, "182-78", "膨胀抬高", "低压"],
                        # [4, 0, "182-78", "膨胀抬高", "低压"], [4, 1, "182-78", "膨胀抬高", "低压"],
                        # [5, 0, "182-78", "膨胀抬高", "低压"]
                        ]

    arrangementDict = {}
    global ID
    for tempElement in tempArrangements:
        if tempElement[1] == 0:  # 只有竖排
            for j in range(2, 31):
                arrangementDict[ID] = Arrangement(tempElement[0] * [j], INF, tempElement[2], tempElement[3],
                                                  tempElement[4], True)
                ID += 1
        elif tempElement[0] == 0:  # 只有横排
            for j in range(1, 16):
                arrangementDict[ID] = Arrangement(tempElement[1] * [j], 0, tempElement[2], tempElement[3],
                                                  tempElement[4], True)
                ID += 1
        else:  # 横竖都有
            minVerticalNum = 2
            for c in getAllComponents():
                if c.specification == tempElement[2]:
                    tempComponent = c
                    break
            else:
                raise Exception("组件'{}'不存在".format(tempElement[2]))
            while calculateVerticalWidth(minVerticalNum, tempComponent.width) < tempComponent.length:
                minVerticalNum += 1
            if tempElement[0] != 1:  # 说明竖排不止一行，横排在倒数第二行
                for j in range(minVerticalNum, 31):
                    maxCrossNum = 0
                    while calculateVerticalWidth(j, tempComponent.width) >= calculateCrossWidth(maxCrossNum,
                                                                                                tempComponent.length):
                        maxCrossNum += 1
                    maxCrossNum -= 1
                    tempArr = (tempElement[0] - 1) * [j] + tempElement[1] * [maxCrossNum] + [j]
                    arrangementDict[ID] = Arrangement(tempArr, tempElement[0] - 1, tempElement[2], tempElement[3],
                                                      tempElement[4], True)
                    ID += 1
            else:  # 说明竖排只有一行，横排在最后一行
                for j in range(minVerticalNum, 31):
                    maxCrossNum = 0
                    while calculateVerticalWidth(j, tempComponent.width) >= calculateCrossWidth(maxCrossNum,
                                                                                                tempComponent.length):
                        maxCrossNum += 1
                    maxCrossNum -= 1
                    tempArr = tempElement[0] * [j] + tempElement[1] * [maxCrossNum]
                    arrangementDict[ID] = Arrangement(tempArr, 1, tempElement[2], tempElement[3], tempElement[4], True)
                    ID += 1

    # 通过输入的屋顶宽度、屋顶长度、组件类型、排布类型和风压，筛选出合适的排布
    result = {}
    for k, arrangement in arrangementDict.items():
        if arrangement.component.specification == componentSpecification and arrangement.arrangeType[0:2] == \
                arrangeType[0:2] and arrangement.maxWindPressure == windPressure:
            for tempElement in arrangement.relativePositionArray:
                if tempElement[1][0] >= roofWidth or tempElement[1][1] >= roofLength:
                    break
            else:
                result[k] = arrangement
    return result


# 组件排布的规格
# component1 = Component("182-72", 1.134, 2.279, 535, 550, 0.30, 0.35)  # 以米、瓦为单位
# component2 = Component("182-78", 1.134, 2.465, 580, 600, 0.30, 0.35)  # 以米、瓦为单位
# component3 = Component("210-60", 1.303, 2.172, 595, 605, 0.33, 0.35)  # 以米、瓦为单位
# component4 = Component("210-66", 1.303, 2.384, 650, 665, 0.33, 0.35)  # 以米、瓦为单位
# components = [component1, component2, component3, component4]

# verticalCount, crossCount, verticalNum, crossNum, component, arrangeType, maxWindPressure

# 分布判断
# if arrangement.width <= roofWidth and arrangement.length <= roofLength:
#     if arrangement.component.specification == componentSpecification:
#         if arrangement.arrangeType == arrangeType:
#             if arrangement.maxWindPressure + 0.00001 >= windPressure:
#                 result.append(arrangement)
#             else:
#                 print("风压不符合，要求风压为", windPressure, "实际风压为", arrangement.maxWindPressure)
#         else:
#             print("排布类型不符合，要求排布类型为", arrangeType, "实际排布类型为", arrangement.arrangeType)
#     else:
#         print("组件类型不符合，要求组件类型为", componentSpecification, "实际组件类型为",
#               arrangement.component.specification)
# else:
#     print("排布尺寸不符合，要求排布尺寸为", roofWidth, roofLength, "实际排布尺寸为", arrangement.width,
#           arrangement.length)

# 去重
# tempArrangements.sort(key=lambda x: (x.verticalCount, x.verticalNum, x.crossCount, x.crossNum), reverse=True)
# arrangements = [tempArrangements[0]]
# for i in range(1, len(tempArrangements)):
#     if arrangements[-1].verticalCount == tempArrangements[i].verticalCount and arrangements[-1].verticalNum == \
#             tempArrangements[i].verticalNum and arrangements[-1].crossCount == tempArrangements[i].crossCount and \
#             arrangements[-1].crossNum == tempArrangements[i].crossNum and arrangements[-1].component.specification == \
#             tempArrangements[i].component.specification and arrangements[-1].arrangeType == tempArrangements[
#         i].arrangeType and abs(arrangements[-1].maxWindPressure - tempArrangements[i].maxWindPressure) < 0.00001:
#         print("重复！！！")
#         continue
#     else:
#         arrangements.append(tempArrangements[i])

# i = 0
# while i < len(tempArrangements) - 1:
#     if tempArrangements[i].verticalCount == tempArrangements[i + 1].verticalCount and tempArrangements[
#         i].verticalNum == tempArrangements[i + 1].verticalNum and tempArrangements[i].crossCount == tempArrangements[
#         i + 1].crossCount and tempArrangements[i].crossNum == tempArrangements[i + 1].crossNum:
#         del tempArrangements[i]
#     else:
#         i += 1
# print(len(tempArrangements))
# print(tempArrangements)
def calculate_ar_Shadow(self, startX, startY, latitude, obstacleArray=[]):
    column, limit_column, arrangement_height = const.const.getColumnsInformation()

    str = self.component.specification + self.arrangeType

    if len(self.relativePositionArray) == 1:
        h_min = arrangement_height[(str, self.componentLayoutArray[0], 0, 0, 0, 0)]
        # h_min = arrangement_height[("182-78膨胀常规", 2, 1, 0)]
        h_max = h_min + (self.relativePositionArray[0][1][1] - self.relativePositionArray[0][0][1]) * sin(radians(20))
        nodearray = [
            [self.relativePositionArray[0][0][0] + startX, self.relativePositionArray[0][0][1] + startY, h_max],
            [self.relativePositionArray[0][1][0] + startX, self.relativePositionArray[0][0][1] + startY, h_max],
            [self.relativePositionArray[0][0][0] + startX, self.relativePositionArray[0][1][1] + startY, h_min],
            [self.relativePositionArray[0][1][0] + startX, self.relativePositionArray[0][1][1] + startY, h_min]
        ]
        calculateShadow(nodearray, False, latitude, obstacleArray)
    else:
        if self.crossPosition == INF:  # 只有竖排
            first_element = self.componentLayoutArray[0]
            count = 0
            for num in self.componentLayoutArray:
                if num == first_element:
                    count += 1
            if self.componentLayoutArray[0] < self.componentLayoutArray[-1]:
                h_min = arrangement_height[(str, len(self.componentLayoutArray), 0, count, 0, 0)]
            else:
                h_min = arrangement_height[(str, len(self.componentLayoutArray), 0, 0, 0, count)]

        elif len(self.componentLayoutArray) == 2 and (
                self.componentLayoutArray[0] != self.componentLayoutArray[1]):  # 竖一横一
            h_min = arrangement_height[(str, 1, 1, 0, 0, 0)]
        else:
            normal_vertical = max(self.componentLayoutArray[0], self.componentLayoutArray[-1])  # 正常的一排列数
            normal_cross = round((normal_vertical * self.component.width + (normal_vertical - 1) *
                                  PhotovoltaicPanelCrossMargin) / self.component.length)
            count1 = 0
            count2 = 0
            count3 = 0
            for i in range(len(self.componentLayoutArray) - 2):
                if self.componentLayoutArray[i] < normal_vertical:
                    count1 += 1
            if self.componentLayoutArray[-2] < normal_cross:
                count2 = 1
            if self.componentLayoutArray[-1] < normal_vertical:
                count3 = 1
            h_min = arrangement_height[(str, len(self.componentLayoutArray) - 1, 1, count1, count2, count3)]
        for node in self.relativePositionArray:
            h_max = h_min + (node[1][1] - node[0][1]) * sin(radians(20))
            nodearray = [
                [node[0][0] + startX, node[0][1] + startY, h_max],
                [node[1][0] + startX, node[0][1] + startY, h_max],
                [node[0][0] + startX, node[1][1] + startY, h_min],
                [node[1][0] + startX, node[1][1] + startY, h_min]
            ]
            calculateShadow(nodearray, False, latitude, obstacleArray)


if __name__ == '__main__':
    a = [[[0, 0], [1, 1]], [[2, 2], [3, 3]]]
    for node in a:
        print(node[0])
