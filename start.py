from flask import Flask, render_template, request, jsonify, send_file, abort
# from backend_haiyou import LLMProcessor, MODEL_NAME
from  backend_shihua import LLMProcessor, MODEL_NAME
import re
from pathlib import Path
app = Flask(__name__)

llm_processor = LLMProcessor()
def normalize_static_md(md: str) -> str:
    """
    将 tool_output 中的绝对地址规范为相对地址：
    - 去掉当前 host 前缀（http(s)://host[:port]）
    - 去掉 localhost/127.0.0.1 前缀
    这样前端渲染的图片/链接在不同环境都可用。
    """
    if not isinstance(md, str):
        return md
    try:
        base = (request.host_url or "").rstrip('/')  # e.g. http://192.168.1.10:5000
        if base:
            md = md.replace(base, '')
    except Exception:
        pass
    md = re.sub(r'https?://(?:localhost|127\.0\.0\.1)(?::\d+)?', '', md)
    return md

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html', model_name=MODEL_NAME)


@app.route('/chat', methods=['POST'])
def chat():
    print(">>> Flask received /chat request")
    data = request.json or {}
    action = data.get('action')
    print(f">>> Action: {action}")

    try:
        if action == 'provide_tool_params':
            tool = data.get('tool')
            params = data.get('params') or {}
            steps = llm_processor.resume_with_tool_params(tool, params)

            reply = steps.get("final_response", "") or ""
            tool_output = steps.get("tool_result") or steps.get("tool_output")
            # if tool_output:
            #     tool_output = normalize_static_md(tool_output)

            return jsonify({
                "reply": reply,
                "tool_output": tool_output,
                "title": (reply or "对话")[:20]
            })
        if action == "new_chat":
            result = llm_processor.new_chat()
            # 只返回欢迎语，前端渲染为第一条助手消息
            return jsonify({
                "reply": result.get("reply", ""),
                "tool_output": None,
                "title": "新建对话"
            })
        user_query = data.get('message')
        if not user_query:
            return jsonify({"error": "No message provided"}), 400
        steps = llm_processor.process_user_query(user_query)  # 这是你自定义的 dict
        if "need_params" in steps:
            return jsonify(steps)

        reply = steps.get("final_response", "")         # 关键：取 final_response
        tool_output = steps.get("tool_result") or steps.get("tool_output")  # 有工具时带回

        return jsonify({
            "reply": reply,
            "tool_output": tool_output,
            "title": (reply or "对话")[:20]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/preview', methods=['GET'])
def preview_file():
    """Serve local project images for in-chat preview.

    Security: only allows files under the MYGPTAIv2 project root and common image extensions.
    Usage: /preview?path=06-contours/c.png
    """
    rel = (request.args.get('path') or '').strip().lstrip('/\\')
    if not rel:
        abort(400, description="missing 'path' query")

    project_root = Path(__file__).resolve().parent
    target = (project_root / rel).resolve()

    # Prevent path traversal: target must be inside project_root
    try:
        target.relative_to(project_root)
    except ValueError:
        abort(403, description="path not allowed")

    if not target.exists() or not target.is_file():
        abort(404, description="file not found")

    if target.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}:
        abort(415, description="unsupported file type")

    return send_file(target)

if __name__ == '__main__':
    print("Flask app running on http://127.0.0.1:5001/")
    app.run(debug=True, port=5001)