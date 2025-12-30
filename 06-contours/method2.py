import cv2
import numpy as np



if __name__ == "__main__":
    img = cv2.imread("main_area.png")
    # 转换为 HSV 颜色空间
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 黑色的颜色范围
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([180, 255, 250])  # 可根据图像调整亮度上限

    # 创建掩膜
    mask = cv2.inRange(hsv, lower_black, upper_black)

    # 可选：形态学操作去噪
    kernel = np.ones((2,2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    kernel = np.ones((5, 5), np.uint8)   # 定义结构元素
    mask = cv2.dilate(mask, kernel, iterations=2)

    # 提取等高线轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # 在白底上绘制黑线结果
    result = np.ones_like(img) * 255
    cv2.drawContours(result, contours, -1, (0,0,0), 1)

    cv2.imwrite("contours.png", result)

    # # 转灰度
    # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # # 自适应阈值（突出黑色等高线）
    # thresh = cv2.adaptiveThreshold(
    #     gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 10
    # )
    # edges = cv2.Canny(thresh, 100, 200)
    # kernel = np.ones((1, 1), np.uint8)   # 定义结构元素
    # edges = cv2.dilate(edges, kernel, iterations=1)

    # cv2.imwrite("edges.png", edges)
    # contours, hierarchy = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    # # 在原图上画出来
    # contour_img = np.ones_like(img) * 255
    # cv2.drawContours(contour_img, contours, -1, (0,0,255), 1)
    # cv2.imwrite("contours.png", contour_img)
    