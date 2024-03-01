from const.const import INF, getUnit


class Component:
    def __init__(self, specification, width, length, verticalSpacing, verticalShortSideSize, crossSpacing,
                 crossShortSideSize, power=INF, thickness=INF, statX=INF, statY=INF, endX=INF, endY=INF,
                 direction=INF, marginRight=INF, marginBottom=INF):
        UNIT = getUnit()
        self.specification = specification
        # 将width和length转换成以UNIT为单位
        self.width = round(width / UNIT)
        self.length = round(length / UNIT)
        self.power = power
        self.thickness = thickness
        self.startX = statX
        self.startY = statY
        self.endX = endX
        self.endY = endY
        self.direction = direction  # 1表示纵向，2表示横向
        self.marginRight = marginRight  # 该矩形右边的间距（只记录每个矩形下边的间距和右边的间距）
        self.marginBottom = marginBottom  # 该矩形下边的间距（只记录每个矩形下边的间距和右边的间距）
        self.verticalSpacing = round(verticalSpacing / UNIT)  # 横梁间距（竖排放）
        self.verticalShortSideSize = round(verticalShortSideSize / UNIT)  # 横梁离短边距离（竖排放）
        self.crossSpacing = round(crossSpacing / UNIT)  # 横梁间距（横排放）
        self.crossShortSideSize = round(crossShortSideSize / UNIT)  # 横梁离短边距离（横排放）


# def assignComponentParameters(parameterDict):
#     global components
#     for component in components:
#         if component.specification == parameterDict["specification"]:
#             component.power = parameterDict["power"]
#             component.thickness = parameterDict["thickness"]
#             break


pvPanelInclination = 20  # todo：之后再加倾角


# component1 = Component("182-72", 1134, 2279, 1400, 439, 1108, 13)  # 以米、瓦为单位
# component2 = Component("182-78", 1134, 2465, 1500, 4825, 1108, 13)  # 以米、瓦为单位
# component3 = Component("210-60", 1303, 2172, 1400, 386, 1277, 13)  # 以米、瓦为单位
# component4 = Component("210-66", 1303, 2384, 1400, 492, 0, 0)  # 以米、瓦为单位
# components = [component1, component2, component3, component4]


def getAllComponents():
    component1 = Component("182-72", 1134, 2279, 1400, 439, 1108, 13)  # 以米、瓦为单位
    component2 = Component("182-78", 1134, 2465, 1500, 4825, 1108, 13)  # 以米、瓦为单位
    component3 = Component("210-60", 1303, 2172, 1400, 386, 1277, 13)  # 以米、瓦为单位
    component4 = Component("210-66", 1303, 2384, 1400, 492, 0, 0)  # 以米、瓦为单位
    return [component1, component2, component3, component4]
