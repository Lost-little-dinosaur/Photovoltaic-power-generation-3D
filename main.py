import classes.roof
from classes.arrangement import screenArrangements
from classes.component import assignComponentParameters
import json

# 输入和输出的单位是都是毫米
if __name__ == '__main__':
    with open('input.json', 'r', encoding='utf-8') as f:
        jsonData = json.load(f)
    roof = classes.roof.Roof(jsonData["scene"]["roof"], jsonData["scene"]["location"]["latitude"])
    for obstacle in jsonData["scene"]["roof"]["obstacles"]:
        roof.addObstacle(obstacle)
    for obstacle in jsonData["scene"]["obstacles"]:
        roof.addSceneObstacle(obstacle)

    assignComponentParameters(jsonData["component"])
    screenedArrangements = screenArrangements(roof.width, roof.length, jsonData["component"], jsonData["arrangeType"],
                                              jsonData["scene"]["location"]["windPressure"])

    roof.getBestOption(screenedArrangements)  # 计算铺设光伏板的最佳方案

    roof.removeComponentsWithFalseFool()
    roof.renewRects2Array()

    roof.paintBoolArray("plt")  # img库会打开一张图片，更方便观察细节，但稍微慢个几秒钟；plt库不会打开图片，更快，适合批量处理
    # test commit
