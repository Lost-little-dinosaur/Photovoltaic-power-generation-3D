import sys, os
import const.const
from tools.mutiProcessing import *

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import classes.roof
from classes.arrangement import screenArrangements
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
    "A边（mm）":"A",
    "B边（mm）":"B",
    "C边（mm）":"C",
    "D边（mm）":"D",
    "E边（mm）":"E",
    "F边（mm）":"F",
    
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
}
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
                                             command=partial(self.open_outside_obstacle_window, *obstacle_ui_info))
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
        for i in range(5):
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
        for i in range(5):
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
            # print(text + ": ", entry.get())
            self.location_info[chn2eng[text]] = entry.get()
        for text, entry in option_entries.items():
            # print(text + ": ", entry.get())
            self.location_info[chn2eng[text]] = entry.get()
        for text, entry in bool_entries.items():
            # print(text + ": ", entry.get())
            self.location_info[chn2eng[text]] = entry.get()
        window.destroy()

    def open_roof_window(self, str_text, option_text, options, bool_text):
        global str_components, str_entries, len_option_bool, submit_btn
        roof_window = tk.Toplevel(self.root)
        roof_window.title("添加屋顶信息")
        # roof_window.geometry("250x200")
        str_components = []
        str_entries = {}
        option_entries = {}
        bool_entries = {}
        len_option_bool = 0
        def create_input_options_for_irregular_roof(roof_window, value):
            global str_components, str_entries, len_option_bool, submit_btn
            roof_options = {
                "矩形":["A","B"],
                "上凸形":["A","B","C","D","E","F"],
                "下凸形":["A","B","C","D","E","F"],
                "左凸形":["A","B","C","D","E","F"],
                "右凸形":["A","B","C","D","E","F"],
                "上凹形":["A","B","C","D","E","F"],
                "下凹形":["A","B","C","D","E","F"],
                "左凹形":["A","B","C","D","E","F"],
                "右凹形":["A","B","C","D","E","F"],
                "正7形":["A","B","C","D"],
                "反7形":["A","B","C","D"],
                "正L形":["A","B","C","D"],
                "反L形":["A","B","C","D"]
            }
            if value not in roof_options:
                return
            for component in str_components:
                component.grid_forget()

            
            str_components = []
            str_entries = {}
            edges = [text + "边（mm）" for text in roof_options[value]] + ["高度（mm）"]
            for i, text in enumerate(edges):
                label = tk.Label(roof_window, text=text + ": ")
                label.grid(row=len_option_bool+i, column=0, padx=5, pady=5)
                entry = tk.Entry(roof_window)
                entry.grid(row=len_option_bool+i, column=1, padx=5, pady=5)
                str_entries[text] = entry
                str_components.append(label)
                str_components.append(entry)    
            submit_btn.grid(row=len(str_entries) + len_option_bool + 1, column=0, columnspan=2,
                        padx=5,
                        pady=5)

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
            scheme_menu.config(width=5)
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
                                                                  bool_entries))
        submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2,
                        padx=5,
                        pady=5)

    def get_roof_data(self, window, str_entries, option_entries, bool_entries):
        for text, entry in str_entries.items():
            # print(text + ": ", entry.get())
            self.roof_info[chn2eng[text]] = entry.get()
        for text, entry in option_entries.items():
            # print(text + ": ", entry.get())
            self.roof_info[chn2eng[text]] = entry.get()
        for text, entry in bool_entries.items():
            # print(text + ": ", entry.get())
            self.roof_info[chn2eng[text]] = entry.get()
        window.destroy()

    def open_obstacle_window(self, str_text, option_text, options, bool_text):
        obstacle_window = tk.Toplevel(self.root)
        obstacle_window.title("添加墙内障碍物信息")
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
            # print(text + ": ", entry.get())
            new_obstacle[chn2eng[text]] = entry.get()
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
            # print(text + ": ", entry.get())
            new_obstacle[chn2eng[text]] = entry.get()
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
            # print(text + ": ", entry.get())
            self.panel_info[chn2eng[text]] = entry.get()
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
            # print(text + ": ", entry.get())
            self.panel_info[chn2eng[text]] = entry.get()
        for text, entry in option_entries.items():
            # print(text + ": ", entry.get())
            self.panel_info[chn2eng[text]] = entry.get()
        for text, entry in bool_entries.items():
            # print(text + ": ", entry.get())
            self.panel_info[chn2eng[text]] = entry.get()
        window.destroy()

    def clear_canvas(self):
        self.roofscene_canvas.delete("all")

    def draw_roofscene(self):
        half_int = lambda x,y: int(x+y)/2
        self.clear_canvas()

        draw_width = frame_width - draw_gap * 2
        draw_height = frame_height - draw_gap * 2

        roofSurfaceCategory = self.roof_info.get('roofSurfaceCategory',"矩形")
        if roofSurfaceCategory == "矩形": #绘制矩形屋顶
            scale = min(draw_width / float(self.roof_info['B']), draw_height / float(self.roof_info['A']))
            scaled_width = float(self.roof_info['B']) * scale
            scaled_height = float(self.roof_info['A']) * scale
            # 计算矩形位置使其居中
            roof_left = (frame_width - scaled_width) / 2
            roof_top = (frame_height - scaled_height) / 2
            roof_right = roof_left + scaled_width
            roof_bottom = roof_top + scaled_height
            # 在 Canvas 上绘制缩放后的矩形
            self.roofscene_canvas.create_rectangle(roof_left, roof_top, roof_right, roof_bottom, outline=roof_outline_color,
                                                tags="roof")
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(half_int(roof_left, roof_right), roof_top,
                                            text=f"{self.roof_info['B']}",
                                            font=("Arial", 12),
                                            fill=text_color)
            self.roofscene_canvas.create_text(roof_left, half_int(roof_top,roof_bottom),
                                            text=f"{self.roof_info['A']}",
                                            font=("Arial", 12),
                                            fill=text_color)
        elif roofSurfaceCategory == "上凸形":
            self.roof_info['G'] = self.roof_info['A'] + self.roof_info['C'] - self.roof_info['E']
            self.roof_info['H'] = self.roof_info['B'] + self.roof_info['D'] + self.roof_info['F']
            AC_height = self.roof_info['A'] + self.roof_info['C']
            scale = min(draw_width / float(self.roof_info['H']), draw_height / float(AC_height))
            
            
            p1 = [(frame_width - self.roof_info['H'] * scale) / 2, (frame_height + AC_height * scale) / 2] # point between AH
            p0 = [p1[0], p1[1] - self.roof_info['A'] * scale] # point between AB
            p2 = [p0[0] + self.roof_info['H'] * scale ,p1[1]] # HG
            p3 = [p2[0], p2[1] - self.roof_info['G'] * scale] # FG
            p4 = [p3[0] - self.roof_info['F'] * scale, p3[1]] #EF
            p5 = [p4[0], p4[1] - self.roof_info['E'] * scale] #DE
            p6 = [p5[0] - self.roof_info['D'] * scale, p5[1]] #CD
            p7 = [p6[0], p0[1]] #BC

            self.roofscene_canvas.create_polygon([p0,p1,p2,p3,p4,p5,p6,p7],outline=roof_outline_color)            
            # 显示屋顶尺寸
            self.roofscene_canvas.create_text(p0[0], half_int(p0[1],p1[1]),
                                            text=f"{self.roof_info['A']}",
                                            font=("Arial", 12),
                                            fill=text_color)
            self.roofscene_canvas.create_text(half_int(p0[0],p7[0]), p7[1],
                                            text=f"{self.roof_info['B']}",
                                            font=("Arial", 12),
                                            fill=text_color)
            self.roofscene_canvas.create_text(p6[0],half_int(p6[1],p7[1]),
                                            text=f"{self.roof_info['C']}",
                                            font=("Arial", 12),
                                            fill=text_color)
            self.roofscene_canvas.create_text(half_int(p5[0],p6[0]), p5[1],
                                            text=f"{self.roof_info['D']}",
                                            font=("Arial", 12),
                                            fill=text_color)
            self.roofscene_canvas.create_text(p4[0], half_int(p4[1],p5[1]),
                                            text=f"{self.roof_info['E']}",
                                            font=("Arial", 12),
                                            fill=text_color)
            self.roofscene_canvas.create_text(half_int(p3[0],p4[0]), p4[1],
                                            text=f"{self.roof_info['F']}",
                                            font=("Arial", 12),
                                            fill=text_color)
            self.roofscene_canvas.create_text(p2[0],half_int(p2[1],p3[1]),
                                            text=f"{self.roof_info['G']}",
                                            font=("Arial", 12),
                                            fill=text_color)
            self.roofscene_canvas.create_text(half_int(p1[0],p2[0]),p1[1],
                                            text=f"{self.roof_info['H']}",
                                            font=("Arial", 12),
                                            fill=text_color)


        # 绘制屋内障碍物
        for obstacle in self.obstacle_info:
            try:
                centerX = float(obstacle['relativePositionX'])
                centerY = float(obstacle['relativePositionY'])
                if obstacle['isRound']:
                    length = float(obstacle['diameter']) / 2
                    x1 = roof_left + (centerX - length) * scale
                    y1 = roof_top + (centerY - length) * scale
                    x2 = roof_left + (centerX + length) * scale
                    y2 = roof_top + (centerY + length) * scale
                    self.roofscene_canvas.create_oval(x1, y1, x2, y2, outline='red')
                else:
                    width = float(obstacle['width'])
                    length = float(obstacle['height'])
                    x1 = roof_left + centerX * scale
                    y1 = roof_top + centerY * scale
                    x2 = roof_left + (centerX + width) * scale
                    y2 = roof_top + (centerY + length) * scale
                    self.roofscene_canvas.create_rectangle(x1, y1, x2, y2, outline='red')
                if len(obstacle["id"]) > 0:
                    self.roofscene_canvas.create_text(x2 + draw_width * 0.01, y2 + draw_height * 0.01,
                                                      text=f"{obstacle['id']}",
                                                      font=("Arial", 10),
                                                      fill="red")
            except:
                continue
        # print(self.get_input_json())

    def calculate_layout(self):
        jsonData = self.get_input_json()
        const.const.changeUnit(jsonData['algorithm']['precision'])
        const.const.changeMaxArrangeCount(jsonData['algorithm']['maxArrangeCount'])

        roof = classes.roof.Roof(jsonData["scene"]["roof"], jsonData["scene"]["location"]["latitude"])
        start_time = time.time()
        assignComponentParameters(jsonData["component"])  # todo
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"assignComponentParameters 代码执行时间为：{execution_time} 秒")

        start_time = time.time()
        screenedArrangements = screenArrangements(roof.width, roof.length, jsonData["component"]["specification"],
                                                  jsonData["arrangeType"],
                                                  jsonData["scene"]["location"]["windPressure"])

        # 多进程计算阴影
        if jsonData["algorithm"]["maxArrangeCount"] > 1:
            chunks = chunk_it(list(screenedArrangements.keys()), cpuCount)
            with multiprocessing.Pool(processes=cpuCount) as pool:
                pool.map(cAS, [(chunk, roof.latitude, screenedArrangements) for chunk in chunks])

        end_time = time.time()
        execution_time = end_time - start_time
        print(f"screenArrangements + calculateArrangementShadow代码执行时间为：{execution_time} 秒")

        # 排布完光伏板后再添加障碍物并分析阴影
        start_time = time.time()
        roof.addObstacles(jsonData["scene"]["roof"]["obstacles"])
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"addObstacles 代码执行时间为：{execution_time} 秒")

        start_time = time.time()
        roof.getValidOptions(screenedArrangements)  # 计算铺设光伏板的最佳方案
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"getValidOptions 代码执行时间为：{execution_time} 秒")

        start_time = time.time()
        roof.addObstaclesConcern(screenedArrangements)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"addObstaclesConcern 代码执行时间为：{execution_time} 秒")

        start_time = time.time()
        roof.obstacleArraySelf = roof.calculateObstacleSelf()
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"calculateObstacleSelf 代码执行时间为：{execution_time} 秒")

        start_time = time.time()
        roof.calculate_column(screenedArrangements)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"calculate_column 代码执行时间为：{execution_time} 秒")

        # return roof.drawPlacement(screenedArrangements)
        start_time = time.time()
        tempArray = roof.drawPlacement(screenedArrangements), [placement[5] for placement in roof.allPlacements]
        end_time = time.time()
        execution_time = end_time - start_time
        print("drawPlacement 代码执行时间为：", execution_time, "秒")
        return tempArray

    def cal_and_display_layout(self):
        for i in range(5):
            self.arrangement_btns[i].config(state="disabled")
        placement_result = self.calculate_layout()
        self.layout_imgs, self.placement_info = placement_result[0][:5], placement_result[1][:5]
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
            self.arrangement_info_text_var.set(self.placement_info[index])
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
                        self.obstacle_info.append(new_item)

        # if "obstacles" in input_json:
        # for key, value in input_json["obstacles"].items():
        #     outside_self.obstacle_info[eng2chn[key]] = value

        if "component" in input_json:
            for key, value in input_json["component"].items():
                self.panel_info[key] = value

        if "algorithm" in input_json:
            for key, value in input_json["algorithm"].items():
                self.algorithm_info[key] = value

        if "arrangeType" in input_json:
            self.arrangeType_var.set(input_json["arrangeType"])

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


def cAS(params):
    chunk, latitude, screenedArrangements = params
    for ID in chunk:
        screenedArrangements[ID].calculateArrangementShadow(latitude)
