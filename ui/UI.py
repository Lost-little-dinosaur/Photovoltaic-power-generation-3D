# import sys, os
#
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#
# import classes.roof
# from classes.arrangement import screenArrangements
# # from classes.component import assignComponentParameters
# import json
# import tkinter as tk
# from PIL import Image, ImageTk
# from functools import partial
#
# location_info = {}
# roof_info = {}
# obstacle_info = []
# outside_obstacle_info = []
# panel_info = {}
# algorithm_info = {}
# frame_width = 420
# frame_height = 320
# draw_gap = 25  # gap for drawing text
# layout_imgs = []
# display_img = None
# file_dir = "files"
#
# chn2eng = {
#     "省份": "province",
#     "城市": "city",
#     "行政区": "region",
#     "经度": "longitude",
#     "纬度": "latitude",
#     "电压等级": "voltageLevel",
#     "距离并网点的距离": "distanceToGridConnection",
#     "风压": "windPressure",
#     "雪压": "snowPressure",
#     "风雪压": "windAndSnowPressure",
#     "大雪": "heavySnow",
#
#     "长度（mm）": "length",
#     "宽度（mm）": "width",
#     "高度（mm）": "height",
#     "偏移角度": "roofDirection",
#     "倾斜角度": "roofAngle",
#     # "可探出距离": "extensibleDistance",
#     "可探出距离（东）": "extensibleDistanceEast",
#     "可探出距离（南）": "extensibleDistanceSouth",
#     "可探出距离（西）": "extensibleDistanceWest",
#     "可探出距离（北）": "extensibleDistanceNorth",
#     # "是否有女儿墙": "haveParapetWall",
#     # "女儿墙":"parapetWall",
#     "女儿墙厚度": "parapetWallthick",
#     "女儿墙高度（mm）（东）": "parapetWalleastHeight",
#     "女儿墙高度（mm）（南）": "parapetWallsouthHeight",
#     "女儿墙高度（mm）（西）": "parapetWallwestHeight",
#     "女儿墙高度（mm）（北）": "parapetWallnorthHeight",
#     "屋顶类型": "category",
#     "复杂屋顶": "isComplex",
#     "预留运维通道": "maintenanceChannel",
#     "是否有挑檐": "haveOverhangingEave",
#     "ID": "id",
#     "直径": "diameter",
#     # "长度（mm）","宽度（mm）","高度（mm）",
#     "距离西侧屋顶距离": "relativePositionX",
#     "距离北侧屋顶距离": "relativePositionY",
#     "可调整高度（mm）": "adjustedHeight",
#     "类型": "type",
#     "是否圆形": "isRound",
#     "是否可移除": "removable",
#     "安装方案": "arrangeType",
#     "组件类型": "specification",
#     "功率": "power",
#     "厚度": "thickness",
#     "精度（mm）": "precision",
#     "贪心（单阵列）": "greedy",
#     "DFS（多阵列）": "dfs",
# }
# eng2chn = {v: k for k, v in chn2eng.items()}
#
#
# def open_location_window():
#     location_window = tk.Toplevel(root)
#     location_window.title("添加位置信息")
#
#     str_text = ["省份", "城市", "行政区", "经度", "纬度", "电压等级", "距离并网点的距离"]
#     str_entries = {}
#     for i, text in enumerate(str_text):
#         label = tk.Label(location_window, text=text + ": ")
#         label.grid(row=i, column=0, padx=5, pady=5)
#         entry = tk.Entry(location_window)
#         entry.grid(row=i, column=1, padx=5, pady=5)
#         str_entries[text] = entry
#     # Frame for installation scheme selection
#     option_text = ["风压", "雪压", "风雪压"]
#     options = [["低压", "高压"], ["低压", "高压"], ["低压", "高压"]]
#     option_entries = {}
#     for i, (text, option) in enumerate(zip(option_text, options)):
#         label = tk.Label(location_window, text=text)
#         label.grid(row=len(str_entries) + i, column=0, padx=5, pady=5)
#         scheme_var = tk.StringVar(location_window)
#         scheme_var.set(option[0])
#         scheme_menu = tk.OptionMenu(location_window, scheme_var, *option, )
#         scheme_menu.config(width=5)
#         scheme_menu.grid(row=len(str_entries) + i, column=1, padx=5, pady=5)
#         option_entries[text] = scheme_var
#     bool_text = ["大雪"]
#     bool_entries = {}
#     for i, text in enumerate(bool_text):
#         label = tk.Label(location_window, text=text)
#         label.grid(row=len(str_entries) + len(option_entries) + i, column=0, padx=5, pady=5)
#         bool_var = tk.BooleanVar()
#         bool_checkbox = tk.Checkbutton(location_window, variable=bool_var)
#         bool_checkbox.grid(row=len(str_entries) + len(option_entries) + i, column=1, padx=5, pady=5)
#         bool_entries[text] = bool_var
#     # 创建按钮，用于获取所有输入的数据
#     submit_btn = tk.Button(location_window, text="提交",
#                            command=lambda: get_location_data(location_window, str_entries, option_entries,
#                                                              bool_entries))
#     submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2, padx=5,
#                     pady=5)
#
#
# def get_location_data(window, str_entries, option_entries, bool_entries):
#     for text, entry in str_entries.items():
#         print(text + ": ", entry.get())
#         location_info[text] = entry.get()
#     for text, entry in option_entries.items():
#         print(text + ": ", entry.get())
#         location_info[text] = entry.get()
#     for text, entry in bool_entries.items():
#         print(text + ": ", entry.get())
#         location_info[text] = entry.get()
#     window.destroy()
#
#
# def open_roof_window():
#     roof_window = tk.Toplevel(root)
#     roof_window.title("添加屋顶信息")
#
#     str_text = ["长度（mm）", "宽度（mm）", "高度（mm）", "偏移角度", "倾斜角度", "可探出距离（东）"
#         , "可探出距离（南）", "可探出距离（西）", "可探出距离（北）",
#                 "女儿墙厚度", "女儿墙高度（mm）（东）", "女儿墙高度（mm）（南）", "女儿墙高度（mm）（西）", "女儿墙高度（mm）（北）"]
#     str_entries = {}
#     for i, text in enumerate(str_text):
#         label = tk.Label(roof_window, text=text + ": ")
#         label.grid(row=i, column=0, padx=5, pady=5)
#         entry = tk.Entry(roof_window)
#         entry.grid(row=i, column=1, padx=5, pady=5)
#         str_entries[text] = entry
#     # Frame for installation scheme selection
#     option_text = ["屋顶类型"]
#     options = [["平屋顶", "斜屋顶"]]
#     option_entries = {}
#     for i, (text, option) in enumerate(zip(option_text, options)):
#         label = tk.Label(roof_window, text=text)
#         label.grid(row=len(str_entries) + i, column=0, padx=5, pady=5)
#         scheme_var = tk.StringVar(roof_window)
#         scheme_var.set(option[0])
#         scheme_menu = tk.OptionMenu(roof_window, scheme_var, *option, )
#         scheme_menu.config(width=5)
#         scheme_menu.grid(row=len(str_entries) + i, column=1, padx=5, pady=5)
#         option_entries[text] = scheme_var
#     bool_text = ["复杂屋顶", "预留运维通道", "是否有挑檐"]
#     bool_entries = {}
#     for i, text in enumerate(bool_text):
#         label = tk.Label(roof_window, text=text)
#         label.grid(row=len(str_entries) + len(option_entries) + i, column=0, padx=5, pady=5)
#         bool_var = tk.BooleanVar()
#         bool_checkbox = tk.Checkbutton(roof_window, variable=bool_var)
#         bool_checkbox.grid(row=len(str_entries) + len(option_entries) + i, column=1, padx=5, pady=5)
#         bool_entries[text] = bool_var
#     # 创建按钮，用于获取所有输入的数据
#     submit_btn = tk.Button(roof_window, text="提交",
#                            command=lambda: get_roof_data(roof_window, str_entries, option_entries, bool_entries))
#     submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2, padx=5,
#                     pady=5)
#
#
# def get_roof_data(window, str_entries, option_entries, bool_entries):
#     for text, entry in str_entries.items():
#         print(text + ": ", entry.get())
#         roof_info[text] = entry.get()
#     for text, entry in option_entries.items():
#         print(text + ": ", entry.get())
#         roof_info[text] = entry.get()
#     for text, entry in bool_entries.items():
#         print(text + ": ", entry.get())
#         roof_info[text] = entry.get()
#     window.destroy()
#
#
# def open_obstacle_window():
#     obstacle_window = tk.Toplevel(root)
#     obstacle_window.title("添加墙内障碍物信息")
#     # 直径？长度（mm）？
#     str_text = ["ID", "直径", "长度（mm）", "宽度（mm）", "高度（mm）", "距离西侧屋顶距离", "距离北侧屋顶距离",
#                 "可调整高度（mm）"]
#     str_entries = {}
#     for i, text in enumerate(str_text):
#         label = tk.Label(obstacle_window, text=text + ": ")
#         label.grid(row=i, column=0, padx=5, pady=5)
#         entry = tk.Entry(obstacle_window)
#         entry.grid(row=i, column=1, padx=5, pady=5)
#         str_entries[text] = entry
#     # Frame for installation scheme selection
#     option_text = ["类型"]
#     options = [["无烟烟囱", "有烟烟囱"]]
#     option_entries = {}
#     for i, (text, option) in enumerate(zip(option_text, options)):
#         label = tk.Label(obstacle_window, text=text)
#         label.grid(row=len(str_entries) + i, column=0, padx=5, pady=5)
#         scheme_var = tk.StringVar(obstacle_window)
#         scheme_var.set(option[0])
#         scheme_menu = tk.OptionMenu(obstacle_window, scheme_var, *option, )
#         scheme_menu.config(width=5)
#         scheme_menu.grid(row=len(str_entries) + i, column=1, padx=5, pady=5)
#         option_entries[text] = scheme_var
#     bool_text = ["是否圆形", "是否可移除"]
#     bool_entries = {}
#     for i, text in enumerate(bool_text):
#         label = tk.Label(obstacle_window, text=text)
#         label.grid(row=len(str_entries) + len(option_entries) + i, column=0, padx=5, pady=5)
#         bool_var = tk.BooleanVar()
#         bool_checkbox = tk.Checkbutton(obstacle_window, variable=bool_var)
#         bool_checkbox.grid(row=len(str_entries) + len(option_entries) + i, column=1, padx=5, pady=5)
#         bool_entries[text] = bool_var
#     # 创建按钮，用于获取所有输入的数据
#     submit_btn = tk.Button(obstacle_window, text="提交",
#                            command=lambda: get_obstacle_data(obstacle_window, str_entries, option_entries,
#                                                              bool_entries))
#     submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2, padx=5,
#                     pady=5)
#
#
# def get_obstacle_data(window, str_entries, option_entries, bool_entries):
#     new_obstacle = {}
#     for text, entry in str_entries.items():
#         print(text + ": ", entry.get())
#         new_obstacle[text] = entry.get()
#     for text, entry in option_entries.items():
#         print(text + ": ", entry.get())
#         new_obstacle[text] = entry.get()
#     for text, entry in bool_entries.items():
#         print(text + ": ", entry.get())
#         new_obstacle[text] = entry.get()
#     obstacle_info.append(new_obstacle)
#     window.destroy()
#
#
# def open_outside_obstacle_window():
#     outside_obstacle_window = tk.Toplevel(root)
#     outside_obstacle_window.title("添加墙内障碍物信息")
#     # 直径？长度（mm）？
#     str_text = ["ID", "直径", "长度（mm）", "宽度（mm）", "高度（mm）", "距离西侧屋顶距离", "距离北侧屋顶距离",
#                 "可调整高度（mm）"]
#     str_entries = {}
#     for i, text in enumerate(str_text):
#         label = tk.Label(outside_obstacle_window, text=text + ": ")
#         label.grid(row=i, column=0, padx=5, pady=5)
#         entry = tk.Entry(outside_obstacle_window)
#         entry.grid(row=i, column=1, padx=5, pady=5)
#         str_entries[text] = entry
#     # Frame for installation scheme selection
#     option_text = ["类型"]
#     options = [["房屋", "树"]]
#     option_entries = {}
#     for i, (text, option) in enumerate(zip(option_text, options)):
#         label = tk.Label(outside_obstacle_window, text=text)
#         label.grid(row=len(str_entries) + i, column=0, padx=5, pady=5)
#         scheme_var = tk.StringVar(outside_obstacle_window)
#         scheme_var.set(option[0])
#         scheme_menu = tk.OptionMenu(outside_obstacle_window, scheme_var, *option, )
#         scheme_menu.config(width=5)
#         scheme_menu.grid(row=len(str_entries) + i, column=1, padx=5, pady=5)
#         option_entries[text] = scheme_var
#     bool_text = ["是否圆形", "是否可移除"]
#     bool_entries = {}
#     for i, text in enumerate(bool_text):
#         label = tk.Label(outside_obstacle_window, text=text)
#         label.grid(row=len(str_entries) + len(option_entries) + i, column=0, padx=5, pady=5)
#         bool_var = tk.BooleanVar()
#         bool_checkbox = tk.Checkbutton(outside_obstacle_window, variable=bool_var)
#         bool_checkbox.grid(row=len(str_entries) + len(option_entries) + i, column=1, padx=5, pady=5)
#         bool_entries[text] = bool_var
#     # 创建按钮，用于获取所有输入的数据
#     submit_btn = tk.Button(outside_obstacle_window, text="提交",
#                            command=lambda: get_outside_obstacle_window_data(outside_obstacle_window, str_entries,
#                                                                             option_entries, bool_entries))
#     submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2, padx=5,
#                     pady=5)
#
#
# def get_outside_obstacle_window_data(window, str_entries, option_entries, bool_entries):
#     new_obstacle = {}
#     for text, entry in str_entries.items():
#         print(text + ": ", entry.get())
#         new_obstacle[text] = entry.get()
#     for text, entry in option_entries.items():
#         print(text + ": ", entry.get())
#         new_obstacle[text] = entry.get()
#     for text, entry in bool_entries.items():
#         print(text + ": ", entry.get())
#         new_obstacle[text] = entry.get()
#     outside_obstacle_info.append(new_obstacle)
#     window.destroy()
#
#
# def open_panel_window():
#     panel_window = tk.Toplevel(root)
#     panel_window.title("添加光伏板信息")
#
#     # 直径？长度（mm）？
#     str_text = ["功率", "厚度"]
#     str_entries = {}
#     for i, text in enumerate(str_text):
#         label = tk.Label(panel_window, text=text + ": ")
#         label.grid(row=i, column=0, padx=5, pady=5)
#         entry = tk.Entry(panel_window)
#         entry.grid(row=i, column=1, padx=5, pady=5)
#         str_entries[text] = entry
#     # Frame for installation scheme selection
#     option_text = ["组件类型"]
#     options = [["182-78"]]
#     option_entries = {}
#     for i, (text, option) in enumerate(zip(option_text, options)):
#         label = tk.Label(panel_window, text=text)
#         label.grid(row=len(str_entries) + i, column=0, padx=5, pady=5)
#         scheme_var = tk.StringVar(panel_window)
#         scheme_var.set(option[0])
#         scheme_menu = tk.OptionMenu(panel_window, scheme_var, *option, )
#         scheme_menu.config(width=5)
#         scheme_menu.grid(row=len(str_entries) + i, column=1, padx=5, pady=5)
#         option_entries[text] = scheme_var
#     bool_text = []
#     bool_entries = {}
#     for i, text in enumerate(bool_text):
#         label = tk.Label(panel_window, text=text)
#         label.grid(row=len(str_entries) + len(option_entries) + i, column=0, padx=5, pady=5)
#         bool_var = tk.BooleanVar()
#         bool_checkbox = tk.Checkbutton(panel_window, variable=bool_var)
#         bool_checkbox.grid(row=len(str_entries) + len(option_entries) + i, column=1, padx=5, pady=5)
#         bool_entries[text] = bool_var
#     # 创建按钮，用于获取所有输入的数据
#     submit_btn = tk.Button(panel_window, text="提交",
#                            command=lambda: get_panel_data(panel_window, str_entries, option_entries, bool_entries))
#     submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2, padx=5,
#                     pady=5)
#
#
# def get_panel_data(window, str_entries, option_entries, bool_entries):
#     for text, entry in str_entries.items():
#         print(text + ": ", entry.get())
#         panel_info[text] = entry.get()
#     for text, entry in option_entries.items():
#         print(text + ": ", entry.get())
#         panel_info[text] = entry.get()
#     for text, entry in bool_entries.items():
#         print(text + ": ", entry.get())
#         panel_info[text] = entry.get()
#     window.destroy()
#
#
# def open_algorithm_window():
#     algorithm_window = tk.Toplevel(root)
#     algorithm_window.title("选择算法类型")
#
#     # 直径？长度（mm）？
#     str_text = ["精度（mm）"]
#     str_entries = {}
#     for i, text in enumerate(str_text):
#         label = tk.Label(algorithm_window, text=text + ": ")
#         label.grid(row=i, column=0, padx=5, pady=5)
#         entry = tk.Entry(algorithm_window)
#         entry.grid(row=i, column=1, padx=5, pady=5)
#         str_entries[text] = entry
#     # Frame for installation scheme selection
#     option_text = ["算法类型"]
#     options = [["贪心（单阵列）", "DFS（多阵列）"]]
#     option_entries = {}
#     for i, (text, option) in enumerate(zip(option_text, options)):
#         label = tk.Label(algorithm_window, text=text)
#         label.grid(row=len(str_entries) + i, column=0, padx=5, pady=5)
#         scheme_var = tk.StringVar(algorithm_window)
#         scheme_var.set(option[0])
#         scheme_menu = tk.OptionMenu(algorithm_window, scheme_var, *option, )
#         scheme_menu.config(width=12)
#         scheme_menu.grid(row=len(str_entries) + i, column=1, padx=5, pady=5)
#         option_entries[text] = scheme_var
#     bool_text = []
#     bool_entries = {}
#     for i, text in enumerate(bool_text):
#         label = tk.Label(algorithm_window, text=text)
#         label.grid(row=len(str_entries) + len(option_entries) + i, column=0, padx=5, pady=5)
#         bool_var = tk.BooleanVar()
#         bool_checkbox = tk.Checkbutton(algorithm_window, variable=bool_var)
#         bool_checkbox.grid(row=len(str_entries) + len(option_entries) + i, column=1, padx=5, pady=5)
#         bool_entries[text] = bool_var
#     # 创建按钮，用于获取所有输入的数据
#     submit_btn = tk.Button(algorithm_window, text="提交",
#                            command=lambda: get_algorithm_data(algorithm_window, str_entries, option_entries,
#                                                               bool_entries))
#     submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2, padx=5,
#                     pady=5)
#
#
# def get_algorithm_data(window, str_entries, option_entries, bool_entries):
#     for text, entry in str_entries.items():
#         print(text + ": ", entry.get())
#         panel_info[text] = entry.get()
#     for text, entry in option_entries.items():
#         print(text + ": ", entry.get())
#         panel_info[text] = entry.get()
#     for text, entry in bool_entries.items():
#         print(text + ": ", entry.get())
#         panel_info[text] = entry.get()
#     window.destroy()
#
#
# def draw_roofscene():
#     roofscene_canvas.delete("all")
#
#     draw_width = frame_width - draw_gap * 2
#     draw_height = frame_height - draw_gap * 2
#     # 绘制屋顶
#     scale = min(draw_width / float(roof_info['宽度（mm）']), draw_height / float(roof_info['长度（mm）']))
#     scaled_width = float(roof_info['宽度（mm）']) * scale
#     scaled_height = float(roof_info['长度（mm）']) * scale
#     # 计算矩形位置使其居中
#     roof_left = (frame_width - scaled_width) / 2
#     roof_top = (frame_height - scaled_height) / 2
#     roof_right = roof_left + scaled_width
#     roof_bottom = roof_top + scaled_height
#     # 在 Canvas 上绘制缩放后的矩形
#     # roofscene_canvas.delete("roof")  # 清除之前的矩形
#     roofscene_canvas.create_rectangle(roof_left, roof_top, roof_right, roof_bottom, outline="blue", tags="roof")
#     # 显示屋顶尺寸
#     roofscene_canvas.create_text(int((roof_left + roof_right) / 2), roof_top, text=f"{roof_info['宽度（mm）']}",
#                                  font=("Arial", 12))
#     roofscene_canvas.create_text(roof_left, int((roof_top + roof_bottom) / 2), text=f"{roof_info['长度（mm）']}",
#                                  font=("Arial", 12))
#
#     # 绘制屋内障碍物
#     for obstacle in obstacle_info:
#         try:
#             centerX = float(obstacle['距离西侧屋顶距离'])
#             centerY = float(obstacle['距离北侧屋顶距离'])
#             if obstacle['是否圆形']:
#                 length = float(obstacle['直径']) / 2
#                 x1 = roof_left + (centerX - length) * scale
#                 y1 = roof_top + (centerY - length) * scale
#                 x2 = roof_left + (centerX + length) * scale
#                 y2 = roof_top + (centerY + length) * scale
#                 roofscene_canvas.create_oval(x1, y1, x2, y2, outline='red')
#             else:
#                 width = float(obstacle['宽度（mm）'])
#                 length = float(obstacle['长度（mm）'])
#                 x1 = roof_left + centerX * scale
#                 y1 = roof_top + centerY * scale
#                 x2 = roof_left + (centerX + width) * scale
#                 y2 = roof_top + (centerY + length) * scale
#                 roofscene_canvas.create_rectangle(x1, y1, x2, y2, outline='red')
#         except:
#             continue
#     print(get_input_json())
#
#
# def calculate_layout():
#     jsonData = get_input_json()
#     roof = classes.roof.Roof(jsonData["scene"]["roof"], jsonData["scene"]["location"]["latitude"])
#     # assignComponentParameters(jsonData["component"]) # todo: 传入光伏板参数
#     screenedArrangements = screenArrangements(roof.width, roof.length, jsonData["component"]["specification"],
#                                               jsonData["arrangeType"], jsonData["scene"]["location"]["windPressure"])
#     roof.getValidOptions(screenedArrangements)  # 计算铺设光伏板的最佳方案
#     # 排布完光伏板后再添加障碍物并分析阴影
#     roof.addObstaclesConcern(jsonData["scene"]["roof"]["obstacles"], screenedArrangements)
#     roof.obstacleArraySelf = roof.calculateObstacleSelf()
#     roof.calculate_column(screenedArrangements)
#     return roof.drawPlacement(screenedArrangements)
#
#
# def cal_and_display_layout():
#     global layout_imgs
#     for i in range(5):
#         arrangement_btns[i].config(state="disabled")
#     layout_imgs = calculate_layout()[:5]
#     display_layout()
#     for i in range(len(layout_imgs)):
#         arrangement_btns[i].config(state="active")
#
#
# def display_layout(index=0):
#     global display_img
#     try:
#         image_matrix = layout_imgs[index]
#         image = Image.fromarray(image_matrix)
#         scaled_image = image.resize((frame_width, frame_height))
#         # image.save(os.path.join(file_dir,f"image_{index}.png"))
#         # scaled_image.save(os.path.join(file_dir,f"scaled_image_{index}.png"))
#         display_img = ImageTk.PhotoImage(scaled_image)
#         arrangement_canvas.create_image(0, 0, anchor=tk.NW, image=display_img)
#     except Exception as e:
#         print("Exception", e)
#
#
# def clear_info():
#     global location_info
#     global roof_info
#     global outside_obstacle_info
#     global panel_info
#     global obstacle_info
#     global algorithm_info
#
#     location_info = {}
#     roof_info = {}
#     obstacle_info = []
#     outside_obstacle_info = []
#     panel_info = {}
#     algorithm_info = {}
#     roofscene_canvas.delete("all")
#
#
# def get_demo_input(index=0):
#     with open(os.path.join(file_dir, f'input{index}.json'), 'r', encoding='utf-8') as f:
#         input_json = json.load(f)
#
#     if "scene" in input_json:
#         if "location" in input_json["scene"]:
#             for key, value in input_json["scene"]["location"].items():
#                 location_info[eng2chn[key]] = value
#
#         if "roof" in input_json["scene"]:
#             for key, value in input_json["scene"]["roof"].items():
#                 try:
#                     roof_info[eng2chn[key]] = value
#                 except:
#                     roof_info[key] = value
#             if 'extensibleDistance' in roof_info:
#                 roof_info["可探出距离（东）"] = roof_info["extensibleDistance"][0]
#                 roof_info["可探出距离（西）"] = roof_info["extensibleDistance"][1]
#                 roof_info["可探出距离（南）"] = roof_info["extensibleDistance"][2]
#                 roof_info["可探出距离（北）"] = roof_info["extensibleDistance"][3]
#             if 'parapetWall' in roof_info:
#                 for key, value in roof_info['parapetWall'].items():
#                     roof_info['parapetWall' + key] = value
#
#             if "obstacles" in input_json["scene"]["roof"]:
#                 for obstacle in input_json["scene"]["roof"]["obstacles"]:
#                     new_item = {}
#                     for key, value in obstacle.items():
#                         try:
#                             new_item[eng2chn[key]] = value
#                         except:
#                             new_item[key] = value
#                     if obstacle['isRound']:
#                         new_item[eng2chn['relativePositionX']] = new_item['centerPosition'][0]
#                         new_item[eng2chn['relativePositionY']] = new_item['centerPosition'][1]
#                     else:
#                         new_item[eng2chn['relativePositionX']] = new_item['upLeftPosition'][0]
#                         new_item[eng2chn['relativePositionY']] = new_item['upLeftPosition'][1]
#                     obstacle_info.append(new_item)
#
#     # if "obstacles" in input_json:
#     # for key, value in input_json["obstacles"].items():
#     #     outside_obstacle_info[eng2chn[key]] = value
#
#     if "component" in input_json:
#         for key, value in input_json["component"].items():
#             panel_info[eng2chn[key]] = value
#
#     if "algorithm" in input_json:
#         for key, value in input_json["algorithm"].items():
#             algorithm_info[eng2chn[key]] = value
#
#     draw_roofscene()
#     return input_json
#
#
# def get_input_json():
#     input_json = {}
#     # guest
#     input_json["guest"] = {}
#     input_json["guest"]["name"] = ""
#     input_json["guest"]["phone"] = ""
#     # scene
#     # location
#     input_json["scene"] = {}
#     input_json["scene"]["location"] = {}
#     for key, value in location_info.items():
#         input_json["scene"]["location"][chn2eng[key]] = value
#     # roof
#     input_json["scene"]["roof"] = {}
#     input_json["scene"]["roof"]["parapetWall"] = {}
#     extensibleDistance = [0, 0, 0, 0]
#     for key, value in roof_info.items():
#         try:
#             new_key = chn2eng[key]
#         except:
#             continue
#         if 'parapetWall' in new_key:
#             input_json["scene"]["roof"]["parapetWall"][new_key[len("parapetWall"):]] = value
#         elif 'extensibleDistance' in new_key:
#             if 'East' in new_key:
#                 extensibleDistance[0] = value
#             if 'West' in new_key:
#                 extensibleDistance[1] = value
#             if 'South' in new_key:
#                 extensibleDistance[2] = value
#             if 'North' in new_key:
#                 extensibleDistance[3] = value
#         else:
#             input_json["scene"]["roof"][new_key] = value
#     input_json["scene"]["roof"]["extensibleDistance"] = extensibleDistance
#     # obstacle in roof
#     input_json["scene"]["roof"]["obstacles"] = []
#     for obstacle in obstacle_info:
#         new_item = {}
#         position = [0, 0]
#         for key, value in obstacle.items():
#             try:
#                 new_key = chn2eng[key]
#             except:
#                 continue
#             if "relativePositionX" == new_key:
#                 position[0] = value
#             elif "relativePositionY" == new_key:
#                 position[1] = value
#             else:
#                 new_item[new_key] = value
#         if new_item["isRound"]:
#             new_item["centerPosition"] = position
#         else:
#             new_item["upLeftPosition"] = position
#
#         input_json["scene"]["roof"]["obstacles"].append(new_item)
#     # arrangeType
#     input_json["arrangeType"] = scheme_var.get()
#     # component
#     input_json["component"] = {}
#     input_json["component"]["specification"] = ""
#     for key, value in panel_info.items():
#         input_json["component"][chn2eng[key]] = value
#
#     # algorithm
#     input_json["algorithm"] = {}
#     for key, value in panel_info.items():
#         input_json["algorithm"][chn2eng[key]] = value
#
#     return input_json
#
#
# root = tk.Tk()
#
#
# def on_closing():
#     root.quit()
#     root.destroy()
#
#
# # 绑定窗口关闭事件
# root.protocol("WM_DELETE_WINDOW", on_closing)
# root.title("光伏板排布计算")
# # 创建左侧的按钮
# left_frame = tk.Frame(root)
# left_frame.pack(side=tk.LEFT, padx=20, pady=20)
# # Buttons for adding information
# location_btn = tk.Button(left_frame, text="添加位置信息", command=open_location_window)
# location_btn.pack(fill=tk.X, pady=5)
# roof_btn = tk.Button(left_frame, text="添加屋顶信息", command=open_roof_window)
# roof_btn.pack(fill=tk.X, pady=5)
# obstacle_btn = tk.Button(left_frame, text="添加屋内障碍物信息", command=open_obstacle_window)
# obstacle_btn.pack(fill=tk.X, pady=5)
# outside_obstacle_btn = tk.Button(left_frame, text="添加屋外障碍物信息", command=open_obstacle_window)
# outside_obstacle_btn.pack(fill=tk.X, pady=5)
# panel_btn = tk.Button(left_frame, text="添加光伏板信息", command=open_panel_window)
# panel_btn.pack(fill=tk.X, pady=5)
# clear_btn = tk.Button(left_frame, text="清空输入信息", command=clear_info)
# clear_btn.pack(fill=tk.X, pady=5)
# # Frame for installation scheme selection
# scheme_frame = tk.Frame(left_frame)
# scheme_frame.pack(fill=tk.X)
# # Installation scheme selection
# scheme_label = tk.Label(scheme_frame, text="安装方案")
# scheme_label.pack(side=tk.LEFT)
# scheme_options = ["膨胀常规", "膨胀抬高", "基墩"]
# scheme_var = tk.StringVar(scheme_frame)
# scheme_var.set(scheme_options[0])
# scheme_menu = tk.OptionMenu(scheme_frame, scheme_var, *scheme_options, )
# scheme_menu.config(width=10)
# scheme_menu.pack(side=tk.LEFT)
# # Button to calculate PV panel layout
# draw_btn = tk.Button(left_frame, text="展示屋面场景", command=draw_roofscene)
# draw_btn.pack(fill=tk.X, pady=(0, 20))
# algorithm_btn = tk.Button(left_frame, text="选择算法类型", command=open_algorithm_window)
# algorithm_btn.pack(fill=tk.X, pady=0)
# calculate_btn = tk.Button(left_frame, text="计算光伏板排布", command=cal_and_display_layout)
# calculate_btn.pack(fill=tk.X, pady=(0, 20))
#
# # 创建右侧的区域，包括“原始拓扑”文字标签和图片显示区域
# arrangement_frame = tk.Frame(root)
# arrangement_frame.pack(side=tk.RIGHT, padx=20, pady=20)
#
# # “原始拓扑”文字标签放置在右侧区域的顶部
# arrangement_text = tk.Label(arrangement_frame, text="组件排布", font=("Arial", 12))
# arrangement_text.pack()
#
# # 图片显示区域放置在“原始拓扑”文字标签下方
# # arrangement_display_frame = tk.Frame(arrangement_frame, width=frame_width, height=frame_height, bg='grey')
# # arrangement_display_frame.pack_propagate(0)  # 防止内部元素影响尺寸
# # arrangement_display_frame.pack()
#
# arrangement_canvas = tk.Canvas(arrangement_frame, width=frame_width, height=frame_height, bg='grey')
# arrangement_canvas.pack()
#
# # “原始拓扑”文字标签放置在右侧区域的顶部
# arrangement_btn_text = tk.Label(arrangement_frame, text="点击按钮查看对应排序的结果：", font=("Arial", 12))
# arrangement_btn_text.pack(side=tk.LEFT, anchor=tk.SW, padx=(0, 5), pady=(5, 0))
#
# # 界面切换按钮
# arrangement_btns = []
# for i in range(5):
#     arrangement_btn = tk.Button(arrangement_frame, text=f"{i + 1}", command=partial(display_layout, i))
#     arrangement_btn.pack(side=tk.LEFT, anchor=tk.SW, padx=(0, 5), pady=(5, 0))
#     arrangement_btn.config(state="disabled")
#     arrangement_btns.append(arrangement_btn)
#
# # 创建右侧的区域，包括“原始拓扑”文字标签和图片显示区域
# roofscene_frame = tk.Frame(root)
# roofscene_frame.pack(side=tk.RIGHT, padx=20, pady=20)
# # “原始拓扑”文字标签放置在右侧区域的顶部
# roofscene_text = tk.Label(roofscene_frame, text="屋面场景", font=("Arial", 12))
# roofscene_text.pack()
#
# # # 图片显示区域放置在“原始拓扑”文字标签下方
# # roofscene_canvas_frame = tk.Frame(roofscene_frame, width=frame_width, height=frame_height, bg='grey')
# # roofscene_canvas_frame.pack()
# # roofscene_canvas_frame.pack_propagate(0)  # 防止内部元素影响尺寸
#
# roofscene_canvas = tk.Canvas(roofscene_frame, width=frame_width, height=frame_height, bg='grey')
# roofscene_canvas.pack()
#
# # “原始拓扑”文字标签放置在右侧区域的顶部
# roofscene_btn_text = tk.Label(roofscene_frame, text="选择输入示例：", font=("Arial", 12))
# roofscene_btn_text.pack(side=tk.LEFT, anchor=tk.SW, padx=(0, 5), pady=(5, 0))
#
# # 界面切换按钮
# roofscene_btns = []
# for i in range(5):
#     roofscene_btn = tk.Button(roofscene_frame, text=f"{i + 1}", command=partial(get_demo_input, i))
#     roofscene_btn.pack(side=tk.LEFT, anchor=tk.SW, padx=(0, 5), pady=(5, 0))
#     if os.path.exists(os.path.join(file_dir, f"input{i}.json")):
#         roofscene_btn.config(state="active")
#     else:
#         roofscene_btn.config(state="disabled")
#     roofscene_btns.append(roofscene_btn)
#
#
# # empty_text = tk.Label(roofscene_frame, text="", font=("Arial", 12))
# # empty_text.pack(side=tk.LEFT, anchor=tk.SW, padx=(0, 5), pady=(5, 0))
# def main():
#     root.mainloop()
#
#
# if __name__ == "__main__":
#     root.mainloop()
