from const.const import getUnit
from tools import tools3D


class Obstacle:
    def __init__(self, obstacle, obstacleArray, roofArray, latitude):
        UNIT = getUnit()
        self.type = obstacle["type"]
        self.ID = obstacle["id"]
        self.realArea = 0
        if obstacle["type"] == "有烟烟囱" or obstacle["type"] == "无烟烟囱":
            self.height = obstacle["height"]
            if not obstacle["isRound"]:
                self.isRound = False
                self.width = round(obstacle["width"] / UNIT)
                self.length = round(obstacle["length"] / UNIT)
                self.realwidth = obstacle["width"]
                self.reallength = obstacle["length"]
                self.upLeftPosition = [round(obstacle["upLeftPosition"][0] / UNIT),
                                       round(obstacle["upLeftPosition"][1] / UNIT)]
                self.realupLeftPosition = [obstacle["upLeftPosition"][0],
                                           obstacle["upLeftPosition"][1]]
                if roofArray.shape[0] < self.upLeftPosition[1] + self.width or roofArray.shape[1] < self.upLeftPosition[
                    0] + self.length:
                    raise Exception("障碍物位置超出屋面范围")  # todo: 先不考虑屋外障碍物
                tools3D.calculateShadow([[self.upLeftPosition[0], self.upLeftPosition[1], self.height +
                                          roofArray[self.upLeftPosition[1]][self.upLeftPosition[0]]],
                                         [self.upLeftPosition[0] + self.width, self.upLeftPosition[1],
                                          self.height + roofArray[self.upLeftPosition[1]][
                                              self.upLeftPosition[0] + self.width]],
                                         [self.upLeftPosition[0] + self.width, self.upLeftPosition[1] + self.length,
                                          self.height + roofArray[self.upLeftPosition[1] + self.length][
                                              self.upLeftPosition[0] + self.width]],
                                         [self.upLeftPosition[0], self.upLeftPosition[1] + self.length,
                                          self.height + roofArray[self.upLeftPosition[1] + self.length][
                                              self.upLeftPosition[0]]]], False, latitude, True, obstacleArray)
                self.realArea = self.realwidth * self.reallength 
            else:
                self.isRound = True
                self.diameter = obstacle["diameter"] / UNIT
                self.centerPosition = [obstacle["centerPosition"][0] / UNIT, obstacle["centerPosition"][1] / UNIT]
                # todo: 圆形的烟囱暂时不做计算阴影
        # elif obstacle["type"] == "屋面扣除":
        #     self.height = obstacle["height"]
        #     self.isRound = False
        #     self.width = obstacle["width"]
        #     self.length = obstacle["length"]
        #     self.upLeftPosition = [obstacle["upLeftPosition"][0], obstacle["upLeftPosition"][1]]
        elif obstacle["type"] == "热水器":  # 暂时只支持烟囱输入
            pass  # todo
        elif obstacle["type"] == "水塔":
            pass  # todo
        elif obstacle["type"] == "上人通道":
            pass  # todo
