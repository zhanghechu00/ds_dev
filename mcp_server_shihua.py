import shutil
from mcp.server.fastmcp import FastMCP
import asyncio
import subprocess
import os
from flask import url_for
try:
    from docx import Document
except ImportError:
    Document = None
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
    exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "runMIP.exe"))
    
    # Mock: 如果exe不存在，直接返回演示结果
    if not os.path.exists(exe_path):
        try:
            img_url = url_for('static', filename='simulation/result.gif', _external=True)
        except RuntimeError:
            img_url = "http://127.0.0.1:5000/static/simulation/result.gif"
        return f"反演仿真程序已启动 (Mock模式)。\n\n![反演仿真模拟]({img_url})"

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
        # 如果此时不在 Flask app context，可以手动拼 URL（假设运行在 http://localhost:5000）
        img_url = "http://127.0.0.1:5000/static/simulation/result.gif"
        return f"![反演仿真模拟]({img_url})"
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
    exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "runGefrac.exe"))
    
    # Mock: 如果exe不存在，直接返回演示结果
    if not os.path.exists(exe_path):
        try:
            img_url = url_for('static', filename='simulation/AiFrac_result.gif', _external=True)
        except RuntimeError:
            img_url = "http://127.0.0.1:5000/static/simulation/AiFrac_result.gif"
        return f"Aifrac 仿真程序已启动 (Mock模式)。\n\n![仿真模拟四维地应力结果]({img_url})"

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
        # 如果此时不在 Flask app context，可以手动拼 URL（假设运行在 http://localhost:5000）
        img_url = "http://127.0.0.1:5000/static/simulation/AiFrac_result.gif"
        return f"![仿真模拟四维地应力结果]({img_url})"

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
    exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "GRDECL_Parser.exe"))
    try:
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            [exe_path, "-f", file_name, "--removeDuplicateNodes", "--rebuild", "none", "--outputFileType", "inp", "--outputCellType", "tet", "--log", "output.log"],  # 还需要进一步增加参数
            cwd=query,
            creationflags=DETACHED_PROCESS
        )
        new_file_name = file_name.replace('.grdecl', '_Tet.inp')
        new_file_name = file_name.replace('.GRDECL', '_Tet.inp')

        # Mock: 如果文件未生成，手动创建一个空文件以通过流程
        output_file_path = os.path.join(query, new_file_name)
        if not os.path.exists(output_file_path):
            with open(output_file_path, 'w') as f:
                f.write("Mock file created by MCP server because exe failed to run.")

        return f"Petrel转Aifrac程序程序已启动，服务端进程PID: {process.pid}，请返回任务列表查看运行情况。转换后的文件为 {new_file_name}"
    except Exception as e:
        return f"调用Petrel转Aifrac程序exe时发生异常: {str(e)}"
@mcp.tool()
async def run_Aifrac2Petrel(query: str) -> str:
    """ 运行Aifrac转Petrel程序，将计算结果为Petrel格式

    Args:
        query: 工作路径
    """
    
    # Mock: 如果exe不存在，直接返回演示结果
    if not os.path.exists(exe_path):
        return f"Aifrac转Petrel程序程序已启动 (Mock模式)，请返回任务列表查看运行情况"

    err= ""
    if query is None or not os.path.exists(query):
        err+="工作路径{query}不存在，请检查"
    # if file_name is None or not os.path.exists(os.path.join(query,file_name)):
    #     err+="文件{file_name}不存在，请检查"
    # if err!="":
        return err

    exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "Gefrac2Petrel.exe"))
    try:
        # Windows下DETACHED_PROCESS让子进程完全独立
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            [exe_path, "--removeDuplicateNodes", "--rebuild", "none", "--outputFileType", "inp", "--outputCellType", "tet"],
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
    exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "boundary.exe"))
    try:
        # Windows下DETACHED_PROCESS让子进程完全独立
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            # [exe_path,"-f","工作路径#!"+F],
            [exe_path,"-f",F], #
            cwd=query,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS
        )
        
        # Mock: 如果文件未生成，手动创建一个空文件以通过流程
        output_file_path = os.path.join(query, "InputModel.inp")
        if not os.path.exists(output_file_path):
            with open(output_file_path, 'w') as f:
                f.write("Mock file created by MCP server because exe failed to run.")

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

    exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "ExportPetroFileV32.exe"))
    try:
        # Windows下DETACHED_PROCESS让子进程完全独立
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            [exe_path,"-o","model.GRDECL","--mapfile",file_name,"--well","welllog.txt","--rnx","110","--rny", "110", "--rnz", "100", "--xmin" ,"19178749", "--xmax" ,"19186699" ,"--ymin" ,"3366759", "--ymax" ,"3374709" ,"--zmin" ,"400" ,"--zmax" ,"2400", "--wvtk", "1"],
            # [exe_path,"-o","model.GRDECL","--mapfile",file_name,"--well","welllog.txt","--rnx","110","--rny", "110", "--rnz", "100", "--xmin" ,"19178749", "--xmax" ,"19186699" ,"--ymin" ,"3366759", "--ymax" ,"3374709" ,"--zmin" ,"400" ,"--zmax" ,"2400"],
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
    exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "welllog.exe"))

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
@mcp.tool()
async def copy_files(source_folder: str, destination_folder: str) -> str:
    """将源文件夹下的所有文件复制到目标文件夹

    Args:
        source_folder: 源文件夹路径
        destination_folder: 目标文件夹路径
    """
    if not os.path.exists(source_folder):
        return f"源文件夹不存在: {source_folder}"
    
    if not os.path.exists(destination_folder):
        try:
            os.makedirs(destination_folder)
        except Exception as e:
            return f"无法创建目标文件夹: {str(e)}"

    copied_count = 0
    errors = []

    try:
        for item in os.listdir(source_folder):
            s = os.path.join(source_folder, item)
            d = os.path.join(destination_folder, item)
            if os.path.isfile(s):
                try:
                    shutil.copy2(s, d)
                    copied_count += 1
                except Exception as e:
                    errors.append(f"复制 {item} 失败: {str(e)}")
    except Exception as e:
        return f"遍历源文件夹时出错: {str(e)}"
    
    result_msg = f"成功复制了 {copied_count} 个文件到 {destination_folder}。"
    if errors:
        result_msg += "\n错误:\n" + "\n".join(errors)
    
    return result_msg

@mcp.tool()
async def verify_word_consistency(file_path: str, keyword: str) -> str:
    """
    检查Word文档中，指定关键字在正文和表格中的对应值是否一致。
    
    Args:
        file_path: Word文档路径
        keyword: 要查找的关键字
    """
    if Document is None:
        return "运行此工具需要安装 python-docx 库。请在终端运行: pip install python-docx"
    
    if not os.path.exists(file_path):
        return f"文件不存在: {file_path}"
    
    try:
        doc = Document(file_path)
    except Exception as e:
        return f"无法打开Word文档: {str(e)}"
    
    text_values = []
    table_values = []
    
    # 1. Search in Paragraphs (Text)
    for para in doc.paragraphs:
        if keyword in para.text:
            # Simple extraction: take everything after the keyword
            parts = para.text.split(keyword, 1)
            if len(parts) > 1:
                # 增强清洗逻辑：去除常见的连接词（如"为"、"is"）、冒号、句号等
                val = parts[1].strip().lstrip(":：为is").strip("。.").strip()
                if val:
                    text_values.append(val)

    # 2. Search in Tables
    for table in doc.tables:
        for row in table.rows:
            cells = row.cells
            for i, cell in enumerate(cells):
                if keyword in cell.text:
                    # Check if there is a next cell
                    if i + 1 < len(cells):
                        val = cells[i+1].text.strip()
                        if val:
                            table_values.append(val)
    
    if not text_values:
        return f"在正文中未找到关键字 '{keyword}' 的相关值。"
    if not table_values:
        return f"在表格中未找到关键字 '{keyword}' 的相关值。"
        
    text_val_str = "; ".join(text_values)
    table_val_str = "; ".join(table_values)
    
    # Check if any text value matches any table value
    # 增强比较逻辑：如果表格中的值包含在正文提取的值中（反之亦然），也视为一致
    match_count = 0
    for tv in text_values:
        for tab_v in table_values:
            if tv == tab_v or tab_v in tv or tv in tab_v:
                match_count += 1
                break
    
    # 检查正文内部是否存在冲突（即正文提取出了多个不同的值）
    # 过滤逻辑：如果提取的值中既有含数字的（如"15.5%"），也有不含数字的（如"测试"），
    # 则优先信任含数字的值作为“真实数据”，忽略非数字的噪声。
    has_digits = [v for v in text_values if any(char.isdigit() for char in v)]
    no_digits = [v for v in text_values if not any(char.isdigit() for char in v)]
    
    final_text_values = text_values
    if has_digits and no_digits:
        final_text_values = has_digits
        # 更新用于显示的字符串，只显示过滤后的有效值
        text_val_str = "; ".join(final_text_values)

    unique_text_values = set(final_text_values)
    has_internal_conflict = len(unique_text_values) > 1

    if match_count > 0:
        if has_internal_conflict:
             return f"部分一致（警告：正文存在多值冲突）。正文值: [{text_val_str}]，表格值: [{table_val_str}]。虽然找到了匹配项，但正文中存在多个不同的数值，请人工核实。"
        else:
             return f"内容一致。正文值: [{text_val_str}]，表格值: [{table_val_str}]"
    else:
        return f"内容不一致！正文值: [{text_val_str}]，表格值: [{table_val_str}]"

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')