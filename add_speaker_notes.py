from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from pptx import Presentation


def _clean_text(s: str) -> str:
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _iter_shape_text(slide) -> Iterable[str]:
    for shape in slide.shapes:
        if not getattr(shape, "has_text_frame", False):
            continue
        text = _clean_text(shape.text or "")
        if text:
            yield text


def _extract_tables(slide) -> List[List[List[str]]]:
    tables: List[List[List[str]]] = []
    for shape in slide.shapes:
        if not getattr(shape, "has_table", False):
            continue
        table = shape.table
        grid: List[List[str]] = []
        for r in range(len(table.rows)):
            row: List[str] = []
            for c in range(len(table.columns)):
                cell_text = _clean_text(table.cell(r, c).text or "")
                row.append(cell_text)
            grid.append(row)
        tables.append(grid)
    return tables


def _guess_title(text_blocks: List[str]) -> Optional[str]:
    if not text_blocks:
        return None
    # Heuristic: first text block is usually title; if it contains many lines, take first line.
    first = text_blocks[0]
    first_line = first.split("\n", 1)[0]
    first_line = _clean_text(first_line)
    if 0 < len(first_line) <= 80:
        return first_line
    # Fallback: choose shortest non-empty block as title candidate
    candidates = sorted((t for t in text_blocks if t), key=lambda x: len(x))
    return candidates[0] if candidates else None


def _split_bullets(text: str) -> List[str]:
    # Keep original line breaks as bullet hints
    lines = [
        _clean_text(x)
        for x in re.split(r"\r?\n", text)
        if _clean_text(x)
    ]
    # If the shape contains a paragraph-like block, treat each line as one point
    if len(lines) > 1:
        return lines
    # Otherwise split on typical separators
    parts = [p.strip() for p in re.split(r"[•\u2022\u25cf\-–—;；。]", text) if p.strip()]
    return parts if len(parts) > 1 else lines


def _summarize_slide(text_blocks: List[str], tables: List[List[List[str]]]) -> Tuple[Optional[str], List[str]]:
    title = _guess_title(text_blocks)

    bullets: List[str] = []
    for block in text_blocks[1:] if title else text_blocks:
        for b in _split_bullets(block):
            b = _clean_text(b)
            if not b:
                continue
            # Avoid re-adding title-like lines
            if title and b == title:
                continue
            bullets.append(b)

    # De-dup while preserving order
    seen = set()
    deduped: List[str] = []
    for b in bullets:
        key = b.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(b)

    # Limit bullets so notes stay readable
    if len(deduped) > 12:
        deduped = deduped[:12] + ["（本页要点较多，讲解时按模块展开）"]

    # If slide is mostly a table, add a hint
    if tables and len(deduped) < 3:
        deduped.append("本页包含对比表：先说结论，再逐列解释差异。")

    return title, deduped


def _notes_template(slide_index_1based: int, title: Optional[str], bullets: List[str], tables: List[List[List[str]]]) -> str:
    title_part = title or f"第 {slide_index_1based} 页"

    lines: List[str] = []
    lines.append(f"【讲者备注｜{title_part}】")

    if bullets:
        lines.append("讲解目标：")
        # Make the goal a short rephrase using first 1-2 bullets
        goal = "；".join(bullets[:2]) if len(bullets) >= 2 else bullets[0]
        lines.append(f"- 让听众理解：{goal}")

        lines.append("讲解要点（可照读/略作改写）：")
        for b in bullets:
            # Add light expansion prompts without hallucinating specifics
            if re.search(r"(指标|度量|latency|延迟|p95|成功率|准确率|召回|A/B)", b, re.I):
                lines.append(f"- {b}（讲口径：定义→采集→计算→目标阈值→看板）")
            elif re.search(r"(方案|选型|策略|建议|路线图|落地)", b):
                lines.append(f"- {b}（讲顺序：背景→方案→收益→成本/风险→下一步）")
            elif re.search(r"(风险|问题|限制|注意)", b):
                lines.append(f"- {b}（补充：触发条件→影响→规避手段）")
            else:
                lines.append(f"- {b}")
    else:
        lines.append("讲解建议：")
        lines.append("- 本页以图示/结构为主：先说它表示什么，再说你希望听众记住什么。")

    if tables:
        # Provide a generic talk track for tables
        lines.append("表格讲解法（建议）：")
        lines.append("- 先给结论：选哪一行/哪一列更适合什么场景。")
        lines.append("- 再讲 2~3 个关键维度：收益、成本、风险/依赖。")
        lines.append("- 最后落到动作：下一步实验/接入/验收指标是什么。")

    lines.append("过渡话术：")
    lines.append("- “讲完这一页，我们马上看下一页的具体落地方式/对比结果。”")

    return "\n".join(lines).strip() + "\n"


def add_notes(input_pptx: Path, output_pptx: Path) -> None:
    prs = Presentation(str(input_pptx))

    for idx, slide in enumerate(prs.slides, start=1):
        text_blocks = list(_iter_shape_text(slide))
        tables = _extract_tables(slide)
        title, bullets = _summarize_slide(text_blocks, tables)
        notes_text = _notes_template(idx, title, bullets, tables)

        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.clear()
        tf.text = notes_text

    output_pptx.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_pptx))


def main() -> None:
    parser = argparse.ArgumentParser(description="Add speaker notes to each slide based on slide content.")
    parser.add_argument("input", help="Input .pptx path")
    parser.add_argument("-o", "--output", help="Output .pptx path (default: <input>_with_notes.pptx)")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
    else:
        output_path = input_path.with_name(input_path.stem + "_with_notes" + input_path.suffix)

    add_notes(input_path, output_path)
    print(f"OK: wrote notes into {output_path}")


if __name__ == "__main__":
    main()
