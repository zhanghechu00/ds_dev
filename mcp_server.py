import shutil
from mcp.server.fastmcp import FastMCP
import asyncio
import subprocess
import os
from flask import url_for
try:
    from rag import query_graph_rag
except ImportError:
    # If rag module is not found mostly due to missing deps in env
    def query_graph_rag(q): return "RAG module not initialized or dependencies missing."


# Initialize FastMCP server
mcp = FastMCP("faction_mcp_server", log_level="ERROR")

def get_exe_path(exe_name, default_absolute_path=None):
    """
    查找可执行文件路径：
    1. 当前工作目录
    2. 系统 PATH
    3. 指定的默认绝对路径
    """
    # 1. 检查当前目录
    cwd_exe = os.path.join(os.getcwd(), exe_name)
    if os.path.exists(cwd_exe):
        return cwd_exe
    
    # 2. 检查 PATH
    path_exe = shutil.which(exe_name)
    if path_exe:
        return path_exe

    # 3. 检查默认路径
    if default_absolute_path and os.path.exists(default_absolute_path):
        return default_absolute_path
    
    return None

@mcp.tool()
async def run_MIP(query: str) -> str:
    """运行反演仿真模拟程序

    Args:
        query: 工作路径
    """
    err= ""
    if query is None or not os.path.exists(query):
        err+="工作路径{query}不存在，请检查"
        return err
    
    exe_path = get_exe_path("runMIP.exe", r"E:\GeFrac\01_C_Platform\runMIP.exe")
    if not exe_path:
        return "错误：未找到 runMIP.exe 程序，请确认文件在项目根目录或已配置路径。"

    try:
        # Windows下DETACHED_PROCESS让子进程完全独立
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            [exe_path],
            cwd=query,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS
        )
        img_url = url_for('simulation', filename='simulation/result.gif', _external=True)
        return f"反演仿真程序已启动 (PID: {process.pid})。\n\n![反演仿真模拟]({img_url})"

    except RuntimeError:
        img_url = "http://127.0.0.1:5001/static/simulation/result.gif"
        return f"反演仿真程序已启动。\n\n![反演仿真模拟]({img_url})"
    except Exception as e:
        return f"调用 runMIP.exe 时发生异常: {str(e)}"

@mcp.tool()
async def run_Aifrac(query: str) -> str:
    """运行仿真模拟程序

    Args:
        query: 工作路径
    """
    err= ""
    if query is None or not os.path.exists(query):
        err+="工作路径{query}不存在，请检查"
        return err
    
    exe_path = get_exe_path("runGefrac.exe", r"E:\GeFrac\01_C_Platform\runGefrac.exe")
    if not exe_path:
        return "错误：未找到 runGefrac.exe 程序，请确认文件在项目根目录或已配置路径。"

    try:
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            [exe_path],
            cwd=query,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS
        )
        img_url = url_for('simulation', filename='simulation/AiFrac_result.gif', _external=True)
        return f"Aifrac 仿真程序已启动 (PID: {process.pid})。\n\n![仿真模拟四维地应力结果]({img_url})"
    except RuntimeError:
        img_url = "http://127.0.0.1:5001/static/simulation/AiFrac_result.gif"
        return f"Aifrac 仿真程序已启动。\n\n![仿真模拟四维地应力结果]({img_url})"
    except Exception as e:
        return f"调用 runGefrac.exe 时发生异常: {str(e)}"

@mcp.tool()
async def run_Petrel2Aifrac(query: str,file_name:str) -> str:
    """运行Petrel转Aifrac程序，将Petrel数据转换为Aifrac格式，地质模型转地质力学模型
    Args:
        query: 工作路径
        file_name: Petrel文件名
    """
    err= ""
    if query is None or not os.path.exists(query):
        err+="工作路径{query}不存在，请检查"
    if file_name is None or not os.path.exists(os.path.join(query,file_name)):
        err+="文件{file_name}不存在，请检查"
    if err!="":
        return err
    
    exe_path = get_exe_path("GRDECL_Parser.exe", r"E:\GeFrac\01_C_Platform\GRDECL_Parser.exe")
    if not exe_path:
        return "错误：未找到 GRDECL_Parser.exe 程序。"

    try:
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            [exe_path, "-f", file_name, "--removeDuplicateNodes", "--rebuild", "none", "--outputFileType", "inp", "--outputCellType", "tet", "--log", "output.log"],
            cwd=query,
            creationflags=DETACHED_PROCESS
        )
        new_file_name = file_name.replace('.grdecl', '_Tet.inp').replace('.GRDECL', '_Tet.inp')

        return f"Petrel转Aifrac程序已启动 (PID: {process.pid})。转换后的文件预计为 {new_file_name}"
    except Exception as e:
        return f"调用Petrel转Aifrac程序exe时发生异常: {str(e)}"

@mcp.tool()
async def run_Aifrac2Petrel(query: str) -> str:
    """ 运行Aifrac转Petrel程序，将计算结果为Petrel格式

    Args:
        query: 工作路径
    """
    err= ""
    if query is None or not os.path.exists(query):
        err+="工作路径{query}不存在，请检查"
        return err

    exe_path = get_exe_path("Gefrac2Petrel.exe", r"E:\GeFrac\01_C_Platform\Gefrac2Petrel.exe")
    if not exe_path:
        return "错误：未找到 Gefrac2Petrel.exe 程序。"

    try:
        # Windows下DETACHED_PROCESS让子进程完全独立
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            [exe_path,"--removeDuplicateNodes", "--rebuild", "none", "--outputFileType", "inp", "--outputCellType", "tet"],
            cwd=query,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS
        )
        return f"Aifrac转Petrel程序已启动 (PID: {process.pid})。"
    except Exception as e:
        return f"调用Aifrac转Petrel程序exe时发生异常: {str(e)}"

@mcp.tool()
async def run_boundary(query: str,F:str) -> str:
    """ 自动设定边界条件，对转换后的模型施加力边界

    Args:
        query: 工作路径
        F: 上覆压力
    """
    err= ""
    if query is None or not os.path.exists(query):
        err+="工作路径{query}不存在，请检查"
    if F is None :
        err+="请输入上覆压力F"
    if err!="":
        return err
    
    exe_path = get_exe_path("boundary.exe", r"E:\GeFrac\01_C_Platform\boundary.exe")
    if not exe_path:
        return "错误：未找到 boundary.exe 程序。"

    try:
        # Windows下DETACHED_PROCESS让子进程完全独立
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            [exe_path,"-f", F], # 注意：原代码 "工作路径#!"+F 看起来像是特定格式，这里假设 exe 接受 -f 参数
            cwd=query,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS
        )
        return f"自动设定边界条件程序已启动 (PID: {process.pid})，输出文件为 InputModel.inp"
    except Exception as e:
        return f"调用自动设定边界条件exe时发生异常: {str(e)}"

# @mcp.tool()
# async def send_image(url: str = "", alt: str = "结果图片") -> str:
#     """
#     返回一张结果图片的 Markdown 链接。前端会自动渲染并支持点击放大。
#     参数:
#       url: 图片 URL（可选；不传则返回一张随机图）
#       alt: 图片的描述（alt 文本）
#     用法:
#       - 直接把返回的 Markdown 作为助手回复的一部分即可显示图片。
#     """
#     # 默认给一张随机图片（可换成你自己的可访问 URL）
#         # 注意：_external=True 需要在有 Flask 应用上下文时调用
#     try:
#         img_url = url_for('static', filename='images/image2.gif', _external=True)
#     except RuntimeError:
#         # 如果此时不在 Flask app context，可以手动拼 URL（假设运行在 http://localhost:5000）
#         img_url = "http://127.0.0.1:5000/static/images/image2.gif"
#     return f"![{alt}]({img_url})"

# @mcp.tool()
# async def run_crashsimulation(query: str,file_name:str) -> str:
#     """运行碰撞模拟程序，输出计算结果动图

#     Args:
#         query: 工作路径
#         file_name: 模型文件名
#     """
#         # 注意：_external=True 需要在有 Flask 应用上下文时调用
#     alt = "碰撞模拟结果"
#     try:
#         #先根据工作路径，将static/images/image2.gif复制过去，改名为crashsimulation.gif
#        # 先根据工作路径，将static/images/image2.gif复制过去，改名为crashsimulation.gif
#         if query is None or not os.path.exists(query):
#             return "工作路径不存在，请检查"
#         source_path = os.path.join("static", "images", "image2.gif")
#         destination_path = os.path.join(query, "crashsimulation.gif")
#         if not os.path.exists(destination_path):
#             os.makedirs(query, exist_ok=True)
#             shutil.copyfile(source_path, destination_path)  # 用copyfile替换rename


#         # 然后返回工作路径query下的图片链接


#         # rel_path = os.path.relpath(destination_path, os.path.join(os.getcwd(), "static"))
#         # img_url = f"http://127.0.0.1:5000/simulation/crashsimulation.gif"
#         # img_url = url_for('static', filename=f'images/{rel_path}', _external=True)

#         img_url = url_for('simulation', filename='simulation/crashsimulation.gif', _external=True)

#         return f"![{alt}]({img_url})"

#     except RuntimeError:
#         # 如果此时不在 Flask app context，可以手动拼 URL（假设运行在 http://localhost:5000）
#         img_url = "http://127.0.0.1:5000/static/simulation/crashsimulation.gif"
#     return f"![{alt}]({img_url})"
@mcp.tool()
async def run_map2petrel(
    query: str, 
    file_name: str,
    well_file: str = "welllog.txt",
    rnx: int = 110,
    rny: int = 110,
    rnz: int = 100,
    xmin: float = 19178749,
    xmax: float = 19186699,
    ymin: float = 3366759,
    ymax: float = 3374709,
    zmin: float = 400,
    zmax: float = 2400
) -> str:
    """
    从高程数据建立Petrel地质模型。
    参数:
        query: 工作路径
        file_name: 高程数据文件名
        well_file: 井轨迹文件名
        rnx, rny, rnz: 网格数量
        xmin, xmax, ymin, ymax, zmin, zmax: 坐标范围
    """
    err= ""
    if query is None or not os.path.exists(query):
        err+="工作路径{query}不存在，请检查"
    if file_name is None or not os.path.exists(os.path.join(query,file_name)):
        err+="文件{file_name}不存在，请检查"
    if err!="":
        return err

    exe_path = get_exe_path("ExportPetroFileV32.exe", r"D:\Desktop\test\VScodeCPP\ExportPetroFile\ExportPetroFileV32.exe")
    if not exe_path:
        return "错误：未找到 ExportPetroFileV32.exe 程序。"

    # 构建命令行参数
    cmd = [
        exe_path,
        "-o", "model.GRDECL",
        "--mapfile", file_name,
        "--well", well_file,
        "--rnx", str(rnx),
        "--rny", str(rny),
        "--rnz", str(rnz),
        "--xmin", str(xmin),
        "--xmax", str(xmax),
        "--ymin", str(ymin),
        "--ymax", str(ymax),
        "--zmin", str(zmin),
        "--zmax", str(zmax)
    ]

    try:
        # Windows下DETACHED_PROCESS让子进程完全独立
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            cmd,
            cwd=query,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS
        )
        img_url = url_for('static', filename='simulation/model0.png', _external=True)
    except RuntimeError:
        # 如果此时不在 Flask app context，可以手动拼 URL（假设运行在 http://localhost:5000）
        img_url = "http://127.0.0.1:5001/static/simulation/model0.png"
    
    return f"建模程序已启动 (PID: {process.pid})。\n使用的参数：\n- 网格: {rnx}x{rny}x{rnz}\n- X范围: {xmin}~{xmax}\n- Y范围: {ymin}~{ymax}\n- Z范围: {zmin}~{zmax}\n\n![建模结果为model.GRDECL]，可以在工作目录查看具体文件，示意图为({img_url})"
@mcp.tool()
async def run_wellcalc(query: str,file_name:str) -> str:
    """
    运行测井地应力约束程序，输出计算结果
    参数:
        query: 工作路径
        file_name: 测井数据文件名

    """
    err= ""
    if query is None or not os.path.exists(query):
        err+="工作路径{query}不存在，请检查"
    if file_name is None or not os.path.exists(os.path.join(query,file_name)):
        err+="文件{file_name}不存在，请检查"
    if err!="":
        return err
    
    exe_path = get_exe_path("welllog.exe")
    if not exe_path:
        return "错误：未找到 welllog.exe 程序。"

    try:
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            [exe_path, file_name], # 假设 welllog.exe 接受文件名作为参数
            cwd=query,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS
        )
        img_url = url_for('static', filename='simulation/welllogresult.png', _external=True)
    except RuntimeError:
        # 如果此时不在 Flask app context，可以手动拼 URL（假设运行在 http://localhost:5000）
        img_url = "http://127.0.0.1:5001/static/simulation/welllogresult.png"
    except Exception as e:
        return f"调用 welllog.exe 时发生异常: {str(e)}"

    return f"测井地应力计算程序已启动 (PID: {process.pid})。\n\n![测井地应力结果]({img_url})"
@mcp.tool()
async def search_result(alt: str) -> str:
    """
    查看其他数据结果（井周压裂模拟结果、四维压裂结果、地应力数据统计结果），输出计算结果
    参数:
        alt: 结果描述
    """
    err= ""
    img_url= ""
    if alt is None or alt.strip() == "":
        err += "请输入结果描述"
        return err
    if alt == "井周压裂模拟结果":
        img_url = "http://localhost:5000/static/simulation/压裂1.gif"+"   http://localhost:5000/static/simulation/压裂2.gif"
    elif alt == "四维压裂模拟结果":
        img_url = "http://localhost:5000/static/simulation/四维压裂.gif"
    elif alt == "地应力数据统计结果":
        img_url = "http://localhost:5000/static/simulation/地应力数据统计.png"
    return f"![alt]({img_url})"

@mcp.tool()
async def ask_knowledge_graph(query: str) -> str:
    """基于项目内部文档和知识库回答问题 (RAG)

    Args:
        query: 你的问题
    """
    return await asyncio.to_thread(query_graph_rag, query)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')