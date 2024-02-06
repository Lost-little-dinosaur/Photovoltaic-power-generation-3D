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
    12 / UNIT) - PhotovoltaicPanelVerticalMargin  # 横光伏板和竖光伏板y轴方向与PhotovoltaicPanelVerticalMargin的差值
# 横斜梁限制
distanceBeamExceed = round(43 / UNIT)  # 横梁要超出组件的距离
distanceBeamDiagonalBeam = round(50 / UNIT)  # 横梁要超出斜梁的距离
columNlimit = 10000
# 立柱排布 a[0][1]=竖1横0
# 182-78组件
column_78_normal = [
    [[], [1100], [1900, 1750], [1900, 3200], [1700, 2600, 3200], [1700, 2600, 2600, 3750]],
    [[1250], [2600], [1350, 2950], [1700, 2600, 2450], [1700, 2600, 2600, 2500]]
]  # 182-78常规
limit_78_normal = [
    [[], [250, columNlimit], [250, columNlimit], [800, columNlimit], [250, columNlimit], [250, columNlimit]],
    [[250, columNlimit], [250, columNlimit], [500, columNlimit], [250, columNlimit], [250, columNlimit]]
]  # 182-78常规_左右限制

column_78_Abutments = [
    [[], [1200], [1900, 1750], [1300, 2000, 1700], [1700, 1700, 1800, 2300], []],
    [[1250], [], [], [], []]
]  # 182-78基墩
limit_78_Abutments = [
    [[], [300, columNlimit], [300, columNlimit], [450, columNlimit], [865, columNlimit], [300, columNlimit]],
    [[300, columNlimit], [300, columNlimit], [300, columNlimit], [300, columNlimit], [300, columNlimit]]
]  # 182-78基墩_左右限制

column_78_raise = [
    [[], [], [2000, 1800], [2000, 3100], [1700, 2600, 3400], [1700, 2600, 2600, 2300]],
    [[], [1400, 2400], [1900, 2300, 2600], [2600, 2600, 2500, 1400], []]
]  # 182-78抬高
limit_78_raise = [
    [[], [250, columNlimit], [250, columNlimit], [800, columNlimit], [250, columNlimit], [1713, columNlimit]],
    [[250, columNlimit], [670, 670], [440, columNlimit], [350, columNlimit], [250, columNlimit]]
]  # 182-78抬高_左右限制

# 182-72组件
column_72_normal = [
    [[], [1100], [1900, 1250], [1900, 3200], [1700, 2600, 3200], [1700, 2650, 2550, 2450]],
    [[1250], [2550], [1500, 2800], [1700, 2600, 2450], [1700, 2600, 2600, 2500]]
]  # 182-72常规
limit_72_normal = [
    [[], [250, columNlimit], [250, columNlimit], [800, columNlimit], [250, columNlimit], [250, columNlimit]],
    [[250, columNlimit], [250, columNlimit], [250, columNlimit], [250, columNlimit], [250, columNlimit]]
]  # 182-72常规_左右限制

column_72_Abutments = [
    [[], [1100], [1900, 1250], [1300, 2000, 1700], [1700, 1700, 1800, 2300], []],
    [[1250], [], [], [], []]
]  # 182-72基墩
limit_72_Abutments = [
    [[], [300, columNlimit], [300, columNlimit], [600, columNlimit], [300, columNlimit], [300, columNlimit]],
    [[300, columNlimit], [300, columNlimit], [300, columNlimit], [300, columNlimit], [300, columNlimit]]
]  # 182-72基墩_左右限制

column_72_raise = [
    [[], [], [2000, 1800], [2000, 3100], [1700, 2600, 3400], [1700, 2450, 2750, 2300]],
    [[], [], [1400, 2400], [1900, 2300, 2600], [2600, 2600, 2500, 1400]]
]  # 182-72抬高
limit_72_raise = [
    [[], [250, columNlimit], [250, columNlimit], [250, columNlimit], [250, columNlimit], [811, columNlimit]],
    [[250, columNlimit], [670, 670], [440, columNlimit], [350, columNlimit], [250, columNlimit]]
]  # 182-72抬高_左右限制

# 210-60组件
column_60_normal = [
    [[], [1100], [1100, 2000], [1900, 3200], [1700, 2600, 3099], [1700, 2600, 2600, 2600]],
    [[1200], [2600], [1350, 2950], [1700, 2600, 1700], [1700, 2600, 2600, 1600]]
]  # 210-60常规
limit_60_normal = [
    [[], [250, columNlimit], [250, columNlimit], [250, columNlimit], [250, columNlimit], [250, columNlimit]],
    [[250, columNlimit], [250, columNlimit], [450, columNlimit], [250, columNlimit], [250, columNlimit]]
]  # 210-60常规_左右限制

column_60_Abutments = [
    [[], [1300], [1100, 2000], [1300, 2000, 1700], [1700, 1700, 1800, 2400], []],
    [[1200], [], [], [], []]
]  # 210-60基墩
limit_60_Abutments = [
    [[], [300, columNlimit], [300, columNlimit], [300, columNlimit], [300, columNlimit], [300, columNlimit]],
    [[300, columNlimit], [300, columNlimit], [300, columNlimit], [300, columNlimit], [300, columNlimit]]
]  # 210-60基墩_左右限制

column_60_raise = [
    [[], [], [1400, 1700], [2000, 3000], [1700, 2200, 3500], [1700, 2600, 2600, 2200]],
    [[], [], [1400, 2400], [1900, 2300, 1750], [2600, 2600, 2500]]
]  # 210-60抬高
limit_60_raise = [
    [[], [250, columNlimit], [250, columNlimit], [250, columNlimit], [250, columNlimit], [450, columNlimit]],
    [[250, columNlimit], [350, columNlimit], [670, columNlimit], [1047, 1047], [250, columNlimit]]
]  # 210-60抬高_左右限制
