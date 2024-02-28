import numpy as np

arr1 = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
arr2 = np.array([[10, 20, 30], [40, 50, 60], [70, 80, 90]])
# 测试：(placement[2][tempArray[i][0][1]:tempArray[i][1][1] + 1, tempArray[i][0][
#                         0]:tempArray[i][1][0] + 1] < screenedArrangements[arrange['ID']].componentHeightArray[
#                                                      tempArray[i][0][1] - arrangeStartY:tempArray[i][1][
#                                                                                             1] - arrangeStartY + 1,
#                                                      tempArray[i][0][0] - arrangeStartX:tempArray[i][1][
#                                                                                             0] - arrangeStartX + 1]).all()
print((arr1[1:2, 1:2] < arr2[1:2, 1:2]).all())
