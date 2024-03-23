from const.const import INF, getUnit


class Component:
    def __init__(self, specification, width, length, verticalSpacing, verticalShortSideSize, crossSpacing,
                 crossShortSideSize, unit=getUnit(), power=INF, thickness=INF):
        # unit = getUnit()
        self.specification = specification
        # 将width和length转换成以UNIT为单位
        self.realWidth = width
        self.realLength = length
        self.width = round(width / unit)
        self.length = round(length / unit)
        self.power = power
        self.thickness = thickness
        self.verticalSpacing = round(verticalSpacing / unit)  # 横梁间距（竖排放）
        self.verticalShortSideSize = round(verticalShortSideSize / unit)  # 横梁离短边距离（竖排放）
        self.crossSpacing = round(crossSpacing / unit)  # 横梁间距（横排放）
        self.crossShortSideSize = round(crossShortSideSize / unit)  # 横梁离短边距离（横排放）


# def assignComponentParameters(parameterDict):
#     global components
#     for component in components:
#         if component.specification == parameterDict["specification"]:
#             component.power = parameterDict["power"]
#             component.thickness = parameterDict["thickness"]
#             break

parameterDict = {"specification": "182-78", "power": 595, "thickness": 350}


def assignComponentParameters(pD):
    global parameterDict
    parameterDict = pD


pvPanelInclination = 20  # todo：之后再加倾角


def getComponent(componentSpecification, unit=getUnit()):
    if componentSpecification == "182-78":
        return Component("182-78", 1134, 2465, 1400, 439, 1108, 13, unit)
    else:
        raise Exception("暂时不支持该型号的光伏板")

# component1 = Component("182-72", 1134, 2279, 1400, 439, 1108, 13)  # 以米、瓦为单位
# component2 = Component("182-78", 1134, 2465, 1500, 4825, 1108, 13)  # 以米、瓦为单位
# component3 = Component("210-60", 1303, 2172, 1400, 386, 1277, 13)  # 以米、瓦为单位
# component4 = Component("210-66", 1303, 2384, 1400, 492, 0, 0)  # 以米、瓦为单位
# components = [component1, component2, component3, component4]


# def getAllComponents(unit):
#     # global parameterDict
#     component1 = Component("182-72", 1134, 2279, 1400, 439, 1108, 13, unit)  # 以米、瓦为单位
#     component2 = Component("182-78", 1134, 2465, 1500, 4825, 1108, 13, unit)  # 以米、瓦为单位
#     component3 = Component("210-60", 1303, 2172, 1400, 386, 1277, 13, unit)  # 以米、瓦为单位
#     component4 = Component("210-66", 1303, 2384, 1400, 492, 0, 0, unit)  # 以米、瓦为单位
#     components = [component1, component2, component3, component4]
#     for component in components:
#         # try:
#         if component.specification == parameterDict["specification"]:
#             component.power = parameterDict["power"]
#             component.thickness = parameterDict["thickness"]
#             break
#         # except:
#         #     print("No parameterDict")
#     return components
