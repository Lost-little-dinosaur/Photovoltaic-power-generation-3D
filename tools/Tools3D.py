import numpy as np


def arePointsCoplanar(points):
    """判断四个点是否共面"""
    assert len(points) == 4, "点的数量必须为4"
    for point in points:
        assert len(point) == 3, "每个点的坐标必须为三维"

    # 构建矩阵，每个点增加一列1
    matrix = np.array([point + [1] for point in points])

    # 计算矩阵的秩
    rank = np.linalg.matrix_rank(matrix)

    # 如果秩小于3，则点共面
    return rank < 3


print(arePointsCoplanar([[10, 20, 0], [30, 40, 0], [50, 60, 0], [70, 80, 0.0000000000001]]))


def calculateShadow(nodeArray, obstacleArray=None):
    if not arePointsCoplanar(nodeArray):
        raise Exception("点不共面或者点的数量不为4")
    if obstacleArray is not None:  # 返回阴影数组
        pass
    else:  # 在obstacleArray上更新每个点的最高阴影
        pass
