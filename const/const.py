# 规定一些常量
UNIT = 10  # 以毫米为单位
INF = 1000000000000  # 无穷大
roofBoardLength = int(5 * UNIT / 10)  # 打印屋顶示意图时，额外屋顶边缘的宽度（单位是单元格）
PhotovoltaicPanelBoardLength = int(3 * UNIT / 10)  # 打印屋顶示意图时，额外光伏板边缘的宽度（单位是单元格）

# 地图中的元素（别删，之后可能会用到！！！）
# Empty = 0  # 空地
# Obstacle = 1  # 障碍物
# Shadow = 2  # 阴影
# PhotovoltaicPanel = 3  # 光伏板
# PhotovoltaicPanelBorder = 6  # 光伏板边框
# PhotovoltaicPanelMargin = 7  # 光伏板边缘
# Margin = 4  # 边缘
# RoofMargin = 5  # 屋顶边缘
# ColorDict = {Empty: (1.0, 1.0, 1.0, 1.0), Obstacle: (0.0, 0.0, 0.0, 1.0),
#              Shadow: (0.5019607843137255, 0.5019607843137255, 0.5019607843137255, 1.0),
#              PhotovoltaicPanel: (1.0, 1.0, 0.0, 1.0), Margin: (1.0, 0.0, 0.0, 1.0), RoofMargin: (0.0, 0.0, 0.0, 1.0),
#              PhotovoltaicPanelMargin: (0.43, 0.43, 0.43, 1.0), PhotovoltaicPanelBorder: (0.0, 0.0, 0.0, 1.0)}
EmptyColor = (1.0, 1.0, 1.0, 1.0)  # 空地
ObstacleColor = (0.0, 0.0, 0.0, 1.0)  # 障碍物
ShadowColor = (0.5019607843137255, 0.5019607843137255, 0.5019607843137255, 1.0)  # 阴影
PhotovoltaicPanelColor = (1.0, 1.0, 0.0, 1.0)  # 光伏板
MarginColor = (1.0, 0.0, 0.0, 1.0)  # 边缘
RoofMarginColor = (0.0, 0.0, 0.0, 1.0)  # 屋顶边缘
PhotovoltaicPanelMarginColor = (0.43, 0.43, 0.43, 1.0)  # 光伏板边缘
PhotovoltaicPanelBorderColor = (0.0, 0.0, 0.0, 1.0)  # 光伏板边框

# 光伏板横竖排之间的间距
PhotovoltaicPanelCrossMargin = round(6 / UNIT)  # 光伏板的横向缝隙
PhotovoltaicPanelVerticalMargin = round(6 / UNIT)  # 竖光伏板和竖光伏板y轴方向的缝隙
PhotovoltaicPanelVerticalDiffMargin = round(
    0.012 / UNIT) - PhotovoltaicPanelVerticalMargin  # 横光伏板和竖光伏板y轴方向与PhotovoltaicPanelVerticalMargin的差值
# 横斜梁限制
distanceBeamExceed = round(43 / UNIT)  # 横梁要超出组件的距离
distanceBeamDiagonalBeam = round(50 / UNIT)  # 横梁要超出斜梁的距离
