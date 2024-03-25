import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.ui_functions import *

def main():
    ui = UI(
        location_ui_info=[["经度", "纬度"], [], [], []],
        roof_ui_info=[
        # ["A边（mm）", "B边（mm）", "高度（mm）", "偏移角度", "倾斜角度"], 
        ["A边（mm）", "B边（mm）", "高度（mm）"], 
        ["屋面类型"], 
        [
            # ["矩形","上凸形","下凸形","左凸形","右凸形","上凹形","下凹形","左凹形","右凹形","正7形","反7形","正L形","反L形"]
            ["矩形","上凸形","正7形","反7形"]
        ],
        []],
        obstacle_ui_info=[["ID", "直径", "长度（mm）", "宽度（mm）", "高度（mm）", "距离西侧屋顶距离", "距离北侧屋顶距离"],
                          ["类型"], [["无烟烟囱", "有烟烟囱"]], ["是否圆形"]],
        outside_obstacle_ui_info=[],
        panel_ui_info=[["功率", "厚度"], [], [], []],
        scheme_options=["膨胀螺栓", "膨胀抬高", "基墩"],
        algorithm_ui_info=[["精度（mm）", "最大方案数量"], [], [], []])

    ui.run()


if __name__ == "__main__":
    import cProfile
    import pstats

    prof = cProfile.Profile()
    prof.run('main()')
    prof.dump_stats('output.prof')

    stream = open('output.txt', 'w')
    stats = pstats.Stats('output.prof', stream=stream)
    stats.sort_stats('tottime')
    stats.print_stats()
    # main()
