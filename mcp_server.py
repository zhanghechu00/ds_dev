import shutil
from mcp.server.fastmcp import FastMCP
import asyncio
import subprocess
import os
from flask import url_for
# Initialize FastMCP server
# mcp = FastMCP("search_mcp_server", log_level="ERROR")
mcp = FastMCP("faction_mcp_server", log_level="ERROR")


# Constants
# @mcp.tool()
# async def search(query: str) -> str:
#     """搜索网络

#     Args:
#         query: 搜索内容
#     """
#     # 正常情况下，这里应该调用相关 API 做搜索，为了减少代码的复杂度，
#     # 这里我们返回一段假的工具执行结果，用以测试
#     return "来自 MCP Server 的答案：纽约市今天的天气是晴天，明天的天气是多云。"
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
    # exe_path = r"E:\GeFrac\01_C_Platform\runMIP.exe"
    try:
        # # Windows下DETACHED_PROCESS让子进程完全独立
        # DETACHED_PROCESS = 0x00000008
        # process = subprocess.Popen(
        #     [exe_path],
        #     cwd=query,
        #     stdout=subprocess.DEVNULL,
        #     stderr=subprocess.DEVNULL,
        #     creationflags=DETACHED_PROCESS
        # )
        img_url = url_for('simulation', filename='simulation/result.gif', _external=True)
        return f"![反演仿真模拟]({img_url})"

    except RuntimeError:
        # 如果此时不在 Flask app context，可以手动拼 URL（假设运行在 http://localhost:5000）
        img_url = "http://127.0.0.1:5000/static/simulation/result.gif"
    #     return f"MIP程序已启动，PID: {process.pid}"
    # except Exception as e:
    #     return f"调用exe时发生异常: {str(e)}"
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
    # exe_path = r"E:\GeFrac\01_C_Platform\runGefrac.exe"
    try:
        # DETACHED_PROCESS = 0x00000008
        # process = subprocess.Popen(
        #     [exe_path],
        #     cwd=query,
        #     stdout=subprocess.DEVNULL,
        #     stderr=subprocess.DEVNULL,
        #     creationflags=DETACHED_PROCESS
        # )
        img_url = url_for('simulation', filename='simulation/AiFrac_result.gif', _external=True)
    except RuntimeError:
        # 如果此时不在 Flask app context，可以手动拼 URL（假设运行在 http://localhost:5000）
        img_url = "http://127.0.0.1:5000/static/simulation/AiFrac_result.gif"
        return f"![仿真模拟四维地应力结果]({img_url})"

    #     return f"正演程序已启动，服务端进程PID: {process.pid}，请返回任务列表查看运行情况"
    # except Exception as e:
    #     return f"调用正演exe时发生异常: {str(e)}"
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
    exe_path = r"E:\GeFrac\01_C_Platform\GRDECL_Parser.exe"
    try:
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            [exe_path, "-f", file_name, "--removeDuplicateNodes", "--rebuild", "none", "--outputFileType", "inp", "--outputCellType", "tet", "--log", "output.log"],  # 还需要进一步增加参数
            cwd=query,
            creationflags=DETACHED_PROCESS
        )
        new_file_name = file_name.replace('.grdecl', '_Tet.inp')
        new_file_name = file_name.replace('.GRDECL', '_Tet.inp')

        return f"Petrel转Aifrac程序程序已启动，服务端进程PID: {process.pid}，请返回任务列表查看运行情况。转换后的文件为 {new_file_name}"
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
    # if file_name is None or not os.path.exists(os.path.join(query,file_name)):
    #     err+="文件{file_name}不存在，请检查"
    # if err!="":
        return err

    exe_path = r"E:\GeFrac\01_C_Platform\Gefrac2Petrel.exe"
    try:
        # Windows下DETACHED_PROCESS让子进程完全独立
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            [exe_path,"--removeDuplicateNodes --rebuild none --outputFileType inp --outputCellType tet "],
            cwd=query,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS
        )
        return f"Aifrac转Petrel程序程序已启动，服务端进程PID: {process.pid}，请返回任务列表查看运行情况"
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
    exe_path = r"E:\GeFrac\01_C_Platform\boundary.exe"
    try:
        # Windows下DETACHED_PROCESS让子进程完全独立
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            [exe_path,"-f","工作路径#!"+F],
            cwd=query,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS
        )
        return f"自动设定边界条件程序已启动，服务端进程PID: {process.pid}，请返回任务列表查看运行情况，输出文件为 InputModel.inp"
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
async def run_map2petrel(query: str,file_name:str) -> str:
    """
    从高程数据建立Petrel地质模型  。
    参数:
        query: 工作路径
        file_name: 高程数据文件名

    """
    # 默认给一张随机图片（可换成你自己的可访问 URL）
        # 注意：_external=True 需要在有 Flask 应用上下文时调用
    err= ""
    if query is None or not os.path.exists(query):
        err+="工作路径{query}不存在，请检查"
    if file_name is None or not os.path.exists(os.path.join(query,file_name)):
        err+="文件{file_name}不存在，请检查"
    if err!="":
        return err

    exe_path = r"D:\Desktop\test\VScodeCPP\ExportPetroFile\ExportPetroFileV32.exe"
    try:
        # Windows下DETACHED_PROCESS让子进程完全独立
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            [exe_path,"-o","model.GRDECL","--mapfile",file_name,"--well","welllog.txt","--rnx","110","--rny", "110", "--rnz", "100", "--xmin" ,"19178749", "--xmax" ,"19186699" ,"--ymin" ,"3366759", "--ymax" ,"3374709" ,"--zmin" ,"400" ,"--zmax" ,"2400"],
            cwd=query,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS
        )
        img_url = url_for('static', filename='simulation/model0.png', _external=True)
    except RuntimeError:
        # 如果此时不在 Flask app context，可以手动拼 URL（假设运行在 http://localhost:5000）
        img_url = "http://localhost:5000/static/simulation/model0.png"
    return f"![建模结果为model.GRDECL]，可以在工作目录查看具体文件，示意图为({img_url})"
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
    try:
        img_url = url_for('static', filename='simulation/welllogresult.png', _external=True)
    except RuntimeError:
        # 如果此时不在 Flask app context，可以手动拼 URL（假设运行在 http://localhost:5000）
        img_url = "http://localhost:5000/static/simulation/welllogresult.png"
    return f"![测井地应力结果]({img_url})"
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

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')