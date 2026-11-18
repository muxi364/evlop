"""
Deterministic AST Code Quality & Algorithmic Efficiency Auditor (`evlop audit` & `evlop verify --quality-gate`).
Inspects Python source files using the standard `ast` module to catch O(N^2) Cartesian nested loops,
loop-invariant I/O or regex compilation inside loop bodies, swallowed bare exceptions, and missing UTF-8 encoding.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class QualityFinding:
    file: str
    line: int
    severity: str  # "high" | "medium" | "low"
    rule_id: str
    message: str
    penalty: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QualityReport:
    target_path: str
    files_scanned: int
    score: float
    passed: bool
    min_score: float
    findings: list[QualityFinding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_path": self.target_path,
            "files_scanned": self.files_scanned,
            "score": self.score,
            "passed": self.passed,
            "min_score": self.min_score,
            "findings": [f.to_dict() for f in self.findings],
        }


class _AstQualityVisitor(ast.NodeVisitor):
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.findings: list[QualityFinding] = []
        self._loop_depth = 0
        self._loop_iterables: list[str] = []

    def _visit_for_like(self, node: ast.For | ast.AsyncFor) -> None:
        # Visit `iter` and `target` BEFORE incrementing loop body depth
        self.visit(node.target)
        self.visit(node.iter)

        iter_name = ast.unparse(node.iter).strip() if hasattr(ast, "unparse") else ""
        is_cartesian_o_n2 = bool(iter_name and iter_name in self._loop_iterables)

        self._loop_depth += 1
        self._loop_iterables.append(iter_name)

        if is_cartesian_o_n2 or self._loop_depth >= 3:
            self.findings.append(
                QualityFinding(
                    file=self.filename,
                    line=getattr(node, "lineno", 1),
                    severity="medium",
                    rule_id="AST-PERF-NESTED-LOOP",
                    message="O(N^2) nested loop over same collection or deep nesting detected; use hash/dict/set indexing.",
                    penalty=12.0,
                )
            )

        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)

        self._loop_iterables.pop()
        self._loop_depth -= 1

    def visit_For(self, node: ast.For) -> None:
        self._visit_for_like(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._visit_for_like(node)

    def visit_While(self, node: ast.While) -> None:
        self.visit(node.test)
        self._loop_depth += 1
        if self._loop_depth >= 3:
            self.findings.append(
                QualityFinding(
                    file=self.filename,
                    line=getattr(node, "lineno", 1),
                    severity="medium",
                    rule_id="AST-PERF-NESTED-LOOP",
                    message="Deeply nested while loop detected; consider flat state machine or indexing.",
                    penalty=12.0,
                )
            )
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)
        self._loop_depth -= 1

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self.findings.append(
                QualityFinding(
                    file=self.filename,
                    line=getattr(node, "lineno", 1),
                    severity="high",
                    rule_id="AST-REL-BARE-EXCEPT",
                    message="Bare `except:` block catches SystemExit/KeyboardInterrupt and hides bugs.",
                    penalty=20.0,
                )
            )
        elif (
            len(node.body) == 1
            and isinstance(node.body[0], ast.Pass)
            and isinstance(node.type, ast.Name)
            and node.type.id == "Exception"
        ):
            self.findings.append(
                QualityFinding(
                    file=self.filename,
                    line=getattr(node, "lineno", 1),
                    severity="medium",
                    rule_id="AST-REL-SWALLOWED-EXCEPTION",
                    message="Silent `except Exception: pass` swallows runtime errors.",
                    penalty=10.0,
                )
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                func_name = f"{node.func.value.id}.{node.func.attr}"
            else:
                func_name = f".{node.func.attr}"

        if self._loop_depth >= 1 and func_name in ("re.compile", ".read_text", ".write_text"):
            self.findings.append(
                QualityFinding(
                    file=self.filename,
                    line=getattr(node, "lineno", 1),
                    severity="high",
                    rule_id="AST-PERF-LOOP-INVARIANT-CALL",
                    message=f"Expensive call `{func_name}()` inside a loop; hoist outside loop or batch I/O.",
                    penalty=18.0,
                )
            )

        if func_name.endswith((".read_text", ".write_text")):
            kw_names = {kw.arg for kw in node.keywords if kw.arg}
            if "encoding" not in kw_names and not node.args:
                self.findings.append(
                    QualityFinding(
                        file=self.filename,
                        line=getattr(node, "lineno", 1),
                        severity="high",
                        rule_id="AST-IO-MISSING-UTF8-ENCODING",
                        message=f"`{func_name}()` called without explicit `encoding='utf-8'` (causes Windows cp936/gbk crashes).",
                        penalty=15.0,
                    )
                )

        self.generic_visit(node)


def audit_python_path(target_path: Path, min_score: float = 90.0) -> QualityReport:
    """Audit a Python file or directory of Python files and compute a 0..100 deterministic quality score."""
    target_path = Path(target_path).resolve()
    if target_path.is_file():
        py_files = [target_path]
    else:
        py_files = [
            p
            for p in sorted(target_path.rglob("*.py"))
            if ".evlop" not in p.parts and "__pycache__" not in p.parts and ".venv" not in p.parts
        ]

    all_findings: list[QualityFinding] = []
    for py_file in py_files:
        try:
            src = py_file.read_text(encoding="utf-8")
            tree = ast.parse(src, filename=str(py_file))
            visitor = _AstQualityVisitor(py_file.name)
            visitor.visit(tree)
            all_findings.extend(visitor.findings)
        except SyntaxError as exc:
            all_findings.append(
                QualityFinding(
                    file=py_file.name,
                    line=exc.lineno or 1,
                    severity="high",
                    rule_id="AST-SYNTAX-ERROR",
                    message=f"SyntaxError: {exc.msg}",
                    penalty=50.0,
                )
            )

    total_penalty = sum(f.penalty for f in all_findings)
    score = round(max(0.0, 100.0 - total_penalty), 2)
    return QualityReport(
        target_path=str(target_path),
        files_scanned=len(py_files),
        score=score,
        passed=(score >= min_score),
        min_score=min_score,
        findings=all_findings,
    )
