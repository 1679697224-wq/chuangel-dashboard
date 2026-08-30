"""零第三方依赖的测试与 Cobertura XML 覆盖率生成器。"""

import ast
from pathlib import Path
import sys
import time
import trace
import unittest
import xml.etree.ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "caixiao" / "backend"
OUTPUT = REPO_ROOT / "caixiao" / "coverage.xml"


def executable_lines(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return sorted({node.lineno for node in ast.walk(tree) if isinstance(node, ast.stmt)})


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT))
    suite = unittest.defaultTestLoader.discover(str(REPO_ROOT / "caixiao" / "tests"), pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    tracer = trace.Trace(count=True, trace=False, ignoredirs=[sys.prefix])
    result = tracer.runfunc(runner.run, suite)
    counts = tracer.results().counts

    root = ET.Element(
        "coverage",
        {
            "version": "stdlib-trace-1",
            "timestamp": str(int(time.time())),
            "branches-covered": "0",
            "branches-valid": "0",
            "branch-rate": "0",
            "complexity": "0",
        },
    )
    ET.SubElement(root, "sources").append(ET.Element("source"))
    root.find("sources/source").text = "."
    packages = ET.SubElement(root, "packages")
    package = ET.SubElement(packages, "package", {"name": "caixiao.backend", "branch-rate": "0", "complexity": "0"})
    classes = ET.SubElement(package, "classes")
    total = covered = 0
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        relative = path.relative_to(REPO_ROOT).as_posix()
        lines = executable_lines(path)
        class_node = ET.SubElement(classes, "class", {"name": relative.replace("/", ".").removesuffix(".py"), "filename": relative, "branch-rate": "0", "complexity": "0"})
        ET.SubElement(class_node, "methods")
        line_nodes = ET.SubElement(class_node, "lines")
        file_covered = 0
        resolved = str(path.resolve())
        for line in lines:
            hits = int(counts.get((resolved, line), 0))
            if hits:
                file_covered += 1
            ET.SubElement(line_nodes, "line", {"number": str(line), "hits": str(hits), "branch": "false"})
        file_rate = file_covered / len(lines) if lines else 1.0
        class_node.set("line-rate", "{:.6f}".format(file_rate))
        total += len(lines)
        covered += file_covered
    rate = covered / total if total else 1.0
    package.set("line-rate", "{:.6f}".format(rate))
    root.set("lines-covered", str(covered))
    root.set("lines-valid", str(total))
    root.set("line-rate", "{:.6f}".format(rate))
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(OUTPUT, encoding="utf-8", xml_declaration=True)
    print("Coverage: {}/{} executable statement lines ({:.2%})".format(covered, total, rate))
    print("Coverage XML: {}".format(OUTPUT))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
