import html as html_lib
import json
import sys
from html.parser import HTMLParser
from pathlib import Path


class Element:
    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.parent = parent
        self.children = []

    @property
    def classes(self):
        return set(self.attrs.get("class", "").split())

    def text(self):
        parts = []
        for child in self.children:
            if isinstance(child, str):
                parts.append(child)
            else:
                parts.append(child.text())
        return " ".join(" ".join(parts).split())


class TreeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element("document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in {"meta", "link", "img", "br", "hr", "input"}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if data.strip():
            self.stack[-1].children.append(html_lib.unescape(data))


def elements(node, tag=None, class_name=None):
    found = []
    for child in node.children:
        if isinstance(child, str):
            continue
        if (tag is None or child.tag == tag) and (class_name is None or class_name in child.classes):
            found.append(child)
        found.extend(elements(child, tag=tag, class_name=class_name))
    return found


def direct_elements(node, tag=None, class_name=None):
    return [
        child
        for child in node.children
        if not isinstance(child, str)
        and (tag is None or child.tag == tag)
        and (class_name is None or class_name in child.classes)
    ]


def direct_span_text(node, class_name):
    for child in direct_elements(node, "span"):
        if class_name in child.classes:
            return child.text()
    return ""


def node_payload(node):
    return {
        "tag": direct_span_text(node, "tag"),
        "name": direct_span_text(node, "name"),
        "description": direct_span_text(node, "desc"),
    }


source = Path(sys.argv[1])
target = Path(sys.argv[2])
parser = TreeParser()
parser.feed(source.read_text(encoding="utf-8"))

tree_candidates = elements(parser.root, "div", "tree")
if not tree_candidates:
    raise RuntimeError("Framework tree not found")
tree = tree_candidates[0]

root_nodes = [node for node in direct_elements(tree, "div", "node") if "root" in node.classes]
root_payload = node_payload(root_nodes[0]) if root_nodes else {}

sections = []
for branch in direct_elements(tree, "div", "branch"):
    if "l1" not in branch.classes:
        continue
    section_nodes = direct_elements(branch, "div", "node")
    if not section_nodes:
        continue
    section = node_payload(section_nodes[0])
    section["subsections"] = []
    children_blocks = direct_elements(branch, "div", "children")
    if children_blocks:
        for sub_branch in direct_elements(children_blocks[0], "div", "branch"):
            sub_nodes = direct_elements(sub_branch, "div", "node")
            if not sub_nodes:
                continue
            subsection = node_payload(sub_nodes[0])
            subsection["items"] = []
            sub_children = direct_elements(sub_branch, "div", "children")
            if sub_children:
                for item in direct_elements(sub_children[0], "div", "node"):
                    if "l2-node" in item.classes:
                        subsection["items"].append(node_payload(item))
            section["subsections"].append(subsection)
    sections.append(section)

head = elements(parser.root, "div", "head")
legend = elements(parser.root, "div", "legend")
hint = elements(parser.root, "div", "hint")
foot = elements(parser.root, "div", "foot")
payload = {
    "source": str(source),
    "titleBlock": head[0].text() if head else "",
    "legend": [span.text() for span in elements(legend[0], "span")] if legend else [],
    "root": root_payload,
    "sections": sections,
    "hint": hint[0].text() if hint else "",
    "foot": foot[0].text() if foot else "",
}
payload["counts"] = {
    "sections": len(sections),
    "subsections": sum(len(section["subsections"]) for section in sections),
    "items": sum(len(subsection["items"]) for section in sections for subsection in section["subsections"]),
}

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(payload["counts"], ensure_ascii=False))
