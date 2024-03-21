import sys
from os import getcwd
import numpy as np
from numpy.lib.shape_base import row_stack
from classes.component import Component, getAllComponents
import const.const
from const.const import *
from math import radians, sin
from tools.tools3D import calculateShadow
import time

ID = 0.


def getComponent(component):
    for c in getAllComponents():
        if component == c.specification:
            return c  # 使用组件的类型
    else:
        raise Exception("组件'{}'不存在".format(component))


class Arrangement:
    def __init__(self, componentLayoutArray, crossPosition, component, arrangeType, maxWindPressure, isRule):
        # zzp: 预估不需要的方案，摆的太少了，等下会直接剔除
        self.componentNum = sum(componentLayoutArray)
        if self.componentNum < getMinComponent() or self.componentNum > getMaxComponent():
            self.legal = False
            return
        self.legal = True

        self.component = getComponent(component)
        # for c in getAllComponents():
        #     if component == c.specification:
        #         self.component = c  # 使用组件的类型
        #         break
        # else:
        #     raise Exception("组件'{}'不存在".format(component))
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
        self.value = self.component.power * self.componentNum
        self.crossPosition = crossPosition  # 横排组件的位置
        self.isRule = isRule  # 是否是规则排布
        self.startX = 0  # 排布左上角坐标x
        self.startY = 0  # 排布左上角坐标y
        self.crossNum = 0
        self.crossCount = 0
        self.verticalCount = 0
        self.verticalNum = 0
        self.componentHeightArray = np.array(self.calculateComponentHeightArray(),dtype=np.float32)  # 每个光伏板具体高度（大小是这个arrangement的最小包络矩形）

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
        self.shadowArray = np.zeros((self.maxWidth + 1, self.maxLength + 1), dtype=np.float32)  # 阴影数组

        self.columnArray_y = []  # 立柱南北间距
        self.columnArray_x = []  # 立柱东西间距
        self.edgeColumn = []  # 边缘立柱
        self.shadowRelativePosition = []

    def calculateStandColumn(self, startXunit, startYunit, roof_Width, obstacles, deletedIndices, type, obstaclerange):
        UNIT = const.const.getUnit()
        column, limit_column, arrangement_height = const.const.getColumnsInformation()
        startX = int(startXunit * UNIT)
        startY = int(startYunit * UNIT)
        temp = []
        for node in obstaclerange:
            temp.append([node[0] - startX, node[1] - startX])
        obstaclerange = temp
        sys.setrecursionlimit(10000)
        def dfsColumn_position(x, n_columns, width, answer, obstaclerange, max_spacing, type, k = 0):
            # type == 1表示常规情况，2表示有扣除
            result = []
            if n_columns <= 0 and type == 1:
                if 250 <= (width - x) <= 700:
                    return answer
            if n_columns <= 0 and type == 2:
                if (width - x) <= max_spacing + k:
                    return answer
            num = answer[-1] + max_spacing + k
            k = 0
            while num >= answer[-1] + max_spacing / 2:
                answer.append(num)  # 将当前数加入组合
                found_match = False
                for node in obstaclerange:
                    if node[0] < num < node[1]:
                        found_match = True
                        break
                if not found_match:
                    result = dfsColumn_position(num, n_columns - 1, width, answer, obstaclerange, max_spacing, type, k)  # 递归搜索下一个数
                    if len(result) != 0:  # 如果找到满足条件的答案，立即返回
                        break
                answer.pop()  # 回溯，移除当前数
                num -= 50
                k += 50
                if len(result) != 0:  # 如果找到满足条件的答案，立即返回
                    break
            return result

        def generate_columns(n_columns, startY, startX, roof_width, width, length, max_spacing,
                             array_iny, obstacles, array_left, array_right, leftNum, rightNum, obstaclerange):
            column_positions = []
            self.columnArray_x = []
            ideal_spacing_min = int((width - 1400) / (n_columns - 1)) + 1  # 计算最小理想间距
            if ideal_spacing_min > max_spacing:
                return []
            ideal_spacing_max = int((width - 500) / (n_columns - 1))  # 计算最大理想间距
            ideal_spacing = min(max_spacing, ideal_spacing_max)
            #column_positions.append(int((width - ideal_spacing * (n_columns - 1)) / 2))
            #for i in range(1, n_columns):
            #    x = int(i * ideal_spacing + column_positions[0])
            #    column_positions.append(x)
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
            for num in range(250, 700, 50):

                column_positions.append(num)  # 将当前数加入组合
                found_match = False
                for node in obstaclerange:
                    if node[0] < num < node[1]:
                        found_match = True
                        break
                if not found_match:
                    column_positions = dfsColumn_position(num, n_columns - 1, width, column_positions,
                                                          obstaclerange, ideal_spacing, 1)  # 递归搜索下一个数
                if len(column_positions) == n_columns:
                    break
                column_positions.pop()  # 回溯，移除当前数
                self.columnArray_x.append(column_positions[0])

            for i in range(len(column_positions) - 1):
                self.columnArray_x.append(column_positions[i + 1] - column_positions[i])
            self.columnArray_x.append(width - column_positions[-1])
            result = []
            self.edgeColumn = []
            if leftNum == 0 and rightNum == 0:
                for x in column_positions:
                    for y in array_iny:
                        if 0 <= x < width and 0 <= y < length:
                            if obstacles[x + startX][y + startY] != 1:
                                result.append([startX + x, startY + y])
                        if x == column_positions[0] or x == column_positions[-1]:
                            if y == array_iny[0] or y == array_iny[-1]:
                                self.edgeColumn.append([startX + x, startY + y])
            else:
                for x in column_positions:
                    for y in array_left:
                        if 0 <= x < bound and 0 <= y < length:
                            if obstacles[x + startX][y + startY] != 1:
                                result.append([startX + x, startY + y])
                        if x == column_positions[0]:
                            if y == array_left[0] or y == array_left[-1]:
                                self.edgeColumn.append([startX + x, startY + y])
                for x in column_positions:
                    for y in array_right:
                        if bound <= x < width and 0 <= y < length:
                            if obstacles[x + startX][y + startY] != 1:
                                result.append([startX + x, startY + y])
                        if x == column_positions[-1]:
                            if y == array_right[0] or y == array_right[-1]:
                                self.edgeColumn.append([startX + x, startY + y])
            final_list = []
            for node in result:
                flag = 1
                # 立柱扣除
                #            for component in self.componentPositionArray:
                #                if (component[0][0] <= node[0] <= component[1][0]
                #                        and component[0][1] <= node[1] <= component[1][1]):
                #                    flag = 1
                #            for i in deletedIndices:
                #                component = self.componentPositionArray[i]
                #                if (component[0][0] < node[0] < component[1][0]
                #                        and component[0][1] < node[1] < component[1][1]):
                #                    flag = 0
                if flag == 1:
                    final_list.append(node)
            return final_list
        # 计算array_y
        up = 0
        down = 0
        array_y = []
        array_limit = []
        array_yleft = []
        array_limitleft = []
        array_yright = []
        array_limitright = []
        leftNum = 0
        rightNum = 0  # 处理拼接类型，左边列数和右边列数
        bound = INF
        height = 0
        lengthright = 0
        for node in self.relativePositionArray:
            if node[1][0] < bound:
                bound = node[1][0]
        bound = bound * UNIT
        str_ar = self.component.specification + self.arrangeType
        if len(self.relativePositionArray) == 1 and self.crossPosition == INF:  # 规则且只包含竖排
            array_y = column[(str_ar, len(self.componentLayoutArray), 0, 0, 0, 0)].copy()
            array_limit = limit_column[(str_ar, len(self.componentLayoutArray), 0, 0, 0, 0)]
            # h_min = arrangement_height[("182-78膨胀常规", 2, 1, 0)]
        elif len(self.relativePositionArray) == 1 and self.crossPosition == 0:  # 只有横排
            array_y = column[(str_ar, 0, 1, 0, 0, 0)].copy()
            array_limit = limit_column[(str_ar, 0, 1, 0, 0, 0)]
        else:  # 拼接类型和竖+横
            if self.crossPosition == INF:  # 只有竖排
                if self.componentLayoutArray[0] < self.componentLayoutArray[-1]:  # 从上面扣除
                    first_element = self.componentLayoutArray[0]
                    count = self.componentLayoutArray.count(first_element)
                    leftNum = self.componentLayoutArray[0]
                    rightNum = self.componentLayoutArray[-1] - leftNum
                    array_yleft = column[(str_ar, len(self.componentLayoutArray), 0, count, 0, 0, 0)].copy()
                    array_limitleft = limit_column[(str_ar, len(self.componentLayoutArray), 0, count, 0, 0, 0)]
                    array_yright = column[(str_ar, len(self.componentLayoutArray), 0, count, 0, 0, 1)].copy()
                    array_limitright = limit_column[(str_ar, len(self.componentLayoutArray), 0, count, 0, 0, 1)]
                    up = 1
                    height = self.relativePositionArray[0][1][1] * UNIT + UNIT
                else:
                    last_element = self.componentLayoutArray[-1]
                    count = self.componentLayoutArray.count(last_element)
                    leftNum = self.componentLayoutArray[-1]
                    rightNum = self.componentLayoutArray[0] - leftNum
                    array_yleft = column[(str_ar, len(self.componentLayoutArray), 0, 0, 0, count, 0)].copy()  # 从下面扣除
                    array_limitleft = limit_column[(str_ar, len(self.componentLayoutArray), 0, 0, 0, count, 0)]
                    array_yright = column[(str_ar, len(self.componentLayoutArray), 0, 0, 0, count, 1)].copy()
                    array_limitright = limit_column[(str_ar, len(self.componentLayoutArray), 0, 0, 0, count, 1)]
                    height = self.relativePositionArray[0][1][1] * UNIT + UNIT  # todo 测试一下
                    down = 1
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
                if count1 == 0 and count2 == 0 and count3 == 0:
                    array_y = column[(str_ar, len(self.componentLayoutArray) - 1, 1, count1, count2, count3)].copy()
                    array_limit = limit_column[(str_ar, len(self.componentLayoutArray) - 1, 1, count1, count2, count3)]
                else:
                    leftNum = min(self.componentLayoutArray[0], self.componentLayoutArray[-1])
                    rightNum = normal_vertical - leftNum
                    array_yleft = column[
                        (str_ar, len(self.componentLayoutArray) - 1, 1, count1, count2, count3, 0)].copy()
                    array_limitleft = limit_column[
                        (str_ar, len(self.componentLayoutArray) - 1, 1, count1, count2, count3, 0)]
                    array_yright = column[
                        (str_ar, len(self.componentLayoutArray) - 1, 1, count1, count2, count3, 1)].copy()
                    array_limitright = limit_column[
                        (str_ar, len(self.componentLayoutArray) - 1, 1, count1, count2, count3, 1)]
                    if count3 != 0:
                        if count2 == 0:
                            height = self.relativePositionArray[1][1][1] * UNIT + UNIT  # todo 测试一下
                        else:
                            height = self.relativePositionArray[0][1][1] * UNIT + UNIT
                        down = 1
                    else:
                        up = 1
                        height = self.relativePositionArray[0][1][1] * UNIT
        self.calculateComponentPositionArrayreal(startX, startY)
        result_y = []
        result_yleft = []
        result_yright = []
        if leftNum == 0 and rightNum == 0:  # 非拼接情况
            length = self.componentPositionArray[-1][1][1] - self.componentPositionArray[0][0][1]
            length += 1
            le = length - sum(array_y) - array_limit[0]
            array_y.insert(0, array_limit[0])
            array_y.append(le)
            self.columnArray_y = array_y
            result_y = []
            prefix_sum = 0
            for i in range(len(array_y) - 1, -1, -1):
                prefix_sum += array_y[i]
                result_y.append(prefix_sum - 1)
            result_y.pop()
        else:  # 拼接情况
            length = self.componentPositionArray[-1][1][1] - self.componentPositionArray[0][0][1]
            length += 1
            le = length - sum(array_yleft) - array_limitleft[0]
            array_yleft.insert(0, array_limitleft[0])
            array_yleft.append(le)
            result_yleft = []
            prefix_sum = 0
            for i in range(len(array_yleft) - 1, -1, -1):
                prefix_sum += array_yleft[i]
                result_yleft.append(prefix_sum - 1)
            result_yleft.pop()
            if up == 1:
                lengthright = length - height
            elif down == 1:
                lengthright = height
                height = 0
            le = lengthright - sum(array_yright) - array_limitright[0]
            array_yright.insert(0, array_limitright[0])
            array_yright.append(le)
            result_yright = []
            prefix_sum = 0
            for i in range(len(array_yright) - 1, -1, -1):
                prefix_sum += array_yright[i]
                result_yright.append(prefix_sum)
            result_yright.pop()
            self.columnArray_y = array_yleft + array_yright
            for i in range(len(result_yright)):
                result_yright[i] = result_yright[i] + height
        ##################   计算column_position
        #    deletedEdgecomponent = []
        #    for i in deletedIndices:
        #        if i in self.edgeComponents:
        #            deletedEdgecomponent.append(i)
        max_spacing = 2000
        width = 0
        for component in self.componentPositionArray:
            if component[1][0] > width:
                width = component[1][0]
        width += 1
        width = width - self.componentPositionArray[0][0][0]  # 绝对宽度
        if len(deletedIndices) == 0:  # 没有扣除情况
            column_min = int(width / max_spacing) + 1
            if width - (column_min * max_spacing) < 1400:
                column_min += 1
            column_min = max(2, column_min)
            column_max = 1000
            for column_n in range(column_min, column_max):
                final_list = generate_columns(column_n, startY, startX, roof_Width, width, length, max_spacing,
                                              result_y, obstacles, result_yleft, result_yright,
                                              leftNum, rightNum, obstaclerange)
                if len(final_list) == 0:
                    continue
                else:
                    if type == "正7形":
                        for node in self.edgeColumn:
                            node[0] = roof_Width - node[0]
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
        else:  # 扣除边缘组件产生新的边缘组件的情况
            column_positions = []
            self.columnArray_x = []
            fixedColumn = []  # 确定的立柱位置
            for i in deletedIndices:
                left_x = self.componentPositionArray[i][0][0] - 500 - startX
                right_x = self.componentPositionArray[i][1][0] + 500 - startX
                # 防止越界
                if left_x > 0:
                    fixedColumn.append([left_x, self.componentPositionArray[i][0][1]])
                if right_x < width:
                    fixedColumn.append([right_x, self.componentPositionArray[i][0][1]])
            fixedColumn = sorted(fixedColumn)
            i = 0
            # 去掉不需要限制的位置
            while i < len(fixedColumn):
                for j in deletedIndices:
                    if fixedColumn[i][1] == self.componentPositionArray[j][0][1]:
                        if (fixedColumn[i][0] > (self.componentPositionArray[j][0][0] - startX)) and \
                                (fixedColumn[i][0] < (self.componentPositionArray[j][1][0] - startX)):
                            fixedColumn.pop(i)
                            i = i - 1
                            break
                i = i + 1
            fixedColumn = sorted(fixedColumn)
            # 去重
            i = 0
            while i < len(fixedColumn) - 1:
                diff = abs(fixedColumn[i][0] - fixedColumn[i + 1][0])
                if diff < 400:
                    average = int((fixedColumn[i][0] + fixedColumn[i + 1][0]) / 2)
                    fixedColumn[i][0] = average
                    fixedColumn.pop(i + 1)
                else:
                    i = i + 1
            # 计算得到需要固定的位置fixedColumn
            if fixedColumn[0][0] < 700:
                x1 = fixedColumn[0][0]
                x2 = fixedColumn[1][0]
                spanNums = len(fixedColumn)
                k = 2
            else:
                x1 = 500
                for num in range(250, 700, 50):
                    found_match = False
                    for node in obstaclerange:
                        if node[0] < num < node[1]:
                            found_match = True
                            break
                    if not found_match:
                        x1 = num
                        break
                x2 = fixedColumn[0][0]
                spanNums = len(fixedColumn) + 1
                k = 1
            for i in range(spanNums - 1):
                column_positions.append(x1)
                spanWidth = x2 - x1
                column_min = int(spanWidth / max_spacing)
                if column_min != 0:
                    column_min = max(1, column_min)
                    column_max = 1000
                    for n_columns in range(column_min, column_max):
                        ideal_spacing = int(spanWidth / n_columns) + 1  # 计算理想间距
                        if ideal_spacing > max_spacing:
                            continue
                        for i in range(1, n_columns):
                            x = int(i * ideal_spacing + x1)
                            column_positions.append(x)
                        if len(column_positions) != 0:
                            break
    #                    templist = []
    #                    templist = dfsColumn_position(x1, n_columns - 1, x2, column_positions,
    #                                                        obstaclerange, ideal_spacing, 2)  # 递归搜索下一个数
    #                    if (x2 - templist[-1]) <= ideal_spacing:
    #                        column_positions += templist
    #                        break


    #            column_positions = list(set(column_positions))
    #            column_positions = sorted(column_positions)
                x1 = x2
                if k < len(fixedColumn):
                    x2 = fixedColumn[k][0]
                k += 1
            # 右边缘的立柱
            if width - fixedColumn[-1][0] < 700:
                column_positions.append(fixedColumn[-1][0])
            else:
                x1 = fixedColumn[-1][0]
                x2 = width - 500
                column_positions.append(x1)
                spanWidth = x2 - x1
                column_min = int(spanWidth / max_spacing)
                if column_min == 0:
                    column_positions.append(x2)
                else:
                    column_min = max(1, column_min)
                    column_max = 1000
                    le = len(column_positions)
                    for n_columns in range(column_min, column_max):
                        ideal_spacing = int(spanWidth / (n_columns + 1))  # 计算理想间距
                        if ideal_spacing > max_spacing:
                            continue
                        ideal_spacing = min(max_spacing, ideal_spacing)
                        for i in range(1, n_columns):
                            x = int(i * ideal_spacing + x1)
                            column_positions.append(x)
                        if len(column_positions) != le:
                            break
        #                templist = []
        #                templist = dfsColumn_position(x1, n_columns - 1, x2, column_positions,
        #                                              obstaclerange, ideal_spacing, 2)  # 递归搜索下一个数
        #                if (x2 - templist[-1]) <= ideal_spacing:
        #                    column_positions += templist
        #                    break
        #            column_positions = list(set(column_positions))
        #            column_positions = sorted(column_positions)
                    column_positions.append(x2)

            self.columnArray_x.append(column_positions[0])
            for i in range(len(column_positions) - 1):
                self.columnArray_x.append(column_positions[i + 1] - column_positions[i])
            self.columnArray_x.append(width - column_positions[-1])
            result = []
            self.edgeColumn = []
            if leftNum == 0 and rightNum == 0:
                for x in column_positions:
                    for y in result_y:
                        if 0 <= x < width and 0 <= y < length:
                            if obstacles[x + startX][y + startY] != 1:
                                result.append([startX + x, startY + y])
                        if x == column_positions[0] or x == column_positions[-1]:
                            if y == result_y[0] or y == result_y[-1]:
                                self.edgeColumn.append([startX + x, startY + y])
            else:
                for x in column_positions:
                    for y in result_yleft:
                        if 0 <= x < bound and 0 <= y < length:
                            if obstacles[x + startX][y + startY] != 1:
                                result.append([startX + x, startY + y])
                        if x == column_positions[0]:
                            if y == result_yleft[0] or y == result_yleft[-1]:
                                self.edgeColumn.append([startX + x, startY + y])
                for x in column_positions:
                    for y in result_yright:
                        if bound <= x < width and 0 <= y < length:
                            if obstacles[x + startX][y + startY] != 1:
                                result.append([startX + x, startY + y])
                        if x == column_positions[-1]:
                            if y == result_yright[0] or y == result_yright[-1]:
                                self.edgeColumn.append([startX + x, startY + y])
            final_list = []
            for node in result:
                flag = 1
                # 立柱扣除
                #                for component in self.componentPositionArray:
                #                    if (component[0][0] <= node[0] <= component[1][0]
                #                            and component[0][1] <= node[1] <= component[1][1]):
                #                        flag = 1
                #                for i in deletedIndices:
                #                    component = self.componentPositionArray[i]
                #                    if (component[0][0] <= node[0] <= component[1][0]
                #                            and component[0][1] < node[1] < component[1][1]):
                #                        flag = 0
                if flag == 1:
                    final_list.append(node)
            if type == "正7形":
                for node in self.edgeColumn:
                    node[0] = roof_Width - node[0]
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
                for j in range(self.componentLayoutArray[i]):
                    self.componentPositionArray.append([[startX, startY], [startX + self.component.width - 1,
                                                                           startY + self.component.length - 1]])
                    startX += self.component.width + PhotovoltaicPanelCrossMargin
                startX -= (self.component.width + PhotovoltaicPanelCrossMargin) * self.componentLayoutArray[i]
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
                for j in range(self.componentLayoutArray[i]):
                    self.componentPositionArray.append([[startX, startY], [startX + self.component.realWidth - 1,
                                                                           startY + self.component.realLength - 1]])
                    startX += self.component.realWidth + PhotovoltaicPanelCrossMargin
                startX -= (self.component.realWidth + PhotovoltaicPanelCrossMargin) * self.componentLayoutArray[i]
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
                if self.componentLayoutArray[0] < self.componentLayoutArray[-1]:
                    first_element = self.componentLayoutArray[0]
                    count = self.componentLayoutArray.count(first_element)
                    hMin = arrangementHeight[(componentStr, len(self.componentLayoutArray), 0, count, 0, 0)]
                else:
                    last_element = self.componentLayoutArray[-1]
                    count = self.componentLayoutArray.count(last_element)
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

    def calculateComponentHeightArray(self, raiseLevel=0):
        UNIT = const.const.getUnit()
        length = (self.relativePositionArray[-1][1][1] - self.relativePositionArray[0][0][0] + 1) * UNIT
        width = max(node[1][0] for node in self.relativePositionArray)
        # width = 0
        # for node in self.relativePositionArray:
        #     if width < node[1][0]:
        #         width = node[1][0]
        componentStr = self.component.specification + self.arrangeType
        if len(self.relativePositionArray) == 1:
            hMin = arrangementHeight[(componentStr, len(self.componentLayoutArray), 0, 0, 0, 0)]
            # hMin = arrangement_height[("182-78膨胀常规", 2, 1, 0)]
        else:
            if self.crossPosition == INF:  # 只有竖排
                # for num in self.componentLayoutArray:
                #     if num == first_element:
                #         count += 1
                if self.componentLayoutArray[0] < self.componentLayoutArray[-1]:
                    first_element = self.componentLayoutArray[0]
                    count = self.componentLayoutArray.count(first_element)
                    hMin = arrangementHeight[(componentStr, len(self.componentLayoutArray), 0, count, 0, 0)]
                else:
                    last_element = self.componentLayoutArray[-1]
                    count = self.componentLayoutArray.count(last_element)
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
                count1 = sum(1 for i in range(len(self.componentLayoutArray) - 2) if
                             self.componentLayoutArray[i] < normal_vertical)
                count2 = 1 if self.componentLayoutArray[-2] < normal_cross else 0
                count3 = 1 if self.componentLayoutArray[-1] < normal_vertical else 0
                try:
                    hMin = arrangementHeight[
                        (componentStr, len(self.componentLayoutArray) - 1, 1, count1, count2, count3)]
                except KeyError:
                    print("KeyError: ", componentStr, len(self.componentLayoutArray) - 1, 1, count1, count2, count3)
        if raiseLevel == 1:
            hMin = 540
        elif raiseLevel == 2:
            hMin = 1000
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
        length = int(length / UNIT)
        return_list = np.zeros((length + 1, width + 1), dtype=np.float64)
        for node in self.relativePositionArray:
            max_x = node[1][0]
            min_x = node[0][0]
            max_y = node[1][1]
            min_y = node[0][1]

            y_range = np.arange(min_y, max_y + 1)
            x_range = np.arange(min_x, max_x + 1)
            return_list[np.ix_(y_range, x_range)] = hMin + temp * (length - y_range[:, np.newaxis])
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
                        [0, 1, "182-78", "膨胀常规", "高压"],

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
    maxWidthCount = 0
    minComponentWidth = INF
    for c in getAllComponents():
        if minComponentWidth > c.width:
            minComponentWidth = c.width
    while calculateVerticalWidth(maxWidthCount, minComponentWidth) <= roofWidth:
        maxWidthCount += 1
    # print("maxWidthCount: ", maxWidthCount)
    maxWidthCount = min(31, maxWidthCount)
    global ID
    for tempElement in tempArrangements:
        if tempElement[1] == 0:  # 只有竖排
            for j in range(2, maxWidthCount):
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
                for j in range(minVerticalNum, maxWidthCount):
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
                for j in range(minVerticalNum, maxWidthCount):
                    maxCrossNum = 0
                    while calculateVerticalWidth(j, tempComponent.width) >= calculateCrossWidth(maxCrossNum,
                                                                                                tempComponent.length):
                        maxCrossNum += 1
                    maxCrossNum -= 1
                    tempArr = tempElement[0] * [j] + tempElement[1] * [maxCrossNum]
                    arrangementDict[ID] = Arrangement(tempArr, 1, tempElement[2], tempElement[3], tempElement[4], True)
                    ID += 1
    # 添加拼接方案
    # 提前计算好i个竖排的宽度能放多少个横排组件 todo:把这个优化放到前面去
    crossCountDict = {"182-78": [0] * maxWidthCount, "210-60": [0] * maxWidthCount, "182-72": [0] * maxWidthCount,
                      "210-66": [0] * maxWidthCount}
    # 目前只计算182-78的
    tempComponent = None
    for c in getAllComponents():
        if c.specification == "182-78":
            tempComponent = c
            break
    for i in range(2, maxWidthCount):
        crossCount = 0
        while calculateVerticalWidth(i, tempComponent.width) >= calculateCrossWidth(crossCount, tempComponent.length):
            crossCount += 1
        crossCount -= 1
        crossCountDict["182-78"][i] = crossCount

    for i in range(2, maxWidthCount):
        for j in range(1, i):
            arrangementDict[ID] = Arrangement([i, i, i, i, j], INF, "182-78", "膨胀常规", "低压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([i, i, i, j, j], INF, "182-78", "膨胀常规", "低压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([i, i, j, j, j], INF, "182-78", "膨胀常规", "低压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([j, i, i, i, i], INF, "182-78", "膨胀常规", "低压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([j, j, i, i, i], INF, "182-78", "膨胀常规", "低压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([j, j, j, i, i], INF, "182-78", "膨胀常规", "低压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([i, i, i, i, j], INF, "182-78", "膨胀常规", "高压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([i, i, i, j, j], INF, "182-78", "膨胀常规", "高压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([i, i, j, j, j], INF, "182-78", "膨胀常规", "高压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([j, i, i, i, i], INF, "182-78", "膨胀常规", "高压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([j, j, i, i, i], INF, "182-78", "膨胀常规", "高压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([j, j, j, i, i], INF, "182-78", "膨胀常规", "高压", False)
            ID += 1
            if crossCountDict["182-78"][i] != 0:
                arrangementDict[ID] = Arrangement([j, j, j, crossCountDict["182-78"][i], i], 3, "182-78", "膨胀常规",
                                                  "低压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([j, j, i, crossCountDict["182-78"][i], i], 3, "182-78", "膨胀常规",
                                                  "低压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([j, i, i, crossCountDict["182-78"][i], i], 3, "182-78", "膨胀常规",
                                                  "低压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([i, i, i, crossCountDict["182-78"][i], j], 3, "182-78", "膨胀常规",
                                                  "低压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([j, j, j, crossCountDict["182-78"][i], i], 3, "182-78", "膨胀常规",
                                                  "高压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([j, j, i, crossCountDict["182-78"][i], i], 3, "182-78", "膨胀常规",
                                                  "高压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([j, i, i, crossCountDict["182-78"][i], i], 3, "182-78", "膨胀常规",
                                                  "高压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([i, i, i, crossCountDict["182-78"][i], j], 3, "182-78", "膨胀常规",
                                                  "高压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([j, j, crossCountDict["182-78"][i], i], 2, "182-78", "膨胀常规",
                                                  "低压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([j, i, crossCountDict["182-78"][i], i], 2, "182-78", "膨胀常规",
                                                  "低压", False)
                ID += 1

                arrangementDict[ID] = Arrangement([i, i, crossCountDict["182-78"][i], j], 2, "182-78", "膨胀常规",
                                                  "低压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([j, j, crossCountDict["182-78"][i], i], 2, "182-78", "膨胀常规",
                                                  "高压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([j, i, crossCountDict["182-78"][i], i], 2, "182-78", "膨胀常规",
                                                  "高压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([i, i, crossCountDict["182-78"][i], j], 2, "182-78", "膨胀常规",
                                                  "高压", False)
                ID += 1
            if crossCountDict["182-78"][j] != 0:
                arrangementDict[ID] = Arrangement([i, i, j, crossCountDict["182-78"][j], j], 3, "182-78", "膨胀常规",
                                                  "低压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([i, i, i, crossCountDict["182-78"][j], j], 3, "182-78", "膨胀常规",
                                                  "低压", False)
                ID += 1

                arrangementDict[ID] = Arrangement([i, i, j, crossCountDict["182-78"][j], j], 3, "182-78", "膨胀常规",
                                                  "高压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([i, i, i, crossCountDict["182-78"][j], j], 3, "182-78", "膨胀常规",
                                                  "高压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([i, i, crossCountDict["182-78"][j], j], 2, "182-78", "膨胀常规",
                                                  "低压", False)
                ID += 1
                arrangementDict[ID] = Arrangement([i, i, crossCountDict["182-78"][j], j], 2, "182-78", "膨胀常规",
                                                  "高压", False)
                ID += 1

            arrangementDict[ID] = Arrangement([j, j, i, i], INF, "182-78", "膨胀常规", "低压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([j, i, i, i], INF, "182-78", "膨胀常规", "低压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([i, i, j, j], INF, "182-78", "膨胀常规", "低压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([i, i, i, j], INF, "182-78", "膨胀常规", "低压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([j, j, i, i], INF, "182-78", "膨胀常规", "高压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([j, i, i, i], INF, "182-78", "膨胀常规", "高压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([i, i, j, j], INF, "182-78", "膨胀常规", "高压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([i, i, i, j], INF, "182-78", "膨胀常规", "高压", False)
            ID += 1

            arrangementDict[ID] = Arrangement([j, i, i], INF, "182-78", "膨胀常规", "低压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([i, i, j], INF, "182-78", "膨胀常规", "低压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([j, i, i], INF, "182-78", "膨胀常规", "高压", False)
            ID += 1
            arrangementDict[ID] = Arrangement([i, i, j], INF, "182-78", "膨胀常规", "高压", False)
            ID += 1

    # 通过输入的屋顶宽度、屋顶长度、组件类型、排布类型和风压，筛选出合适的排布
    result = {}
    arrangementDict = {k: v for k, v in arrangementDict.items() if v.legal}
    for k, arrangement in arrangementDict.items():
        if arrangement.component.specification == componentSpecification and arrangement.arrangeType[0:2] == \
                arrangeType[0:2] and arrangement.maxWindPressure == windPressure:
            for tempElement in arrangement.relativePositionArray:
                if tempElement[1][0] >= roofWidth or tempElement[1][1] >= roofLength:
                    break
            else:
                result[k] = arrangement
    return result


def estimateComponentCount(roofArea, componentSpecification, minAlpha=0.7):
    component = getComponent(componentSpecification)
    componentArea = component.realLength * component.realWidth
    maxComponentCount = int(roofArea / componentArea)
    return int(minAlpha * maxComponentCount), maxComponentCount


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
