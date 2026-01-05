import sys
print("DEBUG: Script starting imports...", flush=True)
import cv2
import numpy as np
import pytesseract
from collections import defaultdict
import argparse
import os
from pathlib import Path
print("DEBUG: Imports finished.", flush=True)

def _configure_tesseract() -> None:
    """Prefer the intended Tesseract install (e.g. 5.5) and its tessdata.

    This avoids accidentally using an older Tesseract from PATH (often 3.0).
    """
    candidates: list[str] = []
    if os.environ.get("TESSERACT_CMD"):
        candidates.append(os.environ["TESSERACT_CMD"])
    if os.environ.get("TESSERACT_EXE"):
        candidates.append(os.environ["TESSERACT_EXE"])

    # Prefer 64-bit default install location first.
    candidates.extend(
        [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
    )

    chosen: str | None = None
    for exe in candidates:
        if exe and Path(exe).exists():
            chosen = exe
            break

    if chosen:
        pytesseract.pytesseract.tesseract_cmd = chosen

        # Ensure tessdata is discoverable; Tesseract expects TESSDATA_PREFIX to
        # point to the tessdata directory.
        tessdata_dir = Path(chosen).parent / "tessdata"
        if tessdata_dir.exists() and not os.environ.get("TESSDATA_PREFIX"):
            os.environ["TESSDATA_PREFIX"] = str(tessdata_dir)

    # Best-effort: print version for debugging.
    try:
        import subprocess

        cmd = pytesseract.pytesseract.tesseract_cmd or "tesseract"
        out = subprocess.check_output([cmd, "--version"], stderr=subprocess.STDOUT, text=True)
        first_line = out.splitlines()[0] if out else ""
        print(f"DEBUG: Using tesseract: {cmd} ({first_line})", flush=True)
        if os.environ.get("TESSDATA_PREFIX"):
            print(f"DEBUG: TESSDATA_PREFIX={os.environ['TESSDATA_PREFIX']}", flush=True)
    except Exception as e:
        print(f"DEBUG: Could not query tesseract version: {e}", flush=True)


_configure_tesseract()

def extract_frames(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray[gray < 10] = 255  # 将接近黑色的像素设为白色
    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
    # cv2.imwrite("binary111.png", binary)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL , cv2.CHAIN_APPROX_SIMPLE)
    max_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(max_contour)
    print(f"Bounding box: x={x}, y={y}, w={w}, h={h}")
    border_area = img.copy()
    cropped = img[y:y+h, x:x+w]
    cv2.rectangle(border_area, (x, y), (x+w, y+h), (255, 255, 255), -1)  # 将主图区域涂白
    return border_area, cropped

def process_border_area(border_area):
    gray = cv2.cvtColor(border_area, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
    cv2.imwrite("binary2.png", binary)
    contours, hierarchy = cv2.findContours(binary, cv2.RETR_CCOMP , cv2.CHAIN_APPROX_SIMPLE)
    print(f"Found {len(contours)} contours in border area")
    # print(hierarchy)
    rcontours = []
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        rcontours.append((area, contour))
    rcontours.sort(key=lambda x: x[0], reverse=True)
    rareas = [area for area, cnt in rcontours]
    orders = [int(np.log10(x)) for x in rareas if x > 0]
    groups = defaultdict(list)
    for n, o in zip(rareas, orders):
        groups[o].append(n)
    # 输出最大组（数量级一致最多的那类）
    largest_group = max(groups.values(), key=len)
    mg = max(largest_group)
    num_max_contours = largest_group.count(mg)
    rcontours = rcontours[:num_max_contours]
    rcontours = [cnt for area, cnt in rcontours]
    # print(f"Selected top {num_max_contours} contours with areas: {rareas}")
    ret_area = border_area.copy()
    b_area = border_area.copy()
    # border_area = cv2.drawContours(border_area, rcontours, -1, (0, 0, 255), 2) 
    # 最外侧的轮廓
    x, y, w, h = cv2.boundingRect(rcontours[0])
    # 分离坐标轴轮廓
    x1, y1, w1, h1 = cv2.boundingRect(rcontours[-1])
    inner_area = ret_area[y1+1:y1+h1, x1+1:x1+w1]
    b_area[y1+1:y1+h1, x1+1:x1+w1] = (255, 255, 255)
    box_area = b_area[y+1:y+h, x+1:x+w]
    box_cord = (x, y, w, h)
    inner_cord = (x1, y1, w1, h1)
    return box_area, box_cord,inner_area,inner_cord

def process_color_bar(inner_area):
    b, g, r = cv2.split(inner_area)
    threshold = 55
    mask = (b < threshold) & (g < threshold) & (r < threshold)
    mask = mask.astype(np.uint8) * 255
    inner_area_text = inner_area.copy()
    inner_area[mask == 255] = [255, 255, 255]
    # cv2.imwrite("colorbar_masked.png", inner_area)
    
    gray = cv2.cvtColor(inner_area, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
    col_sum = np.sum(binary, axis=0).astype(np.float32)
    col_sum_smooth = cv2.GaussianBlur(col_sum.reshape(1, -1), (1, 15), 0).flatten()
    col_sum_smooth = col_sum_smooth / np.max(col_sum_smooth)

    threshold = 0.23
    mask = col_sum_smooth > threshold
    indices = np.where(mask)[0]
    x1, x2 = indices[0], indices[-1]
    colorbar = inner_area[:, x1:x2, :]

    colorbar_text = inner_area_text[:, x1:, :]
    # cv2.imwrite("colorbar_text.png", colorbar_text)

    gray = cv2.cvtColor(colorbar, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
    col_sum = np.sum(binary, axis=1).astype(np.float32)
    col_sum_smooth = cv2.GaussianBlur(col_sum.reshape(-1, 1), (1, 15), 0).flatten()
    col_sum_smooth = col_sum_smooth / np.max(col_sum_smooth)
    threshold = 0.5
    mask = col_sum_smooth > threshold
    indices = np.where(mask)[0]
    # print(indices)
    x1, x2 = indices[0], indices[-1]
    colorbar = colorbar[x1+1:x2-1,:, :]
    cv2.imwrite("colorbar_detect.png", colorbar)
    # print(colorbar.shape)
    b, g, r = cv2.split(colorbar)
    col_sum_b = np.sum(b, axis=1)//colorbar.shape[1]
    col_sum_g = np.sum(g, axis=1)//colorbar.shape[1]
    col_sum_r = np.sum(r, axis=1)//colorbar.shape[1]
    # print(col_sum_b.shape)
    merged = cv2.merge([col_sum_b.astype(np.uint8), col_sum_g.astype(np.uint8), col_sum_r.astype(np.uint8)])
    # np.set_printoptions(threshold=sys.maxsize)
    # print(merged)
    
    print("Extracting colorbar text numbers...")
    colorbar_text  = cv2.cvtColor(colorbar_text, cv2.COLOR_BGR2GRAY)
    colorbar_text  = cv2.bitwise_not(colorbar_text )  # 如果数字是黑色背景，反转
    _, binary = cv2.threshold(colorbar_text , 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    col_sum = np.sum(binary, axis=1).astype(np.float32)
    col_sum_smooth = cv2.GaussianBlur(col_sum.reshape(-1, 1), (1, 15), 0).flatten()
    col_sum_smooth = col_sum_smooth / np.max(col_sum_smooth)
    threshold = 0.5
    mask = col_sum_smooth > threshold
    indices = np.where(mask)[0]
    x1, x2 = indices[0], indices[-1]
    colorbar_text = colorbar_text[x1-20:x2+20,:]
    colorbar_text[colorbar_text<200] = 0
    colorbar_text = cv2.GaussianBlur(colorbar_text, (3, 3), 0)
    cv2.imwrite("colorbar_text.png", colorbar_text)
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=-0123456789.'
    text = pytesseract.image_to_string(colorbar_text, config=custom_config)
    # print("Raw OCR text:", text)
    text = text.split("\n")
    heights = [ float(t) for t in text if len(t)>0]
    heights = sorted(heights, reverse=False)
    return merged, heights

def extrac_from_main(main_area,merged,coord,heights):
    # main_area = main_area[1:-2,1:-2]
    # print("main_area ",main_area.shape,merged.shape)
    target_color = main_area[coord[0]][coord[1]]
    # print("target_color",target_color)
    if target_color[0] > 240 and target_color[1] > 240 and target_color[2] > 240:
        # print("Target color is too close to white, cannot extract height.")
        return None
 
    z_min, z_max = heights[0], heights[-1]
    h, w, _ = merged.shape
    heights = np.linspace(z_max, z_min, h)
    
    top_k= 3
    diff = np.abs(merged.astype(np.int32) - target_color.astype(np.int32))
    diff = diff.astype(np.uint8)
    b_sorted_idx = np.argsort(diff[:, 0,0])
    b_candidates = b_sorted_idx[:min(top_k, len(b_sorted_idx))]
    # --- Step 2: G 通道（仅在 B 候选中筛）---
    g_diff = diff[b_candidates, 0,:]
    distances = np.sqrt(np.sum((g_diff - target_color) ** 2, axis=1))
    min_index = np.argmin(distances)
    best_idx = b_candidates[min_index]
    
    if best_idx == 0:
        lower_idx, upper_idx = best_idx, best_idx + 1
    elif best_idx == len(merged) - 1:
        lower_idx, upper_idx = best_idx - 1, best_idx
    else:
        lower_idx, upper_idx = best_idx - 1, best_idx + 1

    c1 = merged[lower_idx, 0, :].astype(np.float32)
    c2 = merged[upper_idx, 0, :].astype(np.float32)
    h1, h2 = heights[lower_idx], heights[upper_idx]

    # 计算颜色距离比例（线性插值权重）
    d1 = np.linalg.norm(target_color - c1)
    d2 = np.linalg.norm(target_color - c2)
    if d1 + d2 == 0:
        ratio = 0.5
    else:
        ratio = d1 / (d1 + d2)

    # 插值高程
    z_interp = h1 * (1 - ratio) + h2 * ratio

    # found_color = merged[best_idx]
    # print(found_color)

    # target_lab = cv2.cvtColor(np.uint8([[target_color]]), cv2.COLOR_BGR2LAB)[0,0]
    # table_lab = cv2.cvtColor(merged, cv2.COLOR_BGR2LAB)
    # 计算每个色带颜色与目标颜色的距离
    # dists = np.linalg.norm(table_lab - target_lab, axis=1)
    # dists = np.sqrt(np.sum((table_lab.reshape(-1, 3) - target_lab.reshape(3)) ** 2, axis=1))
    # dists = np.sqrt(np.sum((merged - target_color) ** 2, axis=1))
    # 找到最接近的索引
    # idx = np.argmin(dists)
    # print("idx:",best_idx)
    # print("color at idx:", merged[best_idx],z_interp," target color:", target_color, " height:", heights[best_idx])

    return z_interp

def detect_lines(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 边缘检测
    canny_threshold1=50
    canny_threshold2=150
    edges = cv2.Canny(gray, canny_threshold1, canny_threshold2, apertureSize=3)
    # cv2.imwrite("contours.png", edges)
    # 霍夫直线检测
    hough_threshold=100
    min_line_length=10
    max_line_gap=10
    lines = cv2.HoughLinesP(edges, 
                           rho=1,              # 距离分辨率
                           theta=np.pi/180,    # 角度分辨率
                           threshold=hough_threshold,
                           minLineLength=min_line_length,
                           maxLineGap=max_line_gap
                        )
    
    # 创建结果图像
    result_img = img.copy()
    
    if lines is not None:
        # print(f"检测到 {len(lines)} 条直线")
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # 绘制直线
            cv2.line(result_img, (x1, y1), (x2, y2), (255, 255, 255), 2)  # 红色直线

    # cv2.imwrite("lines_detected.png", result_img)
    return result_img

def find_nonzero_ranges(arr):
    ranges = []
    in_range = False
    start = 0
    for i, val in enumerate(arr):
        if val != 0 and not in_range:
            in_range = True
            start = i
        elif val == 0 and in_range:
            in_range = False
            end = i - 1
            ranges.append((start, end))
    if in_range:
        ranges.append((start, len(arr) - 1))
    return ranges

def remove_short_lines(img, axis = 0):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)
    
    binary[binary >= 50]=1
    col_sum = np.sum(binary, axis=axis).astype(np.int32)
    max_index = np.argmax(col_sum)
    if axis == 1:
        img[max_index,:]=[255,255,255]
    else:
        img[:,max_index]=[255,255,255]
    return img
def numbers_OCR(img,axis = 1):
    r,c = img.shape[1], img.shape[0]
    print("OCR image size:", r, c)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
    binary = cv2.dilate(binary, np.ones((5,5), np.uint8), iterations=1)
    binary[binary >= 50]=1
    # cv2.imwrite("binary.png", binary*255)
    # print(binary.shape)
    col_sum = np.sum(binary, axis=axis).astype(np.int32)
    col_sum[col_sum < 15] = 0
    ranges = find_nonzero_ranges(col_sum)
    print("Detected ranges:", ranges)
    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.'
    digitals=[]
    positions = []
    for i, (start, end) in enumerate(ranges):
        if end - start < 10:
            continue
        segment = img[:, start:end+1] if axis == 0 else img[start:end+1, :]
        positions.append((end-start)//2 + start)
        segment = remove_short_lines(segment,axis)
        cv2.imwrite(f"{axis}_segment_{i}.png", segment)
        text = pytesseract.image_to_string(segment, config=custom_config)
        text = text.replace("\n", "")
        if len(text) < 2:
            continue
        # print("识别到的数字：", text)
        digitals.append(float(text))
    digitals = sorted(digitals)
    means_pos = []
    for i in range(len(positions)-1):
        # print(f"Detected width at position {positions[i+1]-positions[i]}")
        means_pos.append((positions[i+1]-positions[i]))
    means_pos = np.mean(means_pos)
    if axis == 0:
        print(f"Average detected height: {means_pos}")
        d =  digitals[0] - (digitals[1] - digitals[0])*positions[0] / means_pos 
        digitals.append(d)
        digitals = sorted(digitals)
    print("Detected numbers:", digitals,positions)
    print(f"Average detected width: {means_pos}")
    return digitals,means_pos

def parse():
    parser = argparse.ArgumentParser(description="提取地形图并生成高程数据")

    parser.add_argument("--input", type=str,required=True, help="输入图像路径")
    parser.add_argument("--gridr", type=int, required=True, default=100, help="row切分维度")
    parser.add_argument("--gridc", type=int, required=True, default=100, help="col切分维度")
    args = parser.parse_args()
    
    return args

def main():
    args = parse()
    print("输入文件:", args.input)
    print("输出采样点数量:", args.gridr, args.gridc)
    img = cv2.imread(args.input)
    extern_area,main_area = extract_frames(img)
    cv2.imwrite("main_area.png", main_area)
    cv2.imwrite("extern_area.png", extern_area)
    box_area, box_cord,inner_area,inner_cord = process_border_area(extern_area)
    cv2.imwrite("border.png", box_area)
    cv2.imwrite("inner.png", inner_area)
    box_r,box_c =box_area.shape[1],box_area.shape[0]
    print("Box area size:", box_r, box_c)

    r = extern_area[box_cord[1]:box_cord[1]+box_cord[3],box_cord[0]:inner_cord[0]]
    result_img = detect_lines(r)
    result_img = detect_lines(result_img)
    xs,rmean = numbers_OCR(result_img)
    # step_x = (xs[-1]-xs[0])/(len(xs)-1)
    # xs.append(xs[0]-step_x)
    # xs = sorted(xs)

    cv2.imwrite("r.png", r)

    t = extern_area[box_cord[1]:inner_cord[1],inner_cord[0]:inner_cord[0]+inner_cord[3]-(inner_cord[0]-box_cord[0])]
    t_img = detect_lines(t)
    t_img = detect_lines(t_img)
    ys,tmean = numbers_OCR(t_img, axis=0)
    # step_y = (ys[-1]-ys[0])/(len(ys)-1)
    # ys.append(ys[0]-step_y)
    # ys.append(ys[-2]+step_y)
    # ys = sorted(ys)
    cv2.imwrite("t.png", t)
    main_area_r,main_area_c =main_area.shape[1],main_area.shape[0]
    print("Inner area size:", main_area_r, main_area_c)

    merged,heights = process_color_bar(inner_area)
    print("Detected heights:", heights, xs, ys,tmean,rmean)
    cv2.imwrite("merged.png", merged)

    rmean = rmean * main_area_r / box_r
    tmean = tmean * main_area_c / box_c

    step_r = int(main_area_r / args.gridr)
    step_c = int(main_area_c / args.gridc)

    # step_r = 25
    # step_c = 25

    result = []
    for ri in range(1,args.gridr):
        for ci in range(1,args.gridc):
            r = min(int(ri*step_r),main_area_r)
            c = min(int(ci*step_c),main_area_c)
            # print(f"Grid ({ri}, {ci})  pixel: ({r}, {c}) xs:{xs} ys:{ys} step_r:{step_r} step_c:{step_c}")
            dis_r = xs[-1] - (xs[1] - xs[0]) * r / rmean 
            dis_c = ys[0] + (ys[-1] - ys[-2]) * c / tmean
            # print("Image pixel coordinates:", dis_r, dis_c)
            coord = (r,c)
            height = extrac_from_main(main_area,merged,coord,heights)
            if height is not None:
                # print(f"Extracted height at grid ({ri}, {ci}):", height)
                result.append((dis_r,dis_c,height))
        #     break
        # break
        
    with open("extracted_heights.txt","w") as f:
        for dis_r,dis_c,height in result:
            f.write(f"{dis_r}\t{dis_c}\t{height}\n")
    # img_pixel_y = (xs[-1] - args.y) * rmean/(xs[1] - xs[0])
    # print((xs[-1] - args.y), rmean,(xs[1] - xs[0]))
    # img_pixel_x = (args.x - ys[0]) * tmean/(ys[-1] - ys[-2])
    # print((args.x - ys[0]), tmean,(ys[-1] - ys[-2]))
    # print("Image pixel coordinates:", img_pixel_x, img_pixel_y)
    # coord = (int(img_pixel_y),int(img_pixel_x))
    # height = extrac_from_main(main_area,merged,coord,heights)
    # print("Extracted height:", height)

if __name__ == "__main__":
    main()

    


