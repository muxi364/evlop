"""Zero-dependency Model Context Protocol (MCP) JSON-RPC 2.0 Server over stdio supporting multi-workspace mounting."""

from __future__ import annotations

import io
import json
from pathlib import Path
import sys
from typing import Any

from evlop import __version__

_WS_PROP = {
    "type": "string",
    "description": "Optional target project workspace directory path (allows one global MCP server to manage any repo).",
}

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "evlop_init_bootstrap",
        "description": "Initialize and bootstrap EVLOP (.evlop/, AGENTS.md, CLAUDE.md, .cursorrules, .mcp.json) in a workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_dir": _WS_PROP,
                "with_hooks": {"type": "boolean", "default": True},
            },
        },
    },
    {
        "name": "evlop_preflight",
        "description": "[Autopilot Step 1] Run Feynman First-Principles deconstruction + BM25 Gene Recall before coding.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_dir": _WS_PROP,
                "task": {"type": "string", "description": "Task description to deconstruct and recall genes for"},
                "top": {"type": "integer", "default": 5},
            },
            "required": ["task"],
        },
    },
    {
        "name": "evlop_ship",
        "description": "[Autopilot Step 2] Run unit tests + 100-pt AST Quality Gate, and auto-promote verified gene into AGENTS.md & CLAUDE.md.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_dir": _WS_PROP,
                "command": {"type": "string", "description": "Verification shell command to run"},
                "code": {"type": "string", "default": ".", "description": "Python file or directory for AST Quality Gate"},
                "min_quality_score": {"type": "number", "default": 95.0},
                "agent_id": {"type": "string", "default": "mcp-autopilot"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "evlop_recall",
        "description": "[Stage E] Recall relevant evolved engineering genes before coding or debugging.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_dir": _WS_PROP,
                "query": {"type": "string", "description": "Error keyword, symptom, or '*' for top genes"},
                "top": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "evlop_verify",
        "description": "[Stage V] Run deterministic verification shell command gate and auto-diagnose failures.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_dir": _WS_PROP,
                "command": {"type": "string", "description": "Test or build command to execute"},
                "timeout": {"type": "integer", "default": 120},
            },
            "required": ["command"],
        },
    },
    {
        "name": "evlop_log",
        "description": "[Stage L] Record a problem-to-fix episode and create or reinforce an evolutionary gene.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_dir": _WS_PROP,
                "title": {"type": "string"},
                "category": {
                    "type": "string",
                    "enum": ["debugging", "architecture", "testing", "tooling", "workflow"],
                    "default": "debugging",
                },
                "task": {"type": "string"},
                "symptom": {"type": "string"},
                "root_cause": {"type": "string"},
                "fix": {"type": "string"},
                "trigger": {"type": "string"},
                "strategy": {"type": "string"},
                "anti_pattern": {"type": "string"},
                "agent_id": {"type": "string", "default": "mcp-agent"},
                "from_last_failure": {"type": "boolean", "default": False},
            },
            "required": ["task", "root_cause", "fix"],
        },
    },
    {
        "name": "evlop_mutate",
        "description": "[Stage O - DGM Mode] Evolve a child gene mutation from an existing parent gene.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_dir": _WS_PROP,
                "parent_id": {"type": "string"},
                "title": {"type": "string"},
                "strategy": {"type": "string"},
                "reason": {"type": "string", "default": "Empirical refinement"},
                "agent_id": {"type": "string", "default": "mcp-agent"},
            },
            "required": ["parent_id", "title", "strategy"],
        },
    },
    {
        "name": "evlop_lineage",
        "description": "[Stage O - DGM Archive] Render the phylogenetic evolution tree of genes in Mermaid format.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_dir": _WS_PROP,
                "out": {"type": "string", "default": ""},
            },
        },
    },
    {
        "name": "evlop_evolve",
        "description": "[Stages O & P] Deduplicate, fitness-score, supersede ancestors, and compile top genes into AGENTS.md and CLAUDE.md.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_dir": _WS_PROP,
                "target": {"type": "string", "default": "AGENTS.md,CLAUDE.md"},
            },
        },
    },
    {
        "name": "evlop_dag_run",
        "description": "[HomeRail Mode] Execute a heterogeneous multi-agent DAG workflow in topological parallel waves.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_dir": _WS_PROP,
                "spec": {"type": "string", "description": "Path to DAG specification JSON file"},
                "run_id": {"type": "string", "default": ""},
            },
            "required": ["spec"],
        },
    },
    {
        "name": "evlop_status",
        "description": "Inspect EVLOP genome health, promoted genes, swarm contributors, and max generation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_dir": _WS_PROP,
            },
        },
    },
]


def _invoke_cli_capture(argv: list[str], workspace: Path) -> tuple[int, str]:
    from evlop.cli import main

    buf = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout = buf
        sys.stderr = buf
        rc = main(argv, root_dir=workspace)
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
    return rc, buf.getvalue().strip()


def handle_mcp_request(req: dict[str, Any], workspace: Path) -> dict[str, Any] | None:
    """Process a single JSON-RPC 2.0 MCP request dictionary and return the response dictionary."""
    method = req.get("method", "")
    req_id = req.get("id")
    params = req.get("params") or {}

    if method == "notifications/initialized":
        return None

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "evlop-mcp", "version": __version__},
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": MCP_TOOLS},
        }

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments") or {}
        eff_workspace = Path(str(args["workspace_dir"])).resolve() if args.get("workspace_dir") else workspace

        if name == "evlop_init_bootstrap":
            argv = ["init", "--bootstrap"]
            if args.get("with_hooks", True):
                argv.append("--with-hooks")
        elif name == "evlop_preflight":
            argv = ["preflight", str(args["task"]), "--top", str(args.get("top", 5))]
        elif name == "evlop_ship":
            argv = [
                "ship",
                str(args["command"]),
                "--code", str(args.get("code", ".")),
                "--min-quality-score", str(args.get("min_quality_score", 95.0)),
                "--agent-id", str(args.get("agent_id", "mcp-autopilot")),
            ]
        elif name == "evlop_recall":
            argv = ["recall", str(args.get("query", "*")), "--top", str(args.get("top", 5))]
        elif name == "evlop_verify":
            argv = ["verify", str(args["command"]), "--timeout", str(args.get("timeout", 120))]
        elif name == "evlop_log":
            argv = [
                "log",
                "--title", str(args.get("title", "")),
                "--category", str(args.get("category", "debugging")),
                "--task", str(args.get("task", "")),
                "--root-cause", str(args.get("root_cause", "")),
                "--fix", str(args.get("fix", "")),
                "--agent-id", str(args.get("agent_id", "mcp-agent")),
            ]
            if args.get("from_last_failure"):
                argv.append("--from-last-failure")
            if args.get("symptom"):
                argv.extend(["--symptom", str(args["symptom"])])
            if args.get("trigger"):
                argv.extend(["--trigger", str(args["trigger"])])
            if args.get("strategy"):
                argv.extend(["--strategy", str(args["strategy"])])
            if args.get("anti_pattern"):
                argv.extend(["--anti-pattern", str(args["anti_pattern"])])
        elif name == "evlop_mutate":
            argv = [
                "mutate",
                "--parent-id", str(args["parent_id"]),
                "--title", str(args["title"]),
                "--strategy", str(args["strategy"]),
                "--reason", str(args.get("reason", "Empirical refinement")),
                "--agent-id", str(args.get("agent_id", "mcp-agent")),
            ]
        elif name == "evlop_lineage":
            argv = ["lineage", "--mermaid"]
            if args.get("out"):
                argv.extend(["--out", str(args["out"])])
        elif name == "evlop_evolve":
            argv = ["evolve", "--target", str(args.get("target", "AGENTS.md,CLAUDE.md"))]
        elif name == "evlop_dag_run":
            argv = ["dag", "run", str(args["spec"])]
            if args.get("run_id"):
                argv.extend(["--run-id", str(args["run_id"])])
        elif name == "evlop_status":
            argv = ["status", "--json"]
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool: {name}"},
            }

        rc, out_text = _invoke_cli_capture(argv, workspace=eff_workspace)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": out_text}],
                "isError": (rc != 0),
            },
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def run_stdio_server(workspace: Path) -> int:
    """Run MCP JSON-RPC 2.0 server loop over stdin/stdout."""
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_mcp_request(req, workspace=workspace)
            if resp is not None:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except Exception as exc:  # pragma: no cover
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": str(exc)},
            }
            sys.stdout.write(json.dumps(err_resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0
