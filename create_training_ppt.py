from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    
    # Define Color Scheme
    # Deep Blue for headers/backgrounds
    COLOR_PRIMARY = RGBColor(0, 51, 102)  # #003366
    # Lighter Blue for accents
    COLOR_ACCENT = RGBColor(51, 102, 153) # #336699
    # White for text on dark backgrounds
    COLOR_WHITE = RGBColor(255, 255, 255)
    # Dark Gray for body text
    COLOR_TEXT = RGBColor(64, 64, 64)     # #404040

    def set_font(paragraph, font_size, bold=False, color=COLOR_TEXT):
        for run in paragraph.runs:
            run.font.size = font_size
            run.font.bold = bold
            run.font.color.rgb = color
            run.font.name = 'Microsoft YaHei' # Use a font that supports Chinese well

    # --- Slide 1: Title Slide ---
    slide_layout = prs.slide_layouts[6] # Blank layout for custom design
    slide = prs.slides.add_slide(slide_layout)
    
    # Background Color
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = COLOR_PRIMARY

    # Title
    title_shape = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(8), Inches(1.5))
    title_tf = title_shape.text_frame
    title_tf.word_wrap = True
    p = title_tf.add_paragraph()
    p.text = "Agent 功能扩展开发培训"
    p.alignment = PP_ALIGN.CENTER
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = COLOR_WHITE
    p.font.name = 'Microsoft YaHei'

    # Subtitle
    subtitle_shape = slide.shapes.add_textbox(Inches(1), Inches(4), Inches(8), Inches(1.5))
    subtitle_tf = subtitle_shape.text_frame
    subtitle_tf.word_wrap = True
    p = subtitle_tf.add_paragraph()
    p.text = "面向硕士研究生的开发指南\n如何为 Agent 添加新工具"
    p.alignment = PP_ALIGN.CENTER
    p.font.size = Pt(24)
    p.font.color.rgb = RGBColor(200, 200, 200)
    p.font.name = 'Microsoft YaHei'

    # Footer/Decoration
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(7), Inches(10), Inches(0.5))
    shape.fill.solid()
    shape.fill.fore_color.rgb = COLOR_ACCENT
    shape.line.fill.background()

    # --- Helper for Content Slides ---
    def add_content_slide(title_text, content_items):
        slide_layout = prs.slide_layouts[6] # Blank layout
        slide = prs.slides.add_slide(slide_layout)

        # Header Bar
        header = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(1.2))
        header.fill.solid()
        header.fill.fore_color.rgb = COLOR_PRIMARY
        header.line.fill.background()

        # Title
        title_shape = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.8))
        p = title_shape.text_frame.add_paragraph()
        p.text = title_text
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.font.name = 'Microsoft YaHei'

        # Content Box
        content_shape = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(9), Inches(5.5))
        tf = content_shape.text_frame
        tf.word_wrap = True

        for item in content_items:
            p = tf.add_paragraph()
            p.text = item
            p.font.size = Pt(20)
            p.font.color.rgb = COLOR_TEXT
            p.font.name = 'Microsoft YaHei'
            p.space_after = Pt(14)
            
            # Simple indentation for "sub-points" (starting with - or number)
            if item.strip().startswith("-") or (len(item)>2 and item[1]=='.'):
                 p.level = 1
            else:
                 p.level = 0

    # Slide 2: 架构概览
    add_content_slide("系统架构概览", [
        "Agent 的核心由三部分组成：",
        "1. Frontend (前端)",
        "   - 用户交互界面，负责展示和收集输入。",
        "2. Backend (后端 - backend_shihua.py)",
        "   - 处理业务逻辑，与大模型 (LLM) 交互。",
        "   - 管理工具注册与分发。",
        "3. MCP Server (工具服务 - mcp_server_shihua.py)",
        "   - 实际执行具体任务的地方。",
        "   - 负责文件操作、仿真计算、外部程序调用等。"
    ])

    # Slide 3: 开发流程三部曲
    add_content_slide("开发流程三部曲", [
        "要为一个 Agent 添加新功能，通常需要完成以下三个步骤：",
        "",
        "Step 1: 在 MCP Server 中实现具体功能函数",
        "   - 编写 Python 代码，实现业务逻辑。",
        "",
        "Step 2: 在 Backend 中注册该工具",
        "   - 让 LLM 知道这个工具的存在及其用途。",
        "",
        "Step 3: 在 Backend 中配置参数校验",
        "   - 确保用户输入完整，提升用户体验。"
    ])

    # Slide 4: Step 1 - 实现功能
    add_content_slide("Step 1: 实现功能 (mcp_server_shihua.py)", [
        "位置: mcp_server_shihua.py",
        "操作: 使用 @mcp.tool() 装饰器定义异步函数。",
        "关键点:",
        "- 函数名应清晰易懂 (如 extract_heights_from_image)。",
        "- 必须包含类型提示 (Type Hints)。",
        "- Docstring (文档字符串) 至关重要！",
        "  - 它是 LLM 理解工具用途的唯一途径。",
        "示例代码:",
        "  @mcp.tool()",
        "  async def my_tool(path: str) -> str:",
        "      '''这是工具的描述'''",
        "      ..."
    ])

    # Slide 5: Step 2 - 注册工具
    add_content_slide("Step 2: 注册工具 (backend_shihua.py)", [
        "位置: backend_shihua.py 中的 TOOLS 列表",
        "操作: 添加一个新的 JSON 对象描述工具。",
        "结构:",
        "- name: 必须与 MCP Server 中的函数名一致。",
        "- description: 详细描述工具功能和参数要求。",
        "- parameters: 定义参数的类型、描述和是否必填。",
        "注意: 这里的 description 会直接作为 Prompt 发送给 LLM。"
    ])

    # Slide 6: Step 3 - 参数校验
    add_content_slide("Step 3: 参数校验 (backend_shihua.py)", [
        "位置: backend_shihua.py 中的 REQUIRED_FIELDS 字典",
        "操作: 添加工具名和必填参数列表。",
        "作用:",
        "- 当 LLM 调用工具但参数缺失时，后端会拦截请求。",
        "- 自动触发前端弹出表单，提示用户补充参数。",
        "示例:",
        "  REQUIRED_FIELDS = {",
        "      'my_tool': ['path', 'param2']",
        "  }"
    ])

    # Slide 7: 实战案例 - 提取高程
    add_content_slide("实战案例: 提取高程数据", [
        "1. mcp_server",
        "   - 定义 extract_heights_from_image 函数，调用 opencv 脚本。",
        "2. backend (TOOLS)",
        "   - 添加工具定义，描述 image_path, grid_r, grid_c 参数。",
        "3. backend (REQUIRED)",
        "   - 添加 'extract_heights_from_image': ['image_path']。",
        "结果:",
        "   用户输入 '帮我提取这张图的高程' -> Agent 发现缺路径 -> 弹窗让用户填路径 -> 执行提取。"
    ])

    # Slide 8: 调试与最佳实践
    add_content_slide("调试与最佳实践", [
        "1. 日志",
        "   - 关注 model.log，查看 LLM 的思考过程和工具调用参数。",
        "2. 错误处理",
        "   - 在 MCP 工具中捕获异常，返回清晰的错误信息字符串。",
        "3. Mock 模式",
        "   - 如果依赖外部 EXE，建议先写 Mock (模拟) 返回。",
        "   - 确保流程通畅后再对接真实程序。",
        "4. 路径处理",
        "   - 始终检查文件路径是否存在，使用绝对路径。"
    ])

    prs.save('Agent_Training_Beautified.pptx')
    print("PPT generated successfully: Agent_Training_Beautified.pptx")

if __name__ == "__main__":
    create_presentation()
