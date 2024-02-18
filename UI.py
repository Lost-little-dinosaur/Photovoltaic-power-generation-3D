import tkinter as tk

location_info = {}
roof_info = {}
obstacle_info = []
outside_obstacle_info = []
panel_info = {}
frame_width = 420
frame_height = 320
draw_gap = 10
root = None


def open_location_window():
    location_window = tk.Toplevel(root)
    location_window.title("添加位置信息")

    str_text = ["省份", "城市", "行政区", "经度", "纬度", "电压等级", "距离并网点的距离"]
    str_entries = {}
    for i, text in enumerate(str_text):
        label = tk.Label(location_window, text=text + ": ")
        label.grid(row=i, column=0, padx=5, pady=5)

        entry = tk.Entry(location_window)
        entry.grid(row=i, column=1, padx=5, pady=5)
        str_entries[text] = entry

    # Frame for installation scheme selection
    option_text = ["风压", "雪压", "风雪压"]
    options = [["低压", "高压"], ["低压", "高压"], ["低压", "高压"]]
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

    bool_text = ["大雪"]
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
                           command=lambda: get_location_data(location_window, str_entries, option_entries,
                                                             bool_entries))
    submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2, padx=5,
                    pady=5)


def get_location_data(window, str_entries, option_entries, bool_entries):
    for text, entry in str_entries.items():
        print(text + ": ", entry.get())
        location_info[text] = entry.get()
    for text, entry in option_entries.items():
        print(text + ": ", entry.get())
        location_info[text] = entry.get()
    for text, entry in bool_entries.items():
        print(text + ": ", entry.get())
        location_info[text] = entry.get()
    window.destroy()


def open_roof_window():
    roof_window = tk.Toplevel(root)
    roof_window.title("添加屋顶信息")

    str_text = ["长度", "宽度", "高度", "偏移角度", "倾斜角度", "可探出距离（东）"
        , "可探出距离（南）", "可探出距离（西）", "可探出距离（北）",
                "女儿墙厚度", "女儿墙高度（东）", "女儿墙高度（南）", "女儿墙高度（西）", "女儿墙高度（北）"]
    str_entries = {}
    for i, text in enumerate(str_text):
        label = tk.Label(roof_window, text=text + ": ")
        label.grid(row=i, column=0, padx=5, pady=5)

        entry = tk.Entry(roof_window)
        entry.grid(row=i, column=1, padx=5, pady=5)
        str_entries[text] = entry

    # Frame for installation scheme selection
    option_text = ["屋顶类型"]
    options = [["平屋顶", "斜屋顶"]]
    option_entries = {}
    for i, (text, option) in enumerate(zip(option_text, options)):
        label = tk.Label(roof_window, text=text)
        label.grid(row=len(str_entries) + i, column=0, padx=5, pady=5)
        scheme_var = tk.StringVar(roof_window)
        scheme_var.set(option[0])
        scheme_menu = tk.OptionMenu(roof_window, scheme_var, *option, )
        scheme_menu.config(width=5)
        scheme_menu.grid(row=len(str_entries) + i, column=1, padx=5, pady=5)
        option_entries[text] = scheme_var

    bool_text = ["复杂屋顶", "预留运维通道"]
    bool_entries = {}
    for i, text in enumerate(bool_text):
        label = tk.Label(roof_window, text=text)
        label.grid(row=len(str_entries) + len(option_entries) + i, column=0, padx=5, pady=5)
        bool_var = tk.BooleanVar()
        bool_checkbox = tk.Checkbutton(roof_window, variable=bool_var)
        bool_checkbox.grid(row=len(str_entries) + len(option_entries) + i, column=1, padx=5, pady=5)
        bool_entries[text] = bool_var

    # 创建按钮，用于获取所有输入的数据
    submit_btn = tk.Button(roof_window, text="提交",
                           command=lambda: get_roof_data(roof_window, str_entries, option_entries, bool_entries))
    submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2, padx=5,
                    pady=5)


def get_roof_data(window, str_entries, option_entries, bool_entries):
    for text, entry in str_entries.items():
        print(text + ": ", entry.get())
        roof_info[text] = entry.get()
    for text, entry in option_entries.items():
        print(text + ": ", entry.get())
        roof_info[text] = entry.get()
    for text, entry in bool_entries.items():
        print(text + ": ", entry.get())
        roof_info[text] = entry.get()
    window.destroy()


def open_obstacle_window():
    obstacle_window = tk.Toplevel(root)
    obstacle_window.title("添加墙内障碍物信息")

    # 直径？长度？
    str_text = ["ID", "直径", "长度", "宽度", "高度", "距离西侧屋顶距离", "距离北侧屋顶距离", "可调整高度"]
    str_entries = {}
    for i, text in enumerate(str_text):
        label = tk.Label(obstacle_window, text=text + ": ")
        label.grid(row=i, column=0, padx=5, pady=5)

        entry = tk.Entry(obstacle_window)
        entry.grid(row=i, column=1, padx=5, pady=5)
        str_entries[text] = entry

    # Frame for installation scheme selection
    option_text = ["类型"]
    options = [["无烟烟囱", "有烟烟囱"]]
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

    bool_text = ["是否圆形", "是否可移除"]
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
                           command=lambda: get_obstacle_data(obstacle_window, str_entries, option_entries,
                                                             bool_entries))
    submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2, padx=5,
                    pady=5)


def get_obstacle_data(window, str_entries, option_entries, bool_entries):
    new_obstacle = {}
    for text, entry in str_entries.items():
        print(text + ": ", entry.get())
        new_obstacle[text] = entry.get()
    for text, entry in option_entries.items():
        print(text + ": ", entry.get())
        new_obstacle[text] = entry.get()
    for text, entry in bool_entries.items():
        print(text + ": ", entry.get())
        new_obstacle[text] = entry.get()
    obstacle_info.append(new_obstacle)
    window.destroy()


def open_outside_obstacle_window():
    outside_obstacle_window = tk.Toplevel(root)
    outside_obstacle_window.title("添加墙内障碍物信息")

    # 直径？长度？
    str_text = ["ID", "直径", "长度", "宽度", "高度", "距离西侧屋顶距离", "距离北侧屋顶距离", "可调整高度"]
    str_entries = {}
    for i, text in enumerate(str_text):
        label = tk.Label(outside_obstacle_window, text=text + ": ")
        label.grid(row=i, column=0, padx=5, pady=5)

        entry = tk.Entry(outside_obstacle_window)
        entry.grid(row=i, column=1, padx=5, pady=5)
        str_entries[text] = entry

    # Frame for installation scheme selection
    option_text = ["类型"]
    options = [["房屋", "树"]]
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

    bool_text = ["是否圆形", "是否可移除"]
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
                           command=lambda: get_outside_obstacle_window_data(outside_obstacle_window, str_entries,
                                                                            option_entries, bool_entries))
    submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2, padx=5,
                    pady=5)


def get_outside_obstacle_window_data(window, str_entries, option_entries, bool_entries):
    new_obstacle = {}
    for text, entry in str_entries.items():
        print(text + ": ", entry.get())
        new_obstacle[text] = entry.get()
    for text, entry in option_entries.items():
        print(text + ": ", entry.get())
        new_obstacle[text] = entry.get()
    for text, entry in bool_entries.items():
        print(text + ": ", entry.get())
        new_obstacle[text] = entry.get()
    outside_obstacle_info.append(new_obstacle)
    window.destroy()


def open_panel_window():
    panel_window = tk.Toplevel(root)
    panel_window.title("添加光伏板信息")

    # 直径？长度？
    str_text = ["功率", "厚度"]
    str_entries = {}
    for i, text in enumerate(str_text):
        label = tk.Label(panel_window, text=text + ": ")
        label.grid(row=i, column=0, padx=5, pady=5)

        entry = tk.Entry(panel_window)
        entry.grid(row=i, column=1, padx=5, pady=5)
        str_entries[text] = entry

    # Frame for installation scheme selection
    option_text = ["组件类型"]
    options = [["182-78"]]
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

    bool_text = []
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
                           command=lambda: get_panel_data(panel_window, str_entries, option_entries, bool_entries))
    submit_btn.grid(row=len(str_entries) + len(option_entries) + len(bool_entries) + 1, column=0, columnspan=2, padx=5,
                    pady=5)


def get_panel_data(window, str_entries, option_entries, bool_entries):
    for text, entry in str_entries.items():
        print(text + ": ", entry.get())
        panel_info[text] = entry.get()
    for text, entry in option_entries.items():
        print(text + ": ", entry.get())
        panel_info[text] = entry.get()
    for text, entry in bool_entries.items():
        print(text + ": ", entry.get())
        panel_info[text] = entry.get()
    window.destroy()


def draw_roofscene():
    roofscene_canvas.delete("all")

    draw_width = frame_width - draw_gap * 2
    draw_height = frame_height - draw_gap * 2

    # 绘制屋顶
    scale = min(draw_width / float(roof_info['长度']), draw_height / float(roof_info['宽度']))
    scaled_width = float(roof_info['长度']) * scale
    scaled_height = float(roof_info['宽度']) * scale
    # 计算矩形位置使其居中
    roof_left = (frame_width - scaled_width) / 2
    roof_top = (frame_height - scaled_height) / 2
    roof_right = roof_left + scaled_width
    roof_bottom = roof_top + scaled_height
    # 在 Canvas 上绘制缩放后的矩形
    # roofscene_canvas.delete("roof")  # 清除之前的矩形
    roofscene_canvas.create_rectangle(roof_left, roof_top, roof_right, roof_bottom, outline="blue", tags="roof")

    # 绘制屋内障碍物
    for obstacle in obstacle_info:
        centerX = float(obstacle['距离西侧屋顶距离'])
        centerY = float(obstacle['距离北侧屋顶距离'])

        if obstacle['是否圆形']:
            length = float(obstacle['直径']) / 2
            x1 = roof_left + (centerX - length) * scale
            y1 = roof_top + (centerY - length) * scale
            x2 = roof_left + (centerX + length) * scale
            y2 = roof_top + (centerY + length) * scale
            roofscene_canvas.create_oval(x1, y1, x2, y2, outline='red')
        else:
            width = float(obstacle['长度']) / 2
            length = float(obstacle['宽度']) / 2
            x1 = roof_left + (centerX - width) * scale
            y1 = roof_top + (centerY - length) * scale
            x2 = roof_left + (centerX + width) * scale
            y2 = roof_top + (centerY + length) * scale
            roofscene_canvas.create_rectangle(x1, y1, x2, y2, outline='red')


def calculate_layout():
    # Perform calculation for PV panel layout based on selected installation scheme
    print("Calculating PV panel layout...")


def clear_info():
    location_info = {}
    roof_info = {}
    obstacle_info = []
    outside_obstacle_info = []
    panel_info = {}
    roofscene_canvas.delete("all")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("光伏板排布计算")

    # 创建左侧的按钮
    left_frame = tk.Frame(root)
    left_frame.pack(side=tk.LEFT, padx=20, pady=20)

    # Buttons for adding information
    location_btn = tk.Button(left_frame, text="添加位置信息", command=open_location_window)
    location_btn.pack(fill=tk.X, pady=5)

    roof_btn = tk.Button(left_frame, text="添加屋顶信息", command=open_roof_window)
    roof_btn.pack(fill=tk.X, pady=5)

    obstacle_btn = tk.Button(left_frame, text="添加屋内障碍物信息", command=open_obstacle_window)
    obstacle_btn.pack(fill=tk.X, pady=5)

    outside_obstacle_btn = tk.Button(left_frame, text="添加屋外障碍物信息", command=open_obstacle_window)
    outside_obstacle_btn.pack(fill=tk.X, pady=5)

    panel_btn = tk.Button(left_frame, text="添加光伏板信息", command=open_panel_window)
    panel_btn.pack(fill=tk.X, pady=5)

    clear_btn = tk.Button(left_frame, text="清空输入信息", command=clear_info)
    clear_btn.pack(fill=tk.X, pady=5)

    # Frame for installation scheme selection
    scheme_frame = tk.Frame(left_frame)
    scheme_frame.pack(fill=tk.X)

    # Installation scheme selection
    scheme_label = tk.Label(scheme_frame, text="安装方案")
    scheme_label.pack(side=tk.LEFT)

    scheme_options = ["膨胀常规", "膨胀抬高", "基墩"]j
    scheme_var = tk.StringVar(scheme_frame)
    scheme_var.set(scheme_options[0])
    scheme_menu = tk.OptionMenu(scheme_frame, scheme_var, *scheme_options, )
    scheme_menu.config(width=10)
    scheme_menu.pack(side=tk.LEFT)

    # Button to calculate PV panel layout
    draw_btn = tk.Button(left_frame, text="展示屋面场景", command=draw_roofscene)
    draw_btn.pack(fill=tk.X, pady=20)

    calculate_btn = tk.Button(left_frame, text="计算光伏板排布", command=calculate_layout)
    calculate_btn.pack(fill=tk.X, pady=20)

    # 创建右侧的区域，包括“原始拓扑”文字标签和图片显示区域
    arrangement_frame = tk.Frame(root)
    arrangement_frame.pack(side=tk.RIGHT, padx=20, pady=20)

    # “原始拓扑”文字标签放置在右侧区域的顶部
    arrangement_text = tk.Label(arrangement_frame, text="组件排布", font=("Arial", 12))
    arrangement_text.pack()

    # 图片显示区域放置在“原始拓扑”文字标签下方
    arrangement_frame = tk.Frame(arrangement_frame, width=frame_width, height=frame_height, bg='grey')
    arrangement_frame.pack()
    arrangement_frame.pack_propagate(0)  # 防止内部元素影响尺寸

    # 创建右侧的区域，包括“原始拓扑”文字标签和图片显示区域
    roofscene_frame = tk.Frame(root)
    roofscene_frame.pack(side=tk.RIGHT, padx=20, pady=20)

    # “原始拓扑”文字标签放置在右侧区域的顶部
    roofscene_text = tk.Label(roofscene_frame, text="屋面场景", font=("Arial", 12))
    roofscene_text.pack()

    # 图片显示区域放置在“原始拓扑”文字标签下方
    roofscene_frame = tk.Frame(roofscene_frame, width=frame_width, height=frame_height, bg='grey')
    roofscene_frame.pack()
    roofscene_frame.pack_propagate(0)  # 防止内部元素影响尺寸

    roofscene_canvas = tk.Canvas(roofscene_frame, width=frame_width, height=frame_height, bg='grey')
    roofscene_canvas.pack()

    root.mainloop()
