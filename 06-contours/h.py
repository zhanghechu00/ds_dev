import cv2
import numpy as np
import random

# === 1. 读取图像 ===
binary = cv2.imread('binary2.png', cv2.IMREAD_GRAYSCALE)

# === 2. 提取轮廓及层级关系 ===
contours, hierarchy = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# 转为彩色方便画线
color_img = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

# === 3. 定义颜色生成函数 ===
def random_color(level):
    """不同层级使用不同颜色，层级越深颜色越亮"""
    random.seed(level)
    return (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

# === 4. 遍历绘制所有轮廓 ===
for i, c in enumerate(contours):
    # 获取当前轮廓层级（通过父索引计数）
    level = 0
    parent = hierarchy[0][i][3]
    while parent != -1:
        parent = hierarchy[0][parent][3]
        level += 1
    
    # 颜色由层级控制
    color = random_color(level)
    
    # 绘制轮廓
    cv2.drawContours(color_img, [c], -1, color, 2)

    # 在轮廓中心标注编号
    M = cv2.moments(c)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        cv2.putText(color_img, str(level), (cx - 10, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

# === 5. 显示与保存结果 ===
cv2.imshow("Contours with Hierarchy", color_img)
cv2.waitKey(0)
cv2.destroyAllWindows()
cv2.imwrite("contours_hierarchy_colored.png", color_img)

# === 6. 打印 hierarchy 信息 ===
print("Hierarchy structure:")
for i, h in enumerate(hierarchy[0]):
    print(f"轮廓 {i}: next={h[0]}, prev={h[1]}, child={h[2]}, parent={h[3]}")
