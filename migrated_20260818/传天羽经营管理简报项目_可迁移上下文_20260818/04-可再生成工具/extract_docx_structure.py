import json
import sys
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


def iter_blocks(document):
    for child in document.element.body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, document)
        elif child.tag.endswith("}tbl"):
            yield Table(child, document)


source = Path(sys.argv[1])
target = Path(sys.argv[2])
document = Document(source)
items = []

for block in iter_blocks(document):
    if isinstance(block, Paragraph):
        text = block.text.strip()
        if text:
            style_name = block.style.name if block.style is not None else "无样式"
            items.append({"type": "paragraph", "style": style_name, "text": text})
    else:
        rows = []
        for row in block.rows:
            rows.append([cell.text.strip() for cell in row.cells])
        items.append({"type": "table", "rows": rows})

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"source": str(source), "items": len(items), "tables": sum(item["type"] == "table" for item in items)}, ensure_ascii=False))
