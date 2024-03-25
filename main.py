from ui import demo_UI as UI
import multiprocessing

# 输入和输出的单位是都是毫米
if __name__ == '__main__':
    # with open('input.json', 'r', encoding='utf-8') as f:
    #     jsonData = json.load(f)
    # roof = classes.roof.Roof(jsonData["scene"]["roof"], jsonData["scene"]["location"]["latitude"])
    #
    # assignComponentParameters(jsonData["component"])
    # screenedArrangements = screenArrangements(roof.width, roof.length, jsonData["component"]["specification"],
    #                                           jsonData["arrangeType"], jsonData["scene"]["location"]["windPressure"])
    #
    # roof.getValidOptions(screenedArrangements)  # 计算铺设光伏板的最佳方案

    # screenedArrangements[420].calculateComponentPositionArray(0, 0)
    # print(screenedArrangements[420].componentPositionArray)
    # # 排布完光伏板后再添加障碍物并分析阴影
    # roof.addObstaclesConcern(jsonData["scene"]["roof"]["obstacles"], screenedArrangements)
    # roof.obstacleArraySelf = roof.calculateObstacleSelf()
    # roof.calculate_column(screenedArrangements)
    multiprocessing.freeze_support()
    UI.main()



    # roof.addSceneObstacles(jsonData["scene"]["obstacles"])
    # roof.paintBoolArray("plt")  # img库会打开一张图片，更方便观察细节，但稍微慢个几秒钟；plt库不会打开图片，更快，适合批量处理
    # test commit

