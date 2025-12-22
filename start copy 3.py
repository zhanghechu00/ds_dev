from flask import Flask, render_template, request, jsonify
from flask import Response
import time, os, urllib.parse
from backend import LLMProcessor, MODEL_NAME
import re
import json
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
    data = request.json or {}
    action = data.get('action')

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

        user_query = data.get('message')
        if not user_query:
            return jsonify({"error": "No message provided"}), 400
        steps = llm_processor.process_user_query(user_query)  # 这是你自定义的 dict
        if "need_params" in steps:
            return jsonify(steps)

        reply = steps.get("final_response", "")         # 关键：取 final_response
        tool_output = steps.get("tool_result") or steps.get("tool_output")  # 有工具时带回
        live_log = None
        try:
            if isinstance(tool_output, str):
                obj = json.loads(tool_output)
                if isinstance(obj, dict) and obj.get("log_path"):
                    # 前端用这个地址拼出 SSE
                    live_log = {"path": obj["log_path"]}
                    # 把对话里的可读提示文字改成 obj["message"]
                    if obj.get("message"):
                        reply = (obj["message"] + "\n\n> 日志已开始流式输出…") or reply
        except Exception:
            pass
        return jsonify({
            "reply": reply,
            "tool_output": tool_output,
            "live_log": live_log,   # ★ 新增
            "title": (reply or "对话")[:20]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/logs/stream')
def stream_log():
    """
    SSE：持续把日志文件的新增内容推送给前端。
    用法：/logs/stream?path=<urlencoded absolute path>
    """
    raw_path = request.args.get('path', '')
    if not raw_path:
        return Response("Missing path", status=400)

    # 简单防护：只允许访问你关心的目录（按需替换根目录）
    # 例如允许 D:\projects、E:\GeFrac 之类；不做复杂校验以保持演示简单
    path = urllib.parse.unquote(raw_path)
    if not os.path.exists(path):
        return Response("Not Found", status=404)

    def generate():
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                # 从文件末尾开始追踪
                f.seek(0, os.SEEK_END)
                while True:
                    line = f.readline()
                    if line:
                        yield f"data: {line.rstrip()}\n\n"
                    else:
                        time.sleep(0.3)
        except Exception as e:
            yield f"data: [stream stopped: {e}]\n\n"

    return Response(generate(), mimetype='text/event-stream')
if __name__ == '__main__':
    print("Flask app running on http://127.0.0.1:5000/")
    app.run(debug=True)