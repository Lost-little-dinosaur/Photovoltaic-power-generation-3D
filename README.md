# Photovoltaic-power-generation-3D

浙大软院VIPA实验室光伏发电排布生成项目3D版本

## 注意事项

1. 输入输出的单位均为毫米
2. 任何坐标都以[x,y]的形式表示，其中x为横坐标，y为纵坐标
3. 数组索引时矩阵时，如果是二维数组，则第一个表示的是y，第二个表示的是x
4. 数组索引时矩阵时，如果是三维数组，则第一个表示的是x，第二个表示的是y，第三个表示的是z
5. length都是指y方向的长度，width都是指x方向的长度
6. placement中的元素意义为：[[放置的arrangement的ID和startXY],当前value,扣除前的obstacleArray,[扣除的光伏板下标(从左到右从上到下,长度和placement[0]一样),立柱排布]
