import classes.roof
from classes.arrangement import screenArrangements
from classes.component import assignComponentParameters
import json

# 输入和输出的单位是都是毫米
if __name__ == '__main__':
    with open('input.json', 'r', encoding='utf-8') as f:
        jsonData = json.load(f)
    roof = classes.roof.Roof(jsonData["scene"]["roof"], jsonData["scene"]["location"]["latitude"])

    assignComponentParameters(jsonData["component"])
    screenedArrangements = screenArrangements(roof.width, roof.length, jsonData["component"]["specification"],
                                              jsonData["arrangeType"], jsonData["scene"]["location"]["windPressure"])

    roof.getValidOptions(screenedArrangements)  # 计算铺设光伏板的最佳方案
    roof.calculate_column(screenedArrangements)

    # 排布完光伏板后再添加障碍物并分析阴影
#    roof.addObstaclesConcern(jsonData["scene"]["roof"]["obstacles"], screenedArrangements)






    # roof.addSceneObstacles(jsonData["scene"]["obstacles"])
    # roof.paintBoolArray("plt")  # img库会打开一张图片，更方便观察细节，但稍微慢个几秒钟；plt库不会打开图片，更快，适合批量处理
    # test commit

