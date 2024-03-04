import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui.ui_functions import *
import cProfile


def main():
    ui = UI(
        location_ui_info=[["经度", "纬度"], [], [], []],
        roof_ui_info=[["长度（mm）", "宽度（mm）", "高度（mm）"], [], [], []],
        obstacle_ui_info=[["ID", "直径", "长度（mm）", "宽度（mm）", "高度（mm）", "距离西侧屋顶距离", "距离北侧屋顶距离"],
                          ["类型"], [["无烟烟囱", "有烟烟囱"]], ["是否圆形"]],
        outside_obstacle_ui_info=[],
        panel_ui_info=[["功率", "厚度"], [], [], []],
        scheme_options=["膨胀常规", "膨胀抬高", "基墩"],
        algorithm_ui_info=[["精度（mm）", "最大方案数量"], [], [], []])

    ui.run()


if __name__ == "__main__":
    # cProfile.run("main()")
    main()
