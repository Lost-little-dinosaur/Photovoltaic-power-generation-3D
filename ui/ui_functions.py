from math import sqrt
import sys, os

import numpy as np

# import Unet.test as UnetTest
from numpy import square
import const.const
from tools.mutiProcessing import *

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import classes.roof
from tkinter import filedialog
from classes.arrangement import estimateComponentCount, screenArrangements
from classes.component import assignComponentParameters
import json
import tkinter as tk
from PIL import Image, ImageTk
from functools import partial
import time

frame_width = 420
frame_height = 320
draw_gap = 25  # gap for drawing text
file_dir = "files"
chn2eng = {
    "省份": "province",
    "城市": "city",
    "行政区": "region",
    "经度": "longitude",
    "纬度": "latitude",
    "电压等级": "voltageLevel",
    "距离并网点的距离": "distanceToGridConnection",
    "风压": "windPressure",
    "雪压": "snowPressure",
    "风雪压": "windAndSnowPressure",
    "大雪": "heavySnow",

    "长度（mm）": "length",
    "宽度（mm）": "width",
    "高度（mm）": "height",
    "A边（mm）": "A",
    "B边（mm）": "B",
    "C边（mm）": "C",
    "D边（mm）": "D",
    "E边（mm）": "E",
    "F边（mm）": "F",
    "顶点数量": "vertexCount",

    "偏移角度": "roofDirection",
    "倾斜角度": "roofAngle",
    # "可探出距离": "extensibleDistance",
    "可探出距离（东）": "extensibleDistanceEast",
    "可探出距离（南）": "extensibleDistanceSouth",
    "可探出距离（西）": "extensibleDistanceWest",
    "可探出距离（北）": "extensibleDistanceNorth",
    # "是否有女儿墙": "haveParapetWall",
    # "女儿墙":"parapetWall",
    "女儿墙厚度": "parapetWallthick",
    "女儿墙高度（mm）（东）": "parapetWalleastHeight",
    "女儿墙高度（mm）（南）": "parapetWallsouthHeight",
    "女儿墙高度（mm）（西）": "parapetWallwestHeight",
    "女儿墙高度（mm）（北）": "parapetWallnorthHeight",
    "屋面类型": "roofSurfaceCategory",
    "屋顶类型": "category",
    "复杂屋顶": "isComplex",
    "预留运维通道": "maintenanceChannel",
    "是否有挑檐": "haveOverhangingEave",
    "ID": "id",
    "直径": "diameter",
    # "长度（mm）","宽度（mm）","高度（mm）",
    "距离西侧屋顶距离": "relativePositionX",
    "距离北侧屋顶距离": "relativePositionY",
    "可调整高度（mm）": "adjustedHeight",
    "类型": "type",
    "是否圆形": "isRound",
    "是否可移除": "removable",
    "安装方案": "arrangeType",
    "组件类型": "specification",
    "功率": "power",
    "厚度": "thickness",
    "精度（mm）": "precision",
    "最大方案数量": "maxArrangeCount",
    "贪心（单阵列）": "greedy",
    "DFS（多阵列）": "dfs",

    "图片路径": "imagePath",
    "图片分辨率": "resolution",
}

max_custom_vertex_in_irregular_roof = 50
for i in range(max_custom_vertex_in_irregular_roof):
    chn2eng[f"自定义{i}顶点的X坐标"] = f"vertex{i}_X"
    chn2eng[f"自定义{i}顶点的Y坐标"] = f"vertex{i}_Y"

eng2chn = {v: k for k, v in chn2eng.items()}

roof_outline_color = "yellow"
text_color = "white"


def is_nonempty_list(var):
    if isinstance(var, list) and len(var) > 0:
        return True
    else:
        return False


class UI:
    def __init__(self,
                 location_ui_info,
                 roof_ui_info,
                 obstacle_ui_info,
                 outside_obstacle_ui_info,
                 panel_ui_info,
                 scheme_options,
                 algorithm_ui_info,
                 ):

        self.location_info = {}
        self.roof_info = {}
        self.obstacle_info = []
        self.outside_obstacle_info = []
        self.panel_info = {}
        self.algorithm_info = {}
        self.layout_imgs = []
        self.layout_final_info = ""
        self.display_img = None

        self.root = tk.Tk()
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.title("光伏板排布计算")
        # 创建左侧的按钮
        left_frame = tk.Frame(self.root)
        left_frame.pack(side=tk.LEFT, padx=20, pady=20)

        if is_nonempty_list(location_ui_info):
            # Buttons for adding information
            location_btn = tk.Button(left_frame, text="添加位置信息",
                                     command=partial(self.open_location_window, *location_ui_info))
            location_btn.pack(fill=tk.X, pady=5)

        if is_nonempty_list(roof_ui_info):
            roof_btn = tk.Button(left_frame, text="添加屋顶信息",
                                 command=partial(self.open_roof_window, *roof_ui_info))
            roof_btn.pack(fill=tk.X, pady=5)

        if is_nonempty_list(obstacle_ui_info):
            obstacle_btn = tk.Button(left_frame, text="添加屋内障碍物信息",
                                     command=partial(self.open_obstacle_window, *obstacle_ui_info))
            obstacle_btn.pack(fill=tk.X, pady=5)

        if is_nonempty_list(outside_obstacle_ui_info):
            outside_obstacle_btn = tk.Button(left_frame, text="添加屋外障碍物信息",
                                             command=partial(self.open_outside_obstacle_window,
                                                             *outside_obstacle_ui_info))
            outside_obstacle_btn.pack(fill=tk.X, pady=5)

        if is_nonempty_list(panel_ui_info):
            panel_btn = tk.Button(left_frame, text="添加光伏板信息",
                                  command=partial(self.open_panel_window, *panel_ui_info))
            panel_btn.pack(fill=tk.X, pady=5)

        clear_btn = tk.Button(left_frame, text="清空输入信息", command=self.clear_info)
        clear_btn.pack(fill=tk.X, pady=5)

        # Frame for installation scheme selection
        if is_nonempty_list(scheme_options):
            scheme_frame = tk.Frame(left_frame)
            scheme_frame.pack(fill=tk.X)
            # Installation scheme selection
            scheme_label = tk.Label(scheme_frame, text="安装方案")
            scheme_label.pack(side=tk.LEFT)
            self.arrangeType_var = tk.StringVar(scheme_frame)
            self.arrangeType_var.set(scheme_options[0])
            scheme_menu = tk.OptionMenu(scheme_frame, self.arrangeType_var, *scheme_options, )
            scheme_menu.config(width=10)
            scheme_menu.pack(side=tk.LEFT)

        # Button to calculate PV panel layout
        draw_btn = tk.Button(left_frame, text="展示屋面场景", command=self.draw_roofscene)
        draw_btn.pack(fill=tk.X, pady=(0, 20))

        if is_nonempty_list(algorithm_ui_info):
            algorithm_btn = tk.Button(left_frame, text="选择算法类型",
                                      command=partial(self.open_algorithm_window, *algorithm_ui_info))
            algorithm_btn.pack(fill=tk.X, pady=0)

        calculate_btn = tk.Button(left_frame, text="计算光伏板排布", command=self.cal_and_display_layout)
        calculate_btn.pack(fill=tk.X, pady=(0, 20))

        # 创建右侧的区域，包括“原始拓扑”文字标签和图片显示区域
        arrangement_frame = tk.Frame(self.root)
        arrangement_frame.pack(side=tk.RIGHT, padx=20, pady=20)

        # 创建右侧的区域，包括“原始拓扑”文字标签和图片显示区域
        arrangement_info_frame = tk.Frame(arrangement_frame)
        arrangement_info_frame.pack(side=tk.RIGHT, padx=20, pady=20)

        # 文字标签放置在右侧区域
        arrangement_info_text = tk.Label(arrangement_info_frame, text="排布信息", font=("Arial", 12))
        arrangement_info_text.pack()
        self.arrangement_info_text_var = tk.StringVar()
        self.arrangement_info_text_var.set("")

        arrangement_info_text = tk.Label(arrangement_info_frame, textvariable=self.arrangement_info_text_var,
                                         font=("Arial", 10))
        arrangement_info_text.pack()

        # text_btn = tk.Button(arrangement_info_frame, text="测试更新排布文本", command=self.update_arrangement_info_text)
        # text_btn.pack(fill=tk.X, pady=(0, 20))

        # “组件排布”文字标签放置在右侧区域的顶部
        arrangement_text = tk.Label(arrangement_frame, text="组件排布", font=("Arial", 12))
        arrangement_text.pack()

        self.arrangement_canvas = tk.Canvas(arrangement_frame, width=frame_width, height=frame_height, bg='black')
        self.arrangement_canvas.pack()

        # “原始拓扑”文字标签放置在右侧区域的顶部
        arrangement_btn_text = tk.Label(arrangement_frame, text="点击按钮查看对应排序的结果：", font=("Arial", 12))
        arrangement_btn_text.pack(side=tk.LEFT, anchor=tk.SW, padx=(0, 5), pady=(5, 0))

        # 界面切换按钮
        self.arrangement_btns = []
        for i in range(const.const.outputPlacementCount):
            arrangement_btn = tk.Button(arrangement_frame, text=f"{i + 1}", command=partial(self.display_layout, i))
            arrangement_btn.pack(side=tk.LEFT, anchor=tk.SW, padx=(0, 5), pady=(5, 0))
            arrangement_btn.config(state="disabled")
            self.arrangement_btns.append(arrangement_btn)

        # 创建右侧的区域，包括“原始拓扑”文字标签和图片显示区域
        roofscene_frame = tk.Frame(self.root)
        roofscene_frame.pack(side=tk.RIGHT, padx=20, pady=20)
        # “原始拓扑”文字标签放置在右侧区域的顶部
        roofscene_text = tk.Label(roofscene_frame, text="屋面场景", font=("Arial", 12))
        roofscene_text.pack()

        self.roofscene_canvas = tk.Canvas(roofscene_frame, width=frame_width, height=frame_height, bg='black')
        self.roofscene_canvas.pack()

        # “原始拓扑”文字标签放置在右侧区域的顶部
        roofscene_btn_text = tk.Label(roofscene_frame, text="选择输入示例：", font=("Arial", 12))
        roofscene_btn_text.pack(side=tk.LEFT, anchor=tk.SW, padx=(0, 5), pady=(5, 0))

        # 界面切换按钮
        self.roofscene_btns = []
        for i in range(21):
            roofscene_btn = tk.Button(roofscene_frame, text=f"{i + 1}", command=partial(self.get_demo_input, i))
            roofscene_btn.pack(side=tk.LEFT, anchor=tk.SW, padx=(0, 5), pady=(5, 0))
            if os.path.exists(os.path.join(file_dir, f"input{i}.json")):
                roofscene_btn.config(state="active")
            else:
                roofscene_btn.config(state="disabled")
            self.roofscene_btns.append(roofscene_btn)

    def run(self):
        self.root.mainloop()

    def open_location_window(self, str_text, option_text, options, bool_text):
        location_window = tk.Toplevel(self.root)
        location_window.title("添加位置信息")

        # str_text = ["省份", "城市", "行政区", "经度", "纬度", "电压等级", "距离并网点的距离"]
        # str_text = ["经度", "纬度"]
        str_entries = {}
        for i, text in enumerate(str_text):
            label = tk.Label(location_window, text=text + ": ")
            label.grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(location_window)
            entry.grid(row=i, column=1, padx=5, pady=5)
            str_entries[text] = entry
        # Frame for installation scheme selection
        # option_text = ["风压", "雪压", "风雪压"]
        # option_text = []
        # options = [["低压", "高压"], ["低压", "高压"], ["低压", "高压"]]
        option_entries = {}
        for i, (text, option) in enumerate(zip(option_text, options)):
            label = tk.Label(location_window, text=text)
            label.grid(row=len(str_entries) + i, column=0, padx=5, pady=5)
            scheme_var = tk.StringVar(location_window)
            scheme_var.set(option[0])
            scheme_menu = tk.OptionMenu(location_window, scheme_var, *option, )
            scheme_menu.config(width=5)
            scheme_menu.grid(row=len(str_entries) + i, column=1, padx=5, pady=5)
            option_entries[text] = scheme_var
        # bool_text = ["大雪"]
        # bool_text = []
        bool_entries = {}
        for i, text in enumerate(bool_text):
            label = tk.Label(location_window, text=text)
            label.grid(row=len(str_entries) + len(option_entries) + i, column=0, padx=5, pady=5)
            bool_var = tk.BooleanVar()
            bool_checkbox = tk.Checkbutton(location_window, variable=bool_var)
            bool_checkbox.grid(row=len(str_entries) + len(option_entries) + i, column=1, padx=5, pady=5)
            bool_entries[text] = bool_var
        # 创建按钮，用于获取所有输入的数据
        submit_btn = tk.Button(location_window, text="提交",
                               command=lambda: self.get_location_data(location_window, str_entries, option_entries,
                                                                      bool_entries))
        submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2,
                        padx=5,
                        pady=5)

    def get_location_data(self, window, str_entries, option_entries, bool_entries):
        for text, entry in str_entries.items():
            input_str = entry.get()
            self.location_info[chn2eng[text]] = float(input_str) if input_str.replace('.', '',
                                                                                      1).isdigit() else input_str
        for text, entry in option_entries.items():
            # print(text + ": ", entry.get())
            self.location_info[chn2eng[text]] = entry.get()
        for text, entry in bool_entries.items():
            # print(text + ": ", entry.get())
            self.location_info[chn2eng[text]] = entry.get()
        window.destroy()

    def open_roof_window(self, str_text, option_text, options, bool_text):
        global str_components, str_entries, vertex_components, vertex_entries, len_option_bool, submit_btn

        roof_window = tk.Toplevel(self.root)
        roof_window.title("添加屋顶信息")
        # roof_window.geometry("250x200")
        str_components = []
        str_entries = {}
        vertex_components = []
        vertex_entries = {}
        option_entries = {}
        bool_entries = {}
        len_option_bool = 0

        def create_input_options_for_irregular_roof(roof_window, value):
            global str_components, str_entries, len_option_bool, submit_btn
            roof_options = {
                "矩形": ["A", "B", "height"],
                "上凸形": ["A", "B", "C", "D", "E", "F", "height"],
                "下凸形": ["A", "B", "C", "D", "E", "F", "height"],
                "左凸形": ["A", "B", "C", "D", "E", "F", "height"],
                "右凸形": ["A", "B", "C", "D", "E", "F", "height"],
                "上凹形": ["A", "B", "C", "D", "E", "F", "height"],
                "下凹形": ["A", "B", "C", "D", "E", "F", "height"],
                "左凹形": ["A", "B", "C", "D", "E", "F", "height"],
                "右凹形": ["A", "B", "C", "D", "E", "F", "height"],
                "正7形": ["A", "B", "C", "D", "height"],
                "反7形": ["A", "B", "C", "D", "height"],
                "正L形": ["A", "B", "C", "D", "height"],
                "反L形": ["A", "B", "C", "D", "height"],
                "自定义多边形": ["顶点数量"],
                "屋顶图片输入": ["图片路径", "图片分辨率"]
            }

            # 斜屋顶
            # roof_options = {
            #     "矩形": ["A", "B","height","roofDirection","roofAngle"],
            #     "上凸形": ["A", "B", "C", "D", "E", "F","height","roofDirection","roofAngle"],
            #     "下凸形": ["A", "B", "C", "D", "E", "F","height","roofDirection","roofAngle"],
            #     "左凸形": ["A", "B", "C", "D", "E", "F","height","roofDirection","roofAngle"],
            #     "右凸形": ["A", "B", "C", "D", "E", "F","height","roofDirection","roofAngle"],
            #     "上凹形": ["A", "B", "C", "D", "E", "F","height","roofDirection","roofAngle"],
            #     "下凹形": ["A", "B", "C", "D", "E", "F","height","roofDirection","roofAngle"],
            #     "左凹形": ["A", "B", "C", "D", "E", "F","height","roofDirection","roofAngle"],
            #     "右凹形": ["A", "B", "C", "D", "E", "F","height","roofDirection","roofAngle"],
            #     "正7形": ["A", "B", "C", "D","height","roofDirection","roofAngle"],
            #     "反7形": ["A", "B", "C", "D","height","roofDirection","roofAngle"],
            #     "正L形": ["A", "B", "C", "D","height","roofDirection","roofAngle"],
            #     "反L形": ["A", "B", "C", "D","height","roofDirection","roofAngle"]
            # }

            def create_vertex_entries(event):
                global vertex_components, vertex_entries
                num_vertices = int(custom_polygon_vertices_entry.get())
                if num_vertices > max_custom_vertex_in_irregular_roof:
                    print(f"自定义屋面顶点数量过大,当前上限为{max_custom_vertex_in_irregular_roof}")
                    return
                remove_vertex_components()
                for i in range(num_vertices):
                    x_label = tk.Label(roof_window, text=f"顶点{i + 1} X:")
                    x_label.grid(row=len_option_bool + i + 1, column=0, padx=5, pady=5)
                    x_entry = tk.Entry(roof_window)
                    x_entry.grid(row=len_option_bool + i + 1, column=1, padx=5, pady=5)
                    y_label = tk.Label(roof_window, text=f"顶点{i + 1} Y:")
                    y_label.grid(row=len_option_bool + i + 1, column=2, padx=5, pady=5)
                    y_entry = tk.Entry(roof_window)
                    y_entry.grid(row=len_option_bool + i + 1, column=3, padx=5, pady=5)
                    vertex_components.append(x_label)
                    vertex_components.append(x_entry)
                    vertex_components.append(y_label)
                    vertex_components.append(y_entry)
                    vertex_entries[f"自定义{i}顶点的X坐标"] = x_entry
                    vertex_entries[f"自定义{i}顶点的Y坐标"] = y_entry
                submit_btn.grid(row=len(str_entries) + len(vertex_entries) + len_option_bool + 1, column=0,
                                columnspan=2,
                                padx=5,
                                pady=5)

            def remove_vertex_components():
                global vertex_components, vertex_entries
                for component in vertex_components:
                    component.grid_forget()
                vertex_components = []
                vertex_entries = {}

            # 打开文件对话框函数
            def browse_file():
                file_path = filedialog.askopenfilename()
                if file_path:
                    str_entries["图片路径"].delete(0, tk.END)
                    str_entries["图片路径"].insert(0, file_path)

            if value not in roof_options:
                return
            for component in str_components:
                component.grid_forget()
            str_components = []
            str_entries = {}
            remove_vertex_components()
            # str_names = [text + "边（mm）" for text in roof_options[value]] + ["高度（mm）"]
            if value == "自定义多边形":
                custom_polygon_vertices_label = tk.Label(roof_window, text="顶点数量:")
                custom_polygon_vertices_label.grid(row=len_option_bool, column=0, padx=5, pady=5)
                custom_polygon_vertices_entry = tk.Entry(roof_window)
                custom_polygon_vertices_entry.grid(row=len_option_bool, column=1, padx=5, pady=5)
                str_components.append(custom_polygon_vertices_label)
                str_components.append(custom_polygon_vertices_entry)
                str_entries["顶点数量"] = custom_polygon_vertices_entry
                custom_polygon_vertices_entry.bind('<KeyRelease>', create_vertex_entries)
            elif value == "屋顶图片输入":
                img_path_label = tk.Label(roof_window, text="图片路径:")
                img_path_label.grid(row=len_option_bool, column=0, padx=5, pady=5)

                img_path_entry = tk.Entry(roof_window)
                img_path_entry.grid(row=len_option_bool, column=1, padx=5, pady=5)

                browse_button = tk.Button(roof_window, text="...", command=browse_file)
                browse_button.grid(row=len_option_bool, column=2, padx=5, pady=5)

                str_components.append(img_path_label)
                str_components.append(img_path_entry)
                str_components.append(browse_button)  # 添加按钮到组件列表中

                str_entries["图片路径"] = img_path_entry
                # 添加图片分辨率输入框及其标签
                resolution_label = tk.Label(roof_window, text="图片分辨率:")
                resolution_label.grid(row=len_option_bool + 1, column=0, padx=5, pady=5)

                resolution_entry = tk.Entry(roof_window)
                resolution_entry.grid(row=len_option_bool + 1, column=1, padx=5, pady=5)

                resolution_unit_label = tk.Label(roof_window, text="厘米/像素")
                resolution_unit_label.grid(row=len_option_bool + 1, column=2, padx=5, pady=5)

                str_components.append(resolution_label)
                str_components.append(resolution_entry)
                str_components.append(resolution_unit_label)  # 添加分辨率相关组件到列表中

                str_entries["图片分辨率"] = resolution_entry
            else:
                str_names = [eng2chn[text] for text in roof_options[value]]
                for i, text in enumerate(str_names):
                    label = tk.Label(roof_window, text=text + ": ")
                    label.grid(row=len_option_bool + i, column=0, padx=5, pady=5)
                    entry = tk.Entry(roof_window)
                    entry.grid(row=len_option_bool + i, column=1, padx=5, pady=5)
                    str_entries[text] = entry
                    str_components.append(label)
                    str_components.append(entry)
                submit_btn.grid(row=len(str_entries) + len_option_bool + 1, column=0, columnspan=2,
                                padx=5, pady=5)

        for i, (text, option) in enumerate(zip(option_text, options)):
            label = tk.Label(roof_window, text=text)
            label.grid(row=i, column=0, padx=5, pady=5)
            scheme_var = tk.StringVar(roof_window)
            scheme_var.set(option[0])
            if text == "屋面类型":
                # 绑定触发函数到 <<MenuSelect>> 事件
                update_roof_type_func = partial(create_input_options_for_irregular_roof, roof_window)
                scheme_menu = tk.OptionMenu(roof_window, scheme_var, *option, command=update_roof_type_func)
            else:
                scheme_menu = tk.OptionMenu(roof_window, scheme_var, *option, )
            scheme_menu.config(width=10)
            scheme_menu.grid(row=i, column=1, padx=5, pady=5)
            option_entries[text] = scheme_var

        for i, text in enumerate(bool_text):
            label = tk.Label(roof_window, text=text)
            label.grid(row=len(option_entries) + i, column=0, padx=5, pady=5)
            bool_var = tk.BooleanVar()
            bool_checkbox = tk.Checkbutton(roof_window, variable=bool_var)
            bool_checkbox.grid(row=len(option_entries) + i, column=1, padx=5, pady=5)
            bool_entries[text] = bool_var

        for i, text in enumerate(str_text):
            label = tk.Label(roof_window, text=text + ": ")
            label.grid(row=len(option_entries) + len(bool_entries) + i, column=0, padx=5, pady=5)
            entry = tk.Entry(roof_window)
            entry.grid(row=len(option_entries) + len(bool_entries) + i, column=1, padx=5, pady=5)
            str_entries[text] = entry
            str_components.append(label)
            str_components.append(entry)

        len_option_bool = len(option_entries) + len(bool_entries)
        # 创建按钮，用于获取所有输入的数据
        submit_btn = tk.Button(roof_window, text="提交",
                               command=lambda: self.get_roof_data(roof_window, str_entries, option_entries,
                                                                  bool_entries, vertex_entries))
        submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2,
                        padx=5, pady=5)

    def get_roof_data(self, window, str_entries, option_entries, bool_entries, vertex_entries):
        for text, entry in str_entries.items():
            input_str = entry.get()
            # 判断input_str是否是浮点数
            if "." in input_str and input_str.replace('.', '', 1).isdigit():
                self.roof_info[chn2eng[text]] = float(input_str)
            else:
                self.roof_info[chn2eng[text]] = int(input_str) if input_str.replace('.', '', 1).isdigit() else input_str
        for text, entry in option_entries.items():
            # print(text + ": ", entry.get())
            self.roof_info[chn2eng[text]] = entry.get()
        for text, entry in bool_entries.items():
            # print(text + ": ", entry.get())
            self.roof_info[chn2eng[text]] = entry.get()
        # 屋顶类型
        if self.roof_info["roofSurfaceCategory"] == "自定义多边形":
            for text, entry in vertex_entries.items():
                input_str = entry.get()
                self.roof_info[chn2eng[text]] = int(input_str) if input_str.replace('.', '', 1).isdigit() else input_str
            self.adjust_irregular_roof_vertices()
        window.destroy()

    def open_obstacle_window(self, str_text, option_text, options, bool_text):
        obstacle_window = tk.Toplevel(self.root)
        obstacle_window.title("添加屋内障碍物信息")
        # 直径？长度（mm）？
        # str_text = ["ID", "直径", "长度（mm）", "宽度（mm）", "高度（mm）", "距离西侧屋顶距离", "距离北侧屋顶距离",
        #             "可调整高度（mm）"]
        # str_text = ["ID", "直径", "长度（mm）", "宽度（mm）", "高度（mm）", "距离西侧屋顶距离", "距离北侧屋顶距离"]
        str_entries = {}
        for i, text in enumerate(str_text):
            label = tk.Label(obstacle_window, text=text + ": ")
            label.grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(obstacle_window)
            entry.grid(row=i, column=1, padx=5, pady=5)
            str_entries[text] = entry
        # Frame for installation scheme selection
        # option_text = ["类型"]
        # options = [["无烟烟囱", "有烟烟囱"]]
        option_entries = {}
        for i, (text, option) in enumerate(zip(option_text, options)):
            label = tk.Label(obstacle_window, text=text)
            label.grid(row=len(str_entries) + i, column=0, padx=5, pady=5)
            scheme_var = tk.StringVar(obstacle_window)
            scheme_var.set(option[0])
            scheme_menu = tk.OptionMenu(obstacle_window, scheme_var, *option, )
            scheme_menu.config(width=5)
            scheme_menu.grid(row=len(str_entries) + i, column=1, padx=5, pady=5)
            option_entries[text] = scheme_var
        # bool_text = ["是否圆形", "是否可移除"]
        bool_entries = {}
        for i, text in enumerate(bool_text):
            label = tk.Label(obstacle_window, text=text)
            label.grid(row=len(str_entries) + len(option_entries) + i, column=0, padx=5, pady=5)
            bool_var = tk.BooleanVar()
            bool_checkbox = tk.Checkbutton(obstacle_window, variable=bool_var)
            bool_checkbox.grid(row=len(str_entries) + len(option_entries) + i, column=1, padx=5, pady=5)
            bool_entries[text] = bool_var
        # 创建按钮，用于获取所有输入的数据
        submit_btn = tk.Button(obstacle_window, text="提交",
                               command=lambda: self.get_obstacle_data(obstacle_window, str_entries, option_entries,
                                                                      bool_entries))
        submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2,
                        padx=5,
                        pady=5)

    def get_obstacle_data(self, window, str_entries, option_entries, bool_entries):
        new_obstacle = {}
        for text, entry in str_entries.items():
            input_str = entry.get()
            new_obstacle[chn2eng[text]] = int(input_str) if input_str.replace('.', '', 1).isdigit() else input_str
        for text, entry in option_entries.items():
            # print(text + ": ", entry.get())
            new_obstacle[chn2eng[text]] = entry.get()
        for text, entry in bool_entries.items():
            # print(text + ": ", entry.get())
            new_obstacle[chn2eng[text]] = entry.get()
        self.obstacle_info.append(new_obstacle)
        window.destroy()

    def open_outside_obstacle_window(self, str_text, option_text, options, bool_text):
        outside_obstacle_window = tk.Toplevel(self.root)
        outside_obstacle_window.title("添加屋外障碍物信息")
        # 直径？长度（mm）？
        # str_text = ["ID", "直径", "长度（mm）", "宽度（mm）", "高度（mm）", "距离西侧屋顶距离", "距离北侧屋顶距离",
        #             "可调整高度（mm）"]
        str_entries = {}
        for i, text in enumerate(str_text):
            label = tk.Label(outside_obstacle_window, text=text + ": ")
            label.grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(outside_obstacle_window)
            entry.grid(row=i, column=1, padx=5, pady=5)
            str_entries[text] = entry
        # Frame for installation scheme selection
        # option_text = ["类型"]
        # options = [["房屋", "树"]]
        option_entries = {}
        for i, (text, option) in enumerate(zip(option_text, options)):
            label = tk.Label(outside_obstacle_window, text=text)
            label.grid(row=len(str_entries) + i, column=0, padx=5, pady=5)
            scheme_var = tk.StringVar(outside_obstacle_window)
            scheme_var.set(option[0])
            scheme_menu = tk.OptionMenu(outside_obstacle_window, scheme_var, *option, )
            scheme_menu.config(width=5)
            scheme_menu.grid(row=len(str_entries) + i, column=1, padx=5, pady=5)
            option_entries[text] = scheme_var
        # bool_text = ["是否圆形", "是否可移除"]
        bool_entries = {}
        for i, text in enumerate(bool_text):
            label = tk.Label(outside_obstacle_window, text=text)
            label.grid(row=len(str_entries) + len(option_entries) + i, column=0, padx=5, pady=5)
            bool_var = tk.BooleanVar()
            bool_checkbox = tk.Checkbutton(outside_obstacle_window, variable=bool_var)
            bool_checkbox.grid(row=len(str_entries) + len(option_entries) + i, column=1, padx=5, pady=5)
            bool_entries[text] = bool_var
        # 创建按钮，用于获取所有输入的数据
        submit_btn = tk.Button(outside_obstacle_window, text="提交",
                               command=lambda: self.get_outside_obstacle_window_data(outside_obstacle_window,
                                                                                     str_entries,
                                                                                     option_entries, bool_entries))
        submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2,
                        padx=5,
                        pady=5)

    def get_outside_obstacle_window_data(self, window, str_entries, option_entries, bool_entries):
        new_obstacle = {}
        for text, entry in str_entries.items():
            input_str = entry.get()
            new_obstacle[chn2eng[text]] = int(input_str) if input_str.replace('.', '', 1).isdigit() else input_str
        for text, entry in option_entries.items():
            # print(text + ": ", entry.get())
            new_obstacle[chn2eng[text]] = entry.get()
        for text, entry in bool_entries.items():
            # print(text + ": ", entry.get())
            new_obstacle[chn2eng[text]] = entry.get()
        self.outside_obstacle_info.append(new_obstacle)
        window.destroy()

    def open_panel_window(self, str_text, option_text, options, bool_text):
        panel_window = tk.Toplevel(self.root)
        panel_window.title("添加光伏板信息")

        # 直径？长度（mm）？
        # str_text = ["功率", "厚度"]
        str_entries = {}
        for i, text in enumerate(str_text):
            label = tk.Label(panel_window, text=text + ": ")
            label.grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(panel_window)
            entry.grid(row=i, column=1, padx=5, pady=5)
            str_entries[text] = entry
        # Frame for installation scheme selection
        # option_text = ["组件类型"]
        # options = [["182-78"]]
        option_entries = {}
        for i, (text, option) in enumerate(zip(option_text, options)):
            label = tk.Label(panel_window, text=text)
            label.grid(row=len(str_entries) + i, column=0, padx=5, pady=5)
            scheme_var = tk.StringVar(panel_window)
            scheme_var.set(option[0])
            scheme_menu = tk.OptionMenu(panel_window, scheme_var, *option, )
            scheme_menu.config(width=5)
            scheme_menu.grid(row=len(str_entries) + i, column=1, padx=5, pady=5)
            option_entries[text] = scheme_var
        # bool_text = []
        bool_entries = {}
        for i, text in enumerate(bool_text):
            label = tk.Label(panel_window, text=text)
            label.grid(row=len(str_entries) + len(option_entries) + i, column=0, padx=5, pady=5)
            bool_var = tk.BooleanVar()
            bool_checkbox = tk.Checkbutton(panel_window, variable=bool_var)
            bool_checkbox.grid(row=len(str_entries) + len(option_entries) + i, column=1, padx=5, pady=5)
            bool_entries[text] = bool_var
        # 创建按钮，用于获取所有输入的数据
        submit_btn = tk.Button(panel_window, text="提交",
                               command=lambda: self.get_panel_data(panel_window, str_entries, option_entries,
                                                                   bool_entries))
        submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2,
                        padx=5,
                        pady=5)

    def get_panel_data(self, window, str_entries, option_entries, bool_entries):
        for text, entry in str_entries.items():
            input_str = entry.get()
            self.panel_info[chn2eng[text]] = int(input_str) if input_str.replace('.', '', 1).isdigit() else input_str
        for text, entry in option_entries.items():
            # print(text + ": ", entry.get())
            self.panel_info[chn2eng[text]] = entry.get()
        for text, entry in bool_entries.items():
            # print(text + ": ", entry.get())
            self.panel_info[chn2eng[text]] = entry.get()
        window.destroy()

    def open_algorithm_window(self, str_text, option_text, options, bool_text):
        algorithm_window = tk.Toplevel(self.root)
        algorithm_window.title("选择算法类型")

        # 直径？长度（mm）？
        # str_text = ["精度（mm）"]
        str_entries = {}
        for i, text in enumerate(str_text):
            label = tk.Label(algorithm_window, text=text + ": ")
            label.grid(row=i, column=0, padx=5, pady=5)
            entry = tk.Entry(algorithm_window)
            entry.grid(row=i, column=1, padx=5, pady=5)
            str_entries[text] = entry
        # Frame for installation scheme selection
        # option_text = ["算法类型"]
        # options = [["贪心（单阵列）", "DFS（多阵列）"]]
        option_entries = {}
        for i, (text, option) in enumerate(zip(option_text, options)):
            label = tk.Label(algorithm_window, text=text)
            label.grid(row=len(str_entries) + i, column=0, padx=5, pady=5)
            scheme_var = tk.StringVar(algorithm_window)
            scheme_var.set(option[0])
            scheme_menu = tk.OptionMenu(algorithm_window, scheme_var, *option, )
            scheme_menu.config(width=12)
            scheme_menu.grid(row=len(str_entries) + i, column=1, padx=5, pady=5)
            option_entries[text] = scheme_var
        # bool_text = []
        bool_entries = {}
        for i, text in enumerate(bool_text):
            label = tk.Label(algorithm_window, text=text)
            label.grid(row=len(str_entries) + len(option_entries) + i, column=0, padx=5, pady=5)
            bool_var = tk.BooleanVar()
            bool_checkbox = tk.Checkbutton(algorithm_window, variable=bool_var)
            bool_checkbox.grid(row=len(str_entries) + len(option_entries) + i, column=1, padx=5, pady=5)
            bool_entries[text] = bool_var
        # 创建按钮，用于获取所有输入的数据
        submit_btn = tk.Button(algorithm_window, text="提交",
                               command=lambda: self.get_algorithm_data(algorithm_window, str_entries, option_entries,
                                                                       bool_entries))
        submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2,
                        padx=5,
                        pady=5)

    def get_algorithm_data(self, window, str_entries, option_entries, bool_entries):
        for text, entry in str_entries.items():
            input_str = entry.get()
            self.algorithm_info[chn2eng[text]] = int(input_str) if input_str.replace('.', '',
                                                                                     1).isdigit() else input_str
        for text, entry in option_entries.items():
            # print(text + ": ", entry.get())
            self.algorithm_info[chn2eng[text]] = entry.get()
        for text, entry in bool_entries.items():
            # print(text + ": ", entry.get())
            self.algorithm_info[chn2eng[text]] = entry.get()
        window.destroy()

    def clear_canvas(self):
        self.roofscene_canvas.delete("all")

    def draw_roofscene(self):
        half_int = lambda x, y: int(x + y) / 2
        get_distance = lambda x, y: sqrt(square(x[0] - y[0]) + square(x[1] - y[1]))
        self.clear_canvas()

        def get_furthest_outside_obstacle_distance():
            res = [0, 0, 0, 0]
            for obstacle in self.outside_obstacle_info:
                centerX = float(obstacle['relativePositionX'])  # 可以是负数
                centerY = float(obstacle['relativePositionY'])  # 可以是负数
                x1, x2, y1, y2 = 0, 0, 0, 0
                if obstacle['isRound']:
                    # continue
                    length = float(obstacle['diameter']) / 2
                    x1 = centerX - length
                    x2 = centerX + length
                    y1 = centerY - length
                    y2 = centerY + length
                else:
                    width = float(obstacle['width'])
                    length = float(obstacle['length'])
                    x1 = centerX
                    y1 = centerY
                    x2 = centerX + width
                    y2 = centerY + length
                res[0] = min(res[0], x1)
                res[1] = min(res[1], y1)
                res[2] = max(res[2], x2)
                res[3] = max(res[3], y2)
            return res

        def get_scale_and_roofTopLeft(roof_width, roof_height):
            scaleX = 1.0
            scaleY = 1.0
            if outside_furthest_distance[2] > 0:
                scaleX = draw_width / float(outside_extension_x)
            else:
                scaleX = draw_width / float(roof_width + outside_extension_x)
            if outside_furthest_distance[3] > 0:
                scaleY = draw_height / float(outside_extension_y)
            else:
                scaleY = draw_height / float(roof_height + outside_extension_y)

            scale = min(scaleX, scaleY)
            # 没有屋外障碍物，屋顶居中
            if outside_extension_x == 0 and outside_extension_y == 0:
                roof_left = (frame_width - roof_width * scale) / 2
                roof_top = (frame_height - roof_height * scale) / 2
            # 存在屋外障碍物，屋顶不要求居中
            else:
                roof_left = draw_gap + abs(outside_furthest_distance[0]) * scale
                roof_top = draw_gap + abs(outside_furthest_distance[1]) * scale
            return scale, roof_left, roof_top

        outside_furthest_distance = get_furthest_outside_obstacle_distance()
        outside_extension_x = abs(outside_furthest_distance[0]) + outside_furthest_distance[2]
        outside_extension_y = abs(outside_furthest_distance[1]) + outside_furthest_distance[3]
        draw_width = frame_width - draw_gap * 2
        draw_height = frame_height - draw_gap * 2

        roofSurfaceCategory = self.roof_info.get('roofSurfaceCategory', "矩形")
        scale = 1.0
        roof_left = 0
        roof_top = 0
        if roofSurfaceCategory == "矩形":  # 绘制矩形屋顶
            scale, roof_left, roof_top = get_scale_and_roofTopLeft(self.roof_info['B'], self.roof_info['A'])
            scaled_width = float(self.roof_info['B']) * scale
            scaled_height = float(self.roof_info['A']) * scale
            roof_right = roof_left + scaled_width
            roof_bottom = roof_top + scaled_height
            # 在 Canvas 上绘制缩放后的矩形
            self.roofscene_canvas.create_rectangle(roof_left, roof_top, roof_right, roof_bottom,
                                                   outline=roof_outline_color,
                                                   tags="roof")
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(half_int(roof_left, roof_right), roof_top,
                                              text=f"{self.roof_info['B']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(roof_left, half_int(roof_top, roof_bottom),
                                              text=f"{self.roof_info['A']}",
                                              font=("Arial", 12),
                                              fill=text_color)
        elif roofSurfaceCategory == "上凸形":
            self.roof_info['G'] = self.roof_info['A'] + self.roof_info['C'] - self.roof_info['E']
            self.roof_info['H'] = self.roof_info['B'] + self.roof_info['D'] + self.roof_info['F']
            AC_height = self.roof_info['A'] + self.roof_info['C']

            scale, roof_left, roof_top = get_scale_and_roofTopLeft(self.roof_info['H'], AC_height)
            # scale = min(draw_width / float(self.roof_info['H']), draw_height / float(AC_height))

            p1 = [roof_left, (frame_height + AC_height * scale) / 2]  # point between AH
            p0 = [p1[0], p1[1] - self.roof_info['A'] * scale]  # point between AB
            p2 = [p0[0] + self.roof_info['H'] * scale, p1[1]]  # HG
            p3 = [p2[0], p2[1] - self.roof_info['G'] * scale]  # FG
            p4 = [p3[0] - self.roof_info['F'] * scale, p3[1]]  # EF
            p5 = [p4[0], p4[1] - self.roof_info['E'] * scale]  # DE
            p6 = [p5[0] - self.roof_info['D'] * scale, p5[1]]  # CD
            p7 = [p6[0], p0[1]]  # BC

            self.roofscene_canvas.create_polygon([p0, p1, p2, p3, p4, p5, p6, p7], outline=roof_outline_color)
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(p0[0], half_int(p0[1], p1[1]),
                                              text=f"{self.roof_info['A']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p0[0], p7[0]), p7[1],
                                              text=f"{self.roof_info['B']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p6[0], half_int(p6[1], p7[1]),
                                              text=f"{self.roof_info['C']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p5[0], p6[0]), p5[1],
                                              text=f"{self.roof_info['D']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p4[0], half_int(p4[1], p5[1]),
                                              text=f"{self.roof_info['E']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p3[0], p4[0]), p4[1],
                                              text=f"{self.roof_info['F']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p2[0], half_int(p2[1], p3[1]),
                                              text=f"{self.roof_info['G']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p1[0], p2[0]), p1[1],
                                              text=f"{self.roof_info['H']}",
                                              font=("Arial", 12),
                                              fill=text_color)
        elif roofSurfaceCategory == "下凸形":
            self.roof_info['G'] = self.roof_info['A'] + self.roof_info['C'] - self.roof_info['E']
            self.roof_info['H'] = self.roof_info['D'] - self.roof_info['B'] - self.roof_info['F']
            AC_height = self.roof_info['A'] + self.roof_info['C']
            scale, roof_left, roof_top = get_scale_and_roofTopLeft(self.roof_info['D'], AC_height)
            # scale = min(draw_width / float(self.roof_info['D']), draw_height / float(AC_height))

            p0 = [roof_left, roof_top]  # CD
            p1 = [p0[0], p0[1] + self.roof_info['C'] * scale]  # BC
            p2 = [p1[0] + self.roof_info['B'] * scale, p1[1]]  # AB
            p3 = [p2[0], p2[1] + self.roof_info['A'] * scale]  # AH
            p4 = [p3[0] + self.roof_info['H'] * scale, p3[1]]  # HG
            p5 = [p4[0], p4[1] - self.roof_info['G'] * scale]  # FG
            p6 = [p5[0] + self.roof_info['F'] * scale, p5[1]]  # EF
            p7 = [p6[0], p6[1] - self.roof_info['E'] * scale]  # DE

            self.roofscene_canvas.create_polygon([p0, p1, p2, p3, p4, p5, p6, p7], outline=roof_outline_color)
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(p0[0], half_int(p0[1], p1[1]),
                                              text=f"{self.roof_info['C']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p1[0], p2[0]), p1[1],
                                              text=f"{self.roof_info['B']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p2[0], half_int(p2[1], p3[1]),
                                              text=f"{self.roof_info['A']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p3[0], p4[0]), p3[1],
                                              text=f"{self.roof_info['H']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p4[0], half_int(p4[1], p5[1]),
                                              text=f"{self.roof_info['G']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p5[0], p6[0]), p6[1],
                                              text=f"{self.roof_info['F']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p6[0], half_int(p6[1], p7[1]),
                                              text=f"{self.roof_info['E']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p0[0], p7[0]), p0[1],
                                              text=f"{self.roof_info['D']}",
                                              font=("Arial", 12),
                                              fill=text_color)
        elif roofSurfaceCategory == "左凸形":
            self.roof_info['G'] = self.roof_info['A'] + self.roof_info['C'] + self.roof_info['E']
            self.roof_info['H'] = self.roof_info['D'] - self.roof_info['B'] + self.roof_info['F']
            DF_width = self.roof_info['D'] + self.roof_info['F']

            scale, roof_left, roof_top = get_scale_and_roofTopLeft(DF_width, self.roof_info['G'])
            # scale = min(draw_width / float(DF_width), draw_height / float(self.roof_info['G']))
            p0 = [roof_left, roof_top + self.roof_info['E'] * scale]  # CD
            p1 = [p0[0], p0[1] + self.roof_info['C'] * scale]  # BC
            p2 = [p1[0] + self.roof_info['B'] * scale, p1[1]]  # AB
            p3 = [p2[0], p2[1] + self.roof_info['A'] * scale]  # AH
            p4 = [p3[0] + self.roof_info['H'] * scale, p3[1]]  # HG
            p5 = [p4[0], roof_top]  # FG
            p6 = [p5[0] - self.roof_info['F'] * scale, p5[1]]  # EF
            p7 = [p6[0], p0[1]]  # DE

            self.roofscene_canvas.create_polygon([p0, p1, p2, p3, p4, p5, p6, p7], outline=roof_outline_color)
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(p0[0], half_int(p0[1], p1[1]),
                                              text=f"{self.roof_info['C']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p1[0], p2[0]), p1[1],
                                              text=f"{self.roof_info['B']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p2[0], half_int(p2[1], p3[1]),
                                              text=f"{self.roof_info['A']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p3[0], p4[0]), p3[1],
                                              text=f"{self.roof_info['H']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p4[0], half_int(p4[1], p5[1]),
                                              text=f"{self.roof_info['G']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p5[0], p6[0]), p6[1],
                                              text=f"{self.roof_info['F']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p6[0], half_int(p6[1], p7[1]),
                                              text=f"{self.roof_info['E']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p0[0], p7[0]), p0[1],
                                              text=f"{self.roof_info['D']}",
                                              font=("Arial", 12),
                                              fill=text_color)
        elif roofSurfaceCategory == "右凸形":
            self.roof_info['G'] = self.roof_info['A'] - self.roof_info['C'] - self.roof_info['E']
            self.roof_info['H'] = self.roof_info['D'] + self.roof_info['B'] - self.roof_info['F']
            BD_width = self.roof_info['D'] + self.roof_info['B']

            scale, roof_left, roof_top = get_scale_and_roofTopLeft(BD_width, self.roof_info['A'])
            # scale = min(draw_width / float(BD_width), draw_height / float(self.roof_info['A']))
            # roof_left = (frame_width - BD_width * scale) / 2
            # roof_top = (frame_height - self.roof_info['A'] * scale) / 2

            p0 = [roof_left, roof_top]  # AB
            p1 = [p0[0], p0[1] + self.roof_info['A'] * scale]  # AH
            p2 = [p1[0] + self.roof_info['H'] * scale, p1[1]]  # HG
            p3 = [p2[0], p2[1] - self.roof_info['G'] * scale]  # FG
            p4 = [p3[0] + self.roof_info['F'] * scale, p3[1]]  # EF
            p5 = [p4[0], p4[1] - self.roof_info['E'] * scale]  # DE
            p6 = [p5[0] - self.roof_info['D'] * scale, p5[1]]  # CD
            p7 = [p6[0], p0[1]]  # BC

            self.roofscene_canvas.create_polygon([p0, p1, p2, p3, p4, p5, p6, p7], outline=roof_outline_color)
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(p0[0], half_int(p0[1], p1[1]),
                                              text=f"{self.roof_info['A']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p1[0], p2[0]), p1[1],
                                              text=f"{self.roof_info['H']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p2[0], half_int(p2[1], p3[1]),
                                              text=f"{self.roof_info['G']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p3[0], p4[0]), p3[1],
                                              text=f"{self.roof_info['F']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p4[0], half_int(p4[1], p5[1]),
                                              text=f"{self.roof_info['E']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p5[0], p6[0]), p6[1],
                                              text=f"{self.roof_info['D']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p6[0], half_int(p6[1], p7[1]),
                                              text=f"{self.roof_info['C']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p0[0], p7[0]), p0[1],
                                              text=f"{self.roof_info['B']}",
                                              font=("Arial", 12),
                                              fill=text_color)
        elif roofSurfaceCategory == "上凹形":
            self.roof_info['G'] = self.roof_info['A'] - self.roof_info['C'] + self.roof_info['E']
            self.roof_info['H'] = self.roof_info['D'] + self.roof_info['B'] + self.roof_info['F']
            max_height = max(self.roof_info['A'], self.roof_info['G'])

            scale, roof_left, roof_top = get_scale_and_roofTopLeft(self.roof_info['H'], max_height)
            # scale = min(draw_width / float(self.roof_info['H']), draw_height / float(max_height))
            # roof_left = (frame_width - self.roof_info['H'] * scale) / 2
            # roof_top = (frame_height - self.roof_info['A'] * scale) / 2

            p0 = [roof_left, roof_top]  # AB
            p1 = [p0[0], p0[1] + self.roof_info['A'] * scale]  # AH
            p2 = [p1[0] + self.roof_info['H'] * scale, p1[1]]  # HG
            p3 = [p2[0], p2[1] - self.roof_info['G'] * scale]  # FG
            p4 = [p3[0] - self.roof_info['F'] * scale, p3[1]]  # EF
            p5 = [p4[0], p4[1] + self.roof_info['E'] * scale]  # DE
            p6 = [p5[0] - self.roof_info['D'] * scale, p5[1]]  # CD
            p7 = [p6[0], p0[1]]  # BC

            self.roofscene_canvas.create_polygon([p0, p1, p2, p3, p4, p5, p6, p7], outline=roof_outline_color)
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(p0[0], half_int(p0[1], p1[1]),
                                              text=f"{self.roof_info['A']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p1[0], p2[0]), p1[1],
                                              text=f"{self.roof_info['H']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p2[0], half_int(p2[1], p3[1]),
                                              text=f"{self.roof_info['G']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p3[0], p4[0]), p3[1],
                                              text=f"{self.roof_info['F']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p4[0], half_int(p4[1], p5[1]),
                                              text=f"{self.roof_info['E']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p5[0], p6[0]), p6[1],
                                              text=f"{self.roof_info['D']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p6[0], half_int(p6[1], p7[1]),
                                              text=f"{self.roof_info['C']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p0[0], p7[0]), p0[1],
                                              text=f"{self.roof_info['B']}",
                                              font=("Arial", 12),
                                              fill=text_color)
        elif roofSurfaceCategory == "下凹形":
            self.roof_info['G'] = self.roof_info['A'] - self.roof_info['C'] + self.roof_info['E']
            self.roof_info['H'] = self.roof_info['B'] - self.roof_info['D'] - self.roof_info['F']
            max_height = max(self.roof_info['A'], self.roof_info['C'])

            scale, roof_left, roof_top = get_scale_and_roofTopLeft(self.roof_info['B'], max_height)
            # scale = min(draw_width / float(self.roof_info['B']), draw_height / float(max_height ))
            # roof_left = (frame_width - self.roof_info['B'] * scale) / 2
            # roof_top = (frame_height - self.roof_info['C'] * scale) / 2

            p0 = [roof_left, roof_top]  # AB
            p1 = [p0[0], p0[1] + self.roof_info['A'] * scale]  # AH
            p2 = [p1[0] + self.roof_info['H'] * scale, p1[1]]  # HG
            p3 = [p2[0], p2[1] - self.roof_info['G'] * scale]  # FG
            p4 = [p3[0] + self.roof_info['F'] * scale, p3[1]]  # EF
            p5 = [p4[0], p4[1] + self.roof_info['E'] * scale]  # DE
            p6 = [p5[0] + self.roof_info['D'] * scale, p5[1]]  # CD
            p7 = [p6[0], p0[1]]  # BC

            self.roofscene_canvas.create_polygon([p0, p1, p2, p3, p4, p5, p6, p7], outline=roof_outline_color)
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(p0[0], half_int(p0[1], p1[1]),
                                              text=f"{self.roof_info['A']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p1[0], p2[0]), p1[1],
                                              text=f"{self.roof_info['H']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p2[0], half_int(p2[1], p3[1]),
                                              text=f"{self.roof_info['G']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p3[0], p4[0]), p3[1],
                                              text=f"{self.roof_info['F']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p4[0], half_int(p4[1], p5[1]),
                                              text=f"{self.roof_info['E']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p5[0], p6[0]), p6[1],
                                              text=f"{self.roof_info['D']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p6[0], half_int(p6[1], p7[1]),
                                              text=f"{self.roof_info['C']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p0[0], p7[0]), p0[1],
                                              text=f"{self.roof_info['B']}",
                                              font=("Arial", 12),
                                              fill=text_color)
        elif roofSurfaceCategory == "左凹形":
            self.roof_info['G'] = self.roof_info['A'] + self.roof_info['C'] + self.roof_info['E']
            self.roof_info['H'] = self.roof_info['B'] - self.roof_info['D'] + self.roof_info['F']
            max_width = max(self.roof_info['F'], self.roof_info['H'])

            scale, roof_left, roof_top = get_scale_and_roofTopLeft(max_width, self.roof_info['G'])
            # scale = min(draw_width / float(max_width), draw_height / float(self.roof_info['G']))
            # roof_left = (frame_width - self.roof_info['H'] * scale) / 2
            # roof_top = (frame_height - self.roof_info['G'] * scale) / 2

            p0 = [roof_left, roof_top + (self.roof_info['E'] + self.roof_info['C']) * scale]  # AB
            p1 = [p0[0], p0[1] + self.roof_info['A'] * scale]  # AH
            p2 = [p1[0] + self.roof_info['H'] * scale, p1[1]]  # HG
            p3 = [p2[0], p2[1] - self.roof_info['G'] * scale]  # FG
            p4 = [p3[0] - self.roof_info['F'] * scale, p3[1]]  # EF
            p5 = [p4[0], p4[1] + self.roof_info['E'] * scale]  # DE
            p6 = [p5[0] + self.roof_info['D'] * scale, p5[1]]  # CD
            p7 = [p6[0], p0[1]]  # BC

            self.roofscene_canvas.create_polygon([p0, p1, p2, p3, p4, p5, p6, p7], outline=roof_outline_color)
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(p0[0], half_int(p0[1], p1[1]),
                                              text=f"{self.roof_info['A']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p1[0], p2[0]), p1[1],
                                              text=f"{self.roof_info['H']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p2[0], half_int(p2[1], p3[1]),
                                              text=f"{self.roof_info['G']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p3[0], p4[0]), p3[1],
                                              text=f"{self.roof_info['F']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p4[0], half_int(p4[1], p5[1]),
                                              text=f"{self.roof_info['E']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p5[0], p6[0]), p6[1],
                                              text=f"{self.roof_info['D']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p6[0], half_int(p6[1], p7[1]),
                                              text=f"{self.roof_info['C']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p0[0], p7[0]), p0[1],
                                              text=f"{self.roof_info['B']}",
                                              font=("Arial", 12),
                                              fill=text_color)
        elif roofSurfaceCategory == "右凹形":
            self.roof_info['G'] = self.roof_info['A'] - self.roof_info['C'] - self.roof_info['E']
            self.roof_info['H'] = self.roof_info['B'] - self.roof_info['D'] + self.roof_info['F']
            max_width = max(self.roof_info['B'], self.roof_info['H'])
            scale, roof_left, roof_top = get_scale_and_roofTopLeft(max_width, self.roof_info['A'])
            # scale = min(draw_width / float(max_width), draw_height / float(self.roof_info['A']))
            # roof_left = (frame_width - self.roof_info['B'] * scale) / 2
            # roof_top = (frame_height - self.roof_info['A'] * scale) / 2

            p0 = [roof_left, roof_top]  # AB
            p1 = [p0[0], p0[1] + self.roof_info['A'] * scale]  # AH
            p2 = [p1[0] + self.roof_info['H'] * scale, p1[1]]  # HG
            p3 = [p2[0], p2[1] - self.roof_info['G'] * scale]  # FG
            p4 = [p3[0] - self.roof_info['F'] * scale, p3[1]]  # EF
            p5 = [p4[0], p4[1] - self.roof_info['E'] * scale]  # DE
            p6 = [p5[0] + self.roof_info['D'] * scale, p5[1]]  # CD
            p7 = [p6[0], p0[1]]  # BC

            self.roofscene_canvas.create_polygon([p0, p1, p2, p3, p4, p5, p6, p7], outline=roof_outline_color)
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(p0[0], half_int(p0[1], p1[1]),
                                              text=f"{self.roof_info['A']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p1[0], p2[0]), p1[1],
                                              text=f"{self.roof_info['H']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p2[0], half_int(p2[1], p3[1]),
                                              text=f"{self.roof_info['G']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p3[0], p4[0]), p3[1],
                                              text=f"{self.roof_info['F']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p4[0], half_int(p4[1], p5[1]),
                                              text=f"{self.roof_info['E']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p5[0], p6[0]), p6[1],
                                              text=f"{self.roof_info['D']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p6[0], half_int(p6[1], p7[1]),
                                              text=f"{self.roof_info['C']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p0[0], p7[0]), p0[1],
                                              text=f"{self.roof_info['B']}",
                                              font=("Arial", 12),
                                              fill=text_color)
        elif roofSurfaceCategory == "正7形":
            self.roof_info['E'] = self.roof_info['A'] + self.roof_info['C']
            self.roof_info['F'] = self.roof_info['D'] - self.roof_info['B']
            scale, roof_left, roof_top = get_scale_and_roofTopLeft(self.roof_info['D'], self.roof_info['E'])
            # scale = min(draw_width / float(self.roof_info['D']), draw_height / float(self.roof_info['E']))

            p0 = [(frame_width - self.roof_info['D'] * scale) / 2,
                  (frame_height - self.roof_info['E'] * scale) / 2]  # point between CD
            p1 = [p0[0], p0[1] + self.roof_info['C'] * scale]  # point between BC
            p2 = [p1[0] + self.roof_info['B'] * scale, p1[1]]  # AB
            p3 = [p2[0], p2[1] + self.roof_info['A'] * scale]  # AF
            p4 = [p3[0] + self.roof_info['F'] * scale, p3[1]]  # EF
            p5 = [p4[0], p4[1] - self.roof_info['E'] * scale]  # DE

            self.roofscene_canvas.create_polygon([p0, p1, p2, p3, p4, p5], outline=roof_outline_color)
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(p2[0], half_int(p2[1], p3[1]),
                                              text=f"{self.roof_info['A']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p1[0], p2[0]), p1[1],
                                              text=f"{self.roof_info['B']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p0[0], half_int(p0[1], p1[1]),
                                              text=f"{self.roof_info['C']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p0[0], p5[0]), p0[1],
                                              text=f"{self.roof_info['D']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p4[0], half_int(p4[1], p5[1]),
                                              text=f"{self.roof_info['E']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p3[0], p4[0]), p4[1],
                                              text=f"{self.roof_info['F']}",
                                              font=("Arial", 12),
                                              fill=text_color)
        elif roofSurfaceCategory == "反7形":
            self.roof_info['E'] = self.roof_info['A'] - self.roof_info['C']
            self.roof_info['F'] = self.roof_info['B'] - self.roof_info['D']
            scale, roof_left, roof_top = get_scale_and_roofTopLeft(self.roof_info['B'], self.roof_info['A'])
            # scale = min(draw_width / float(self.roof_info['B']), draw_height / float(self.roof_info['A']))
            # roof_left = (frame_width - self.roof_info['B'] * scale) / 2
            # roof_top = (frame_height - self.roof_info['A'] * scale) / 2
            p0 = [roof_left + self.roof_info['B'] * scale, roof_top + self.roof_info['C'] * scale]  # point between CD
            p1 = [p0[0], roof_top]  # point between BC
            p2 = [roof_left, p1[1]]  # AB
            p3 = [p2[0], p2[1] + self.roof_info['A'] * scale]  # AF
            p4 = [p3[0] + self.roof_info['F'] * scale, p3[1]]  # EF
            p5 = [p4[0], p4[1] - self.roof_info['E'] * scale]  # DE

            self.roofscene_canvas.create_polygon([p0, p1, p2, p3, p4, p5], outline=roof_outline_color)
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(p2[0], half_int(p2[1], p3[1]),
                                              text=f"{self.roof_info['A']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p1[0], p2[0]), p1[1],
                                              text=f"{self.roof_info['B']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p0[0], half_int(p0[1], p1[1]),
                                              text=f"{self.roof_info['C']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p0[0], p5[0]), p0[1],
                                              text=f"{self.roof_info['D']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p4[0], half_int(p4[1], p5[1]),
                                              text=f"{self.roof_info['E']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p3[0], p4[0]), p4[1],
                                              text=f"{self.roof_info['F']}",
                                              font=("Arial", 12),
                                              fill=text_color)
        elif roofSurfaceCategory == "正L形":
            self.roof_info['E'] = self.roof_info['A'] - self.roof_info['C']
            self.roof_info['F'] = self.roof_info['B'] + self.roof_info['D']
            scale, roof_left, roof_top = get_scale_and_roofTopLeft(self.roof_info['F'], self.roof_info['A'])
            # scale = min(draw_width / float(self.roof_info['F']), draw_height / float(self.roof_info['A']))
            # roof_left = (frame_width - self.roof_info['F'] * scale) / 2
            # roof_top = (frame_height - self.roof_info['A'] * scale) / 2
            p0 = [roof_left + self.roof_info['B'] * scale, roof_top + self.roof_info['C'] * scale]  # point between CD
            p1 = [p0[0], roof_top]  # point between BC
            p2 = [roof_left, p1[1]]  # AB
            p3 = [p2[0], p2[1] + self.roof_info['A'] * scale]  # AF
            p4 = [p3[0] + self.roof_info['F'] * scale, p3[1]]  # EF
            p5 = [p4[0], p4[1] - self.roof_info['E'] * scale]  # DE

            self.roofscene_canvas.create_polygon([p0, p1, p2, p3, p4, p5], outline=roof_outline_color)
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(p2[0], half_int(p2[1], p3[1]),
                                              text=f"{self.roof_info['A']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p1[0], p2[0]), p1[1],
                                              text=f"{self.roof_info['B']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p0[0], half_int(p0[1], p1[1]),
                                              text=f"{self.roof_info['C']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p0[0], p5[0]), p0[1],
                                              text=f"{self.roof_info['D']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p4[0], half_int(p4[1], p5[1]),
                                              text=f"{self.roof_info['E']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p3[0], p4[0]), p4[1],
                                              text=f"{self.roof_info['F']}",
                                              font=("Arial", 12),
                                              fill=text_color)
        elif roofSurfaceCategory == "反L形":
            self.roof_info['E'] = self.roof_info['A'] + self.roof_info['C']
            self.roof_info['F'] = self.roof_info['B'] + self.roof_info['D']

            scale, roof_left, roof_top = get_scale_and_roofTopLeft(self.roof_info['F'], self.roof_info['E'])
            # scale = min(draw_width / float(self.roof_info['F']), draw_height / float(self.roof_info['E']))
            # roof_left = (frame_width - self.roof_info['F'] * scale) / 2
            # roof_top = (frame_height - self.roof_info['E'] * scale) / 2
            p0 = [roof_left + self.roof_info['B'] * scale, roof_top]  # point between CD
            p1 = [p0[0], p0[1] + self.roof_info['C'] * scale]  # point between BC
            p2 = [roof_left, p1[1]]  # AB
            p3 = [p2[0], p2[1] + self.roof_info['A'] * scale]  # AF
            p4 = [p3[0] + self.roof_info['F'] * scale, p3[1]]  # EF
            p5 = [p4[0], p4[1] - self.roof_info['E'] * scale]  # DE

            self.roofscene_canvas.create_polygon([p0, p1, p2, p3, p4, p5], outline=roof_outline_color)
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(p2[0], half_int(p2[1], p3[1]),
                                              text=f"{self.roof_info['A']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p1[0], p2[0]), p1[1],
                                              text=f"{self.roof_info['B']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p0[0], half_int(p0[1], p1[1]),
                                              text=f"{self.roof_info['C']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p0[0], p5[0]), p0[1],
                                              text=f"{self.roof_info['D']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(p4[0], half_int(p4[1], p5[1]),
                                              text=f"{self.roof_info['E']}",
                                              font=("Arial", 12),
                                              fill=text_color)
            self.roofscene_canvas.create_text(half_int(p3[0], p4[0]), p4[1],
                                              text=f"{self.roof_info['F']}",
                                              font=("Arial", 12),
                                              fill=text_color)
        elif roofSurfaceCategory == "自定义多边形":
            vertices = [(self.roof_info[f"vertex{i}_X"], self.roof_info[f"vertex{i}_Y"])
                        for i in range(self.roof_info["vertexCount"])]
            min_x = min(vertices, key=lambda p: p[0])[0]
            max_x = max(vertices, key=lambda p: p[0])[0]
            min_y = min(vertices, key=lambda p: p[1])[1]
            max_y = max(vertices, key=lambda p: p[1])[1]
            max_height = max_y - min_y
            max_width = max_x - min_x
            # 正常的话，minx,miny 顶点坐标为(0,0)
            scale, roof_left, roof_top = get_scale_and_roofTopLeft(max_width, max_height)
            # 自定义坐标(0,0)映射上屋面后，为(roof_left, roof_top)
            scaled_vertices = [(roof_left + v[0] * scale, roof_top + v[1] * scale) for v in vertices]
            self.roofscene_canvas.create_polygon(scaled_vertices, outline=roof_outline_color)
            # 显示屋顶尺寸
            for i in range(len(scaled_vertices)):
                scaled_v0 = scaled_vertices[i]
                scaled_v1 = None
                v0 = vertices[i]
                v1 = None
                if i + 1 == len(scaled_vertices):
                    v1 = vertices[0]
                    scaled_v1 = scaled_vertices[0]
                else:
                    v1 = vertices[i + 1]
                    scaled_v1 = scaled_vertices[i + 1]
                self.roofscene_canvas.create_text(half_int(scaled_v0[0], scaled_v1[0]),
                                                  half_int(scaled_v0[1], scaled_v1[1]),
                                                  text=f"{round(get_distance(v0, v1))}",
                                                  font=("Arial", 12),
                                                  fill=text_color)
        elif roofSurfaceCategory == "屋顶图片输入":
            def point_to_line_distance(line, x0, y0):
                # 提取 x 和 y 坐标
                x = [p[0] for p in line]
                y = [p[1] for p in line]

                # 检查是否所有的 x 坐标都相同
                if len(set(x)) == 1:
                    # 竖直线的情况
                    distance = abs(x0 - x[0])
                else:
                    # 拟合直线，返回斜率和截距
                    A = np.vstack([x, np.ones(len(x))]).T
                    m, c = np.linalg.lstsq(A, y, rcond=None)[0]

                    # 一般情况
                    distance = abs(m * x0 - y0 + c) / np.sqrt(m ** 2 + 1)

                return distance

            self.roof_info["roofMatrix"] = UnetTest.img2data(self.roof_info[chn2eng["图片路径"]])
            roof_matrix = self.roof_info["roofMatrix"]
            resolution = self.roof_info["resolution"] * 10
            rows = len(roof_matrix)
            cols = len(roof_matrix[0]) if rows > 0 else 0
            edge_points = []
            directionX = [0, 1, 0, -1, 1, 1, -1, -1]
            directionY = [1, 0, -1, 0, 1, -1, 1, -1]
            straightDirectionX = [0, 1, 0, -1]
            straightDirectionY = [1, 0, -1, 0]

            # Detecting edge points
            tempFlag = False
            for ii in range(rows):
                for jj in range(cols):
                    if roof_matrix[ii][jj] == 1 and ((ii == 0 or roof_matrix[ii - 1][jj] == 0) or (
                            ii == rows - 1 or roof_matrix[ii + 1][jj] == 0) or (
                                                             jj == 0 or roof_matrix[ii][jj - 1] == 0) or (
                                                             jj == cols - 1 or roof_matrix[ii][jj + 1] == 0)):
                        edge_points.append((jj, ii))
                        tempFlag = True
                        break
                if tempFlag:
                    break
            # 从这个点开始扩散寻找边界
            if len(edge_points) == 0:
                raise Exception("边界点数量为0")

            addFlag = True
            while addFlag:
                addFlag = False
                tempJ, tempI = edge_points[-1]
                for ii in range(len(directionX)):  # 从第一个边界点的四面八方开始寻找边界
                    tempI += directionY[ii]
                    tempJ += directionX[ii]
                    if 0 <= tempI < rows and 0 <= tempJ < cols and roof_matrix[tempI][tempJ] == 1:
                        for jj in range(len(straightDirectionX)):  # 判断当前[i,j]是否是边界点（要求四个方向的点至少有一个是0）
                            if 0 <= tempI + straightDirectionY[jj] < rows and 0 <= tempJ + straightDirectionX[
                                jj] < cols and roof_matrix[tempI + straightDirectionY[jj]][tempJ + straightDirectionX[
                                jj]] == 0 and (tempJ, tempI) not in edge_points:
                                edge_points.append((tempJ, tempI))
                                addFlag = True
                                break
                    if addFlag:
                        break
                    tempI -= directionY[ii]
                    tempJ -= directionX[ii]

            # Variables for tracking line segments
            all_lines = []
            temp_line = [edge_points[0]]

            # Define a threshold for point-line distance (can be adjusted)
            distance_threshold1 = 0.90
            distance_threshold2 = 1.31
            line_size_threshold = 3000000

            for point in edge_points[1:]:
                # Current line properties
                x0, y0 = point

                # Calculate the distance from the current point to the line defined by the start and end points of the temp_line
                distance = point_to_line_distance(temp_line, x0, y0)

                if len(temp_line) <= line_size_threshold and distance <= distance_threshold2 or len(
                        temp_line) > line_size_threshold and distance <= distance_threshold1:
                    temp_line.append(point)
                else:
                    all_lines.append(temp_line)
                    temp_line = [point]
                    # print(distance)

            # Append the last line segment
            if temp_line:
                all_lines.append(temp_line)

            # Drawing and annotating lines
            scale, roof_left, roof_top = get_scale_and_roofTopLeft(cols * resolution, rows * resolution)
            self.roof_info["vertexCount"] = len(all_lines)
            for ii, line in enumerate(all_lines):
                start_x, start_y = line[0]
                self.roof_info[f"vertex{ii}_X"] = start_x * resolution
                self.roof_info[f"vertex{ii}_Y"] = start_y * resolution
                end_x, end_y = line[-1]
                self.roofscene_canvas.create_line(
                    roof_left + start_x * resolution * scale,
                    roof_top + start_y * resolution * scale,
                    roof_left + end_x * resolution * scale,
                    roof_top + end_y * resolution * scale,
                    fill='yellow', width=2)

                # Calculate line length and display it
                line_length = sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2) * resolution
                mid_x = (start_x + end_x) / 2
                mid_y = (start_y + end_y) / 2
                self.roofscene_canvas.create_text(
                    roof_left + mid_x * resolution * scale,
                    roof_top + mid_y * resolution * scale,
                    text=f"{line_length:.0f}",
                    font=("Arial", 12),
                    fill="white")
        obstacles = self.obstacle_info + self.outside_obstacle_info
        # 绘制障碍物障碍物
        for obstacle in obstacles:
            try:
                centerX = float(obstacle['relativePositionX'])
                centerY = float(obstacle['relativePositionY'])
                if obstacle['isRound']:
                    # continue
                    length = float(obstacle['diameter']) / 2
                    x1 = roof_left + (centerX - length) * scale
                    y1 = roof_top + (centerY - length) * scale
                    x2 = roof_left + (centerX + length) * scale
                    y2 = roof_top + (centerY + length) * scale
                    self.roofscene_canvas.create_oval(x1, y1, x2, y2, outline='red')
                else:
                    width = float(obstacle['width'])
                    length = float(obstacle['length'])
                    x1 = roof_left + centerX * scale
                    y1 = roof_top + centerY * scale
                    x2 = roof_left + (centerX + width) * scale
                    y2 = roof_top + (centerY + length) * scale
                    self.roofscene_canvas.create_rectangle(x1, y1, x2, y2, outline='red')
                if len(obstacle["id"]) > 0:
                    self.roofscene_canvas.create_text(x2 + draw_width * 0.03, y2 + draw_height * 0.03,
                                                      text=f"{obstacle['id']}",
                                                      font=("Arial", 10),
                                                      fill="red")
            except:
                continue

        # print(self.get_input_json())

    def calculate_layout(self):
        allTimeStart = time.time()
        print(
            f"算法精度：{self.algorithm_info['precision']} mm，最大方案数量：{self.algorithm_info['maxArrangeCount']}")
        jsonData = self.get_input_json()
        const.const.changeUnit(jsonData['algorithm']['precision'])
        #    const.const.changeMinComponent(jsonData['algorithm']['minComponent'])
        const.const.changeMaxArrangeCount(jsonData['algorithm']['maxArrangeCount'])

        roof = classes.roof.Roof(jsonData["scene"]["roof"], jsonData["scene"]["location"]["latitude"],
                                 jsonData["scene"]["location"])
        assignComponentParameters(jsonData["component"])

        start_time = time.time()
        roof.addObstacles(jsonData["scene"]["roof"]["obstacles"])
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"addObstacles 代码执行时间为：{execution_time} 秒")

        # zzp: 基于屋顶有效面积，估计光伏板数量，参数0.7，参数范围0-1，参数越高预估光伏板数量越多
        minComponentCount, maxComponentCount = estimateComponentCount(roof.realArea,
                                                                      jsonData["component"]["specification"],
                                                                      0.7 / jsonData['algorithm']['maxArrangeCount'])
        const.const.changeMinComponent(minComponentCount if jsonData['algorithm']['maxArrangeCount'] >= 2 else 1)
        const.const.changeMaxComponent(maxComponentCount)
        print(f"自动估计最小光伏板数量:{minComponentCount}，最大光伏板数量:{maxComponentCount}")

        start_time = time.time()
        #    screenedArrangements = screenArrangements(roof.width, roof.length, jsonData["component"]["specification"],
        #                                              jsonData["arrangeType"],
        #                                              jsonData["scene"]["location"]["windPressure"])
        screenedArrangements = screenArrangements(roof.width, roof.length, jsonData["component"]["specification"],
                                                  jsonData["arrangeType"],
                                                  "低压")

        end_time = time.time()
        execution_time = end_time - start_time
        print(f"screenArrangements 代码执行时间为：{execution_time} 秒")

        start_time = time.time()
        # 多进程计算阴影
        if jsonData["algorithm"]["maxArrangeCount"] > 1:
            chunks = chunk_it(list(screenedArrangements.keys()), cpuCount)
            allResultArray = []
            with multiprocessing.Pool(processes=cpuCount) as pool:
                resultArray = pool.map(cAS, [(chunk, roof.latitude, screenedArrangements) for chunk in chunks])
                for r in resultArray:
                    for rr in r:
                        allResultArray.append(rr)
            for result in allResultArray:
                screenedArrangements[result[0]].shadowRelativePosition = result[1]
                screenedArrangements[result[0]].shadowArray = result[2]

        # zzp:提前排序
        screenedArrangements = dict(sorted(screenedArrangements.items(), key=lambda x: x[1].value, reverse=True))
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"calculateArrangementShadow代码执行时间为：{execution_time} 秒")

        start_time = time.time()
        maxValue = 0
        panelValue = -1
        for i in range(1, jsonData['algorithm']['maxArrangeCount'] + 1):
            panelValue = roof.getBestOptions(screenedArrangements, i, maxValue, maxComponentCount)  # 计算铺设光伏板的最佳方案
            print(f"{i}阵列下得到的最大光伏板:{panelValue}")
            if i == jsonData['algorithm']['maxArrangeCount']:
                break
            if maxValue < panelValue:
                maxValue = panelValue

            # zzp:剪枝过大的方案
            IDArray = list(screenedArrangements.keys())
            original_length = len(IDArray)
            cut_index = len(IDArray)
            for j in range(cut_index):
                if screenedArrangements[IDArray[j]].componentNum <= maxValue:
                    cut_index = j
                    break
            screenedArrangements = {IDArray[j]: screenedArrangements[IDArray[j]] for j in
                                    range(cut_index, original_length)}

            # zzp:剪枝过小的方案
            # IDArray = list(screenedArrangements.keys())
            # maxArrangementValue = sum([screenedArrangements[IDArray[j]].componentNum for j in range(i)])
            # cut_index = len(IDArray)
            # for j in range(i, cut_index):
            #     if screenedArrangements[IDArray[j]].componentNum + maxArrangementValue < maxValue:
            #         cut_index = j
            #         break
            # screenedArrangements = {IDArray[j]: screenedArrangements[IDArray[j]] for j in range(cut_index)}
            print(
                f"计算{i}阵列对方案进行剪枝，剪枝前方案数量：{original_length}，剪枝后方案数量：{len(list(screenedArrangements.keys()))}")

        end_time = time.time()
        execution_time = end_time - start_time
        print(f"getBestOptions 代码执行时间为：{execution_time} 秒")

        # start_time = time.time()
        # panelValue = roof.addObstaclesConcern(screenedArrangements)
        # end_time = time.time()
        # execution_time = end_time - start_time
        # print(f"addObstaclesConcern 代码执行时间为：{execution_time} 秒")

        start_time = time.time()
        roof.obstacleArraySelf = roof.calculateObstacleSelf()
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"calculateObstacleSelf 代码执行时间为：{execution_time} 秒")

        start_time = time.time()
        columnValue = roof.calculate_column(screenedArrangements)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"calculate_column 代码执行时间为：{execution_time} 秒")

        # 按是否抬高筛选出更优的排布方案
        # minRaiseLevel = const.const.INF
        for placement in roof.allPlacements:
            raiseText = ""
            for i, arrangement in enumerate(placement[0]):
                if arrangement["raiseLevel"] == 1:
                    raiseText += f"第{i + 1}阵列高度为{1000}mm\n"
                else:
                    raiseText += f"第{i + 1}阵列高度为{540}mm\n"
            placement[4] += raiseText + "\n\n"

        # return roof.drawPlacement(screenedArrangements)
        start_time = time.time()
        tempArray = [roof.drawPlacement(screenedArrangements),
                     [placement[4] for placement in roof.allPlacements[:const.const.outputPlacementCount]]]
        # tempArray = roof.drawPlacement(screenedArrangements), ["", "", "", "", ""]
        end_time = time.time()
        execution_time = end_time - start_time
        print("drawPlacement 代码执行时间为：", execution_time, "秒\n")
        print(f"一共排布了{panelValue}块光伏板，{columnValue}根立柱")
        print("总代码执行时间为：", time.time() - allTimeStart, "秒\n")
        tempArray.append({
            "精度": f"{jsonData['algorithm']['precision']}mm",
            "最大阵列数量": f"{jsonData['algorithm']['maxArrangeCount']}种",
            "基于面积推算的最大光伏板数量": f"{maxComponentCount}块",
            "最终排布的方案种类数": f"{len(roof.allPlacements)}种",
            "最终排布的光伏板数量": f"{panelValue}块",
            "最终排布的立柱数量": f"{columnValue}根",
            "总耗时": "{:.2f}s".format(time.time() - allTimeStart)
        })
        return tempArray

    def cal_and_display_layout(self):
        for i in range(const.const.outputPlacementCount):
            self.arrangement_btns[i].config(state="disabled")
        placement_result = self.calculate_layout()
        self.layout_imgs, self.placement_info, self.layout_final_info = \
            placement_result[0][:const.const.outputPlacementCount], \
            placement_result[1][:const.const.outputPlacementCount], "\n".join(
                [f"{k}:{v}" for k, v in placement_result[2].items()])
        self.display_layout()
        for i in range(len(self.layout_imgs)):
            self.arrangement_btns[i].config(state="active")

    def display_layout(self, index=0):
        try:
            image_matrix = self.layout_imgs[index]
            image = Image.fromarray(image_matrix)
            scaled_image = image.resize((frame_width, frame_height))
            # image.save(os.path.join(file_dir,f"image_{index}.png"))
            # scaled_image.save(os.path.join(file_dir,f"scaled_image_{index}.png"))
            self.display_img = ImageTk.PhotoImage(scaled_image)
            self.arrangement_canvas.create_image(0, 0, anchor=tk.NW, image=self.display_img)
            self.arrangement_info_text_var.set(self.placement_info[index] + self.layout_final_info)
        except Exception as e:
            print("Exception", e)

    def clear_info(self):

        self.location_info = {}
        self.roof_info = {}
        self.obstacle_info = []
        self.outside_obstacle_info = []
        self.panel_info = {}
        self.algorithm_info = {}
        self.clear_canvas()

    def get_demo_input(self, index=0):
        with open(os.path.join(file_dir, f'input{index}.json'), 'r', encoding='utf-8') as f:
            input_json = json.load(f)

        self.clear_info()

        if "scene" in input_json:
            if "location" in input_json["scene"]:
                for key, value in input_json["scene"]["location"].items():
                    self.location_info[key] = value

            if "roof" in input_json["scene"]:
                for key, value in input_json["scene"]["roof"].items():
                    try:
                        self.roof_info[key] = value
                    except:
                        self.roof_info[key] = value
                if 'extensibleDistance' in self.roof_info:
                    self.roof_info["extensibleDistanceEast"] = self.roof_info["extensibleDistance"][0]
                    self.roof_info["extensibleDistanceWest"] = self.roof_info["extensibleDistance"][1]
                    self.roof_info["extensibleDistanceSouth"] = self.roof_info["extensibleDistance"][2]
                    self.roof_info["extensibleDistanceNorth"] = self.roof_info["extensibleDistance"][3]
                if 'parapetWall' in self.roof_info:
                    for key, value in self.roof_info['parapetWall'].items():
                        self.roof_info['parapetWall' + key] = value

                if "obstacles" in input_json["scene"]["roof"]:
                    for obstacle in input_json["scene"]["roof"]["obstacles"]:
                        new_item = {}
                        for key, value in obstacle.items():
                            try:
                                new_item[key] = value
                            except:
                                new_item[key] = value
                        if obstacle['isRound']:
                            new_item['relativePositionX'] = new_item['centerPosition'][0]
                            new_item['relativePositionY'] = new_item['centerPosition'][1]
                        else:
                            new_item['relativePositionX'] = new_item['upLeftPosition'][0]
                            new_item['relativePositionY'] = new_item['upLeftPosition'][1]
                        new_item['isRound'] = obstacle['isRound']
                        self.obstacle_info.append(new_item)

            if "obstacles" in input_json["scene"]:
                for obstacle in input_json["scene"]["obstacles"]:
                    new_item = {}
                    for key, value in obstacle.items():
                        try:
                            new_item[key] = value
                        except:
                            new_item[key] = value
                    if obstacle['isRound']:
                        new_item['relativePositionX'] = new_item['centerPosition'][0]
                        new_item['relativePositionY'] = new_item['centerPosition'][1]
                    else:
                        new_item['relativePositionX'] = new_item['upLeftPosition'][0]
                        new_item['relativePositionY'] = new_item['upLeftPosition'][1]
                    new_item['isRound'] = obstacle['isRound']
                    self.outside_obstacle_info.append(new_item)

        if "component" in input_json:
            for key, value in input_json["component"].items():
                self.panel_info[key] = value

        if "algorithm" in input_json:
            for key, value in input_json["algorithm"].items():
                self.algorithm_info[key] = value

        if "arrangeType" in input_json:
            self.arrangeType_var.set(input_json["arrangeType"])

        self.adjust_irregular_roof_vertices()
        self.draw_roofscene()
        return input_json

    def get_input_json(self):
        input_json = {}
        # guest
        input_json["guest"] = {}
        input_json["guest"]["name"] = ""
        input_json["guest"]["phone"] = ""
        # scene
        # location
        input_json["scene"] = {}
        input_json["scene"]["location"] = {}
        for key, value in self.location_info.items():
            input_json["scene"]["location"][key] = value
        # roof
        input_json["scene"]["roof"] = {}
        input_json["scene"]["roof"]["parapetWall"] = {}
        extensibleDistance = [0, 0, 0, 0]
        for key, value in self.roof_info.items():
            if 'parapetWall' in key:
                input_json["scene"]["roof"]["parapetWall"][key[len("parapetWall"):]] = value
            elif 'extensibleDistance' in key:
                if 'East' in key:
                    extensibleDistance[0] = value
                if 'West' in key:
                    extensibleDistance[1] = value
                if 'South' in key:
                    extensibleDistance[2] = value
                if 'North' in key:
                    extensibleDistance[3] = value
            else:
                input_json["scene"]["roof"][key] = value
        input_json["scene"]["roof"]["extensibleDistance"] = extensibleDistance
        if self.roof_info["roofSurfaceCategory"] != "矩形":
            input_json["scene"]["roof"]["isComplex"] = True
        # obstacle in roof
        input_json["scene"]["roof"]["obstacles"] = []
        for obstacle in self.obstacle_info:
            new_item = {}
            position = [0, 0]
            for key, value in obstacle.items():
                if "relativePositionX" == key:
                    position[0] = value
                elif "relativePositionY" == key:
                    position[1] = value
                else:
                    new_item[key] = value
            if new_item["isRound"]:
                new_item["centerPosition"] = position
            else:
                new_item["upLeftPosition"] = position

            input_json["scene"]["roof"]["obstacles"].append(new_item)
        # arrangeType
        input_json["arrangeType"] = self.arrangeType_var.get()
        # component
        input_json["component"] = {}
        input_json["component"]["specification"] = ""
        for key, value in self.panel_info.items():
            input_json["component"][key] = value

        # algorithm
        input_json["algorithm"] = {}
        for key, value in self.algorithm_info.items():
            input_json["algorithm"][key] = value

        return input_json

    def on_closing(self):
        self.root.quit()
        self.root.destroy()

    def update_arrangement_info_text(self):
        self.arrangement_info_text_var.set("展示文本\n展示文本\n")

    def adjust_irregular_roof_vertices(self):
        if self.roof_info["roofSurfaceCategory"] == "自定义多边形":
            vertices = [(self.roof_info[f"vertex{i}_X"], self.roof_info[f"vertex{i}_Y"])
                        for i in range(self.roof_info["vertexCount"])]
            min_x = min(vertices, key=lambda p: p[0])[0]
            min_y = min(vertices, key=lambda p: p[1])[1]
            for i, v in enumerate(vertices):
                self.roof_info[f"vertex{i}_X"] = v[0] - min_x
                self.roof_info[f"vertex{i}_Y"] = v[1] - min_y


def cAS(params):
    chunk, latitude, screenedArrangements = params
    retultArray = []
    for ID in chunk:
        screenedArrangements[ID].calculateArrangementShadow(latitude)
        retultArray.append([ID, screenedArrangements[ID].shadowRelativePosition, screenedArrangements[ID].shadowArray])
    return retultArray
