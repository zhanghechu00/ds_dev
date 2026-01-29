import base64
import urllib.request
import os

def generate_image():
    input_file = r"d:\code\ds\MYGPTAIv2\platform_architecture.mmd"
    output_file = r"d:\code\ds\MYGPTAIv2\platform_architecture.png"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        mermaid_code = f.read()

    # Use standard base64 encoding
    graphbytes = mermaid_code.encode("utf8")
    base64_bytes = base64.b64encode(graphbytes)
    base64_string = base64_bytes.decode("ascii")
    
    # Generate URL (using mermaid.ink service)
    url = f"https://mermaid.ink/img/{base64_string}"
    
    print(f"Attempting to download from mermaid.ink...")

    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response, open(output_file, 'wb') as out_file:
            out_file.write(response.read())
        print(f"Success! Image saved to: {output_file}")
    except Exception as e:
        print(f"Failed to download image: {e}")
        print("Falling back to HTML generation...")
        generate_html_fallback(mermaid_code)

def generate_html_fallback(mermaid_code):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Architecture Diagram</title>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true }});
        </script>
        <style>
            body {{ font-family: sans-serif; display: flex; flex-direction: column; align-items: center; }}
            h2 {{ color: #333; }}
            .download-hint {{ margin-bottom: 20px; color: #666; }}
            #graphDiv {{ border: 1px solid #ddd; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <h2>Platform Architecture</h2>
        <div class="download-hint">Right-click the diagram below and select "Save Image As..."</div>
        <div class="mermaid" id="graphDiv">
{mermaid_code}
        </div>
    </body>
    </html>
    """
    html_path = r"d:\code\ds\MYGPTAIv2\platform_architecture_export.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Created interactive HTML file: {html_path}")

if __name__ == "__main__":
    generate_image()
