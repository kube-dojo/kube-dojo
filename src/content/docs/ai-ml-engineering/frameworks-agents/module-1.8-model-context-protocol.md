---
title: "Model Context Protocol (MCP) for Agents"
slug: ai-ml-engineering/frameworks-agents/module-1.8-model-context-protocol
sidebar:
  order: 509
---

## Learning Outcomes

By the end of this module, you will be able to:

- **Explain** why agent systems need a shared tool and context protocol instead of a growing pile of custom adapters between every model host and every internal service.
- **Design** an MCP architecture that separates hosts, clients, servers, transports, data access, tool execution, and user approval responsibilities into explicit trust boundaries.
- **Describe** the core MCP primitives, including tools, resources, prompts, and sampling, and choose the right primitive for a read, action, workflow template, or model-mediated request.
- **Trace and implement** the JSON-RPC lifecycle from `initialize` through discovery and invocation by building a small stdio server and client that expose the protocol mechanics directly.
- **Evaluate and compare** security, production deployment, native function calling, and agent-framework integration choices so MCP remains a reusable connector boundary rather than hidden glue code.

## Why This Module Matters

Hypothetical scenario: your engineering organization has three AI coding assistants, two customer-support agents, a custom LangGraph workflow, and a growing list of systems those agents need to inspect or act on: Git repositories, issue trackers, incident tools, Postgres databases, Kubernetes clusters, documentation indexes, and internal APIs. If every host needs custom wiring for every system, the integration surface grows as a product of both sides. Five hosts and twelve data sources do not create seventeen decisions; they can create sixty separate adapter contracts, each with its own schema drift, authentication behavior, error handling, and operational blind spots.

MCP matters because it attacks that "M x N" integration problem at the protocol boundary. Instead of making every AI host understand the private API shape of every tool provider, MCP defines how a host creates a client connection to a server, how that server advertises capabilities, and how the client asks for context or requests a controlled action. The server remains responsible for translating the protocol request into the real business system, while the host remains responsible for user experience, model orchestration, consent, and policy.

The durable lesson is not a particular SDK import, a vendor UI, or a June 2026 feature checklist. The durable lesson is that agent tool integration becomes safer when the boundary is explicit. A protocol gives you a place to negotiate versions, declare capabilities, validate inputs, classify reads separately from actions, apply authentication outside the model prompt, and observe every call as a real distributed-system event. MCP is one open standard for that boundary, and you should study it as systems engineering rather than as another prompt-engineering trick.

> **MCP snapshot - as of 2026-06-08**: the public MCP specification page identifies `2025-11-25` as the latest specification revision; commonly referenced official SDK packages include Python package `mcp` from `modelcontextprotocol/python-sdk` and TypeScript package `@modelcontextprotocol/sdk` from `modelcontextprotocol/typescript-sdk`; OpenAI's Agents SDK documents MCP integrations through its own server abstractions. The MCP spec and SDK APIs evolve, so verify the current spec revision, transport names, SDK package names, and code-level APIs at `modelcontextprotocol.io` before relying on version-specific details.

## The Integration Problem MCP Tries to Solve

Before protocols enter the picture, tool use usually starts with direct model-provider function calling. You define a JSON schema for a function such as `search_docs`, send that schema to the model API, receive a tool-call request from the model, execute application code, and send the tool result back into the conversation. That pattern is useful and remains important. It gives a single application a clean way to expose a handful of local functions to a model through the provider API it already uses.

The problem appears when tool surfaces become shared infrastructure instead of single-application helpers. A documentation team may want one search server that works in multiple IDEs, chat tools, and agent frameworks. A platform team may want one Kubernetes diagnostics server with carefully reviewed read-only tools, approval-gated remediation tools, and audit logging. A security team may want tool descriptions and authorization policy owned by the system team rather than copied into every agent prompt. Provider-native function calling does not automatically solve that cross-host distribution problem because the schemas, transports, and lifecycle are normally embedded inside each application.

MCP changes the shape of the problem by standardizing the connector boundary. A server publishes a set of capabilities through the protocol; a host application creates one client connection per server; the client discovers tools, resources, prompts, and client/server capabilities at runtime; and the host decides how those capabilities become available to the model and user. The server can be local, such as a subprocess launched by an IDE, or remote, such as a network service reached over HTTP. Either way, the model does not need raw database credentials, and the host does not need bespoke integration code for every backend.

Think of MCP as the adapter standard between agent hosts and context providers, not as the agent's brain. The LLM still reasons through the task, the host still manages the conversation, and your business systems still enforce their own rules. MCP gives those pieces a common language for "what can you do?", "what context can I read?", "please perform this named action with these arguments", "here is the result", and "this connection supports these optional features." That is a narrower claim than saying MCP replaces every tool-calling API, and it is the claim that remains useful even as SDKs and host products change.

The most important design shift is that the integration boundary becomes inspectable. Without a protocol, teams often hide tool wiring inside prompts, callback functions, or framework-specific nodes. With a protocol, you can test `tools/list` without running a full conversation, validate `tools/call` arguments before a model ever sees the result, replay JSON-RPC transcripts during debugging, and place rate limits or authorization checks at the server boundary. Protocols do not make bad tools safe, but they make tool behavior concrete enough to secure, observe, and review.

## The MCP Architecture: Hosts, Clients, and Servers

MCP uses a client-server architecture with three roles that are easy to blur if you only look at a polished product UI. The host is the application the user experiences, such as an IDE, a desktop assistant, a web chat product, or a headless agent runner. The client is the protocol component inside that host that manages one connection to one MCP server. The server is the program or service that exposes context and capabilities through MCP.

That separation matters because policy decisions live at different layers. The server knows the backend system, validates arguments, executes actions, and decides what it is willing to expose. The client speaks the protocol, maintains the connection, and correlates requests with responses. The host decides when to ask the model, how to present tool choices, whether a user must approve a call, how to store conversation state, and how to combine multiple servers into one agent experience. In a well-designed system, none of those responsibilities are silently delegated to the model.

```text
User
  |
  v
MCP Host: IDE, chat app, workflow runner, or agent framework
  |
  +-- MCP Client A ---- transport ---- MCP Server A ---- docs index
  |
  +-- MCP Client B ---- transport ---- MCP Server B ---- incident API
  |
  +-- MCP Client C ---- transport ---- MCP Server C ---- local filesystem

The host may connect to many servers, but each client connection has one
server-side peer, one negotiated protocol lifecycle, and one stream of
JSON-RPC messages to correlate.
```

A local server often runs as a child process of the host and communicates over standard input and standard output. That form is convenient for developer tools because installation can be as simple as configuring a command, arguments, and environment variables. A remote server usually runs as an independent process behind an HTTP endpoint and can serve many clients. That form fits shared enterprise systems, but it also moves the problem into normal web-service territory: authentication, authorization, session handling, origin checks, TLS, rate limits, incident response, and service ownership all matter.

MCP's architecture also lets you avoid a common agent anti-pattern: treating the tool list as prompt text. In brittle systems, tool names, argument formats, and examples are pasted into a system prompt and expected to stay synchronized with real code. In MCP, discovery is a protocol operation. The client can ask the server what tools exist, what schemas they accept, what resources are available, and what prompt templates the server offers. The host may still summarize those capabilities for a model, but the source of truth is a server response, not a stale paragraph in a prompt.

The model itself is not a protocol peer in the same sense. A model may decide that a tool should be used, but the host and client translate that intent into an MCP request. That distinction protects the architecture from a subtle mistake: giving model output the same authority as a signed client request. The server should validate every argument, enforce its own permissions, and return explicit success or error results. The host should decide whether the user or policy engine must approve the call before it reaches the server.

## The Core Primitives: Tools, Resources, Prompts, and Sampling

MCP's server-side primitives are intentionally small. A resource is readable context identified by a URI, a tool is an executable function with structured arguments, and a prompt is a reusable message template that a server can expose to users through the host. Client-side features include sampling, where a server can ask the host's model to generate a response under host control, along with other capabilities such as roots and elicitation in newer revisions. The important habit is choosing a primitive based on semantics rather than convenience.

Use a resource when the client needs to read context without causing side effects. A resource might represent `repo://README.md`, `incident://INC-1042/timeline`, `schema://payments/orders`, or `policy://deployment-gate`. Reading it should not restart a service, create a ticket, mutate a database row, or send a message. Treat resources as the "reference shelf" of the server. They can be dynamic, paginated, or generated on demand, but the act of reading should remain safe enough for the host to reason about separately from actions.

Use a tool when the operation performs computation, reaches into a backend API, or may change state. Searching an index can be modeled as a tool because it computes a ranked result from arguments. Updating an incident, creating a pull request, rotating a key, restarting a deployment, or sending an email is definitely a tool because it has side effects. A tool definition should include a clear description and a JSON schema for inputs, but that schema is only the outer gate. The server still needs business validation, authorization checks, idempotency decisions, and careful error reporting.

Use a prompt when the server owns a workflow template rather than a backend operation. For example, a code-review server might expose a `review_security_diff` prompt that accepts a diff resource URI and returns a structured set of messages for the host to present as a command. A prompt is user-controlled in the usual interaction model: the user or host selects it, arguments are filled in, and the resulting message sequence can be sent to the model. That is different from a model autonomously calling a tool.

Sampling is easiest to misunderstand because it flows in the opposite direction from tool calls. With sampling, a server can request that the client ask the host's language model for a generation, while the client retains control over model access, permissions, and what the server can see. That can support advanced workflows where a server needs model assistance, but it should be treated as sensitive. The server is asking the host to spend model budget and potentially expose context, so approval, visibility, and least-privilege controls matter.

The primitive choice creates a security story. If you hide a destructive operation behind a resource read, a host might prefetch it, index it, or display it without an approval flow. If you expose a read-only lookup as a high-risk tool, users may suffer approval fatigue and start clicking through prompts. If you put workflow policy only inside prompt text, the server cannot enforce it. Good MCP design makes the action class obvious before the model generates any arguments.

## Transport and JSON-RPC Message Flow

MCP separates the data layer from the transport layer. The data layer uses JSON-RPC 2.0 messages: requests have a `method`, optional `params`, and an `id`; responses carry the same `id` with either `result` or `error`; notifications are requests without an `id` and do not receive responses. The transport layer decides how those JSON-RPC messages move between client and server. The standard transports are stdio for local process communication and Streamable HTTP for networked communication.

The lifecycle begins with initialization. The client sends `initialize` with the protocol version it supports, client capabilities, and client information. The server responds with the selected protocol version, server capabilities, server information, and optional instructions. Then the client sends `notifications/initialized` to mark the start of normal operation. Only after that handshake should the client rely on discovered capabilities or call server methods. Version and capability negotiation are not ceremony; they prevent a host from assuming a tool, prompt, or transport behavior that the server never promised.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "<negotiated-version>",
    "capabilities": {
      "sampling": {},
      "roots": {}
    },
    "clientInfo": {
      "name": "example-agent-host",
      "version": "1.0.0"
    }
  }
}
```

After initialization, discovery calls reveal what the server exposes. `tools/list` returns tool definitions and input schemas. `resources/list` returns resource metadata and URIs. `prompts/list` returns prompt templates and arguments. A client may cache these lists when the server says it is safe or when the host accepts staleness, but dynamic systems should handle list-change notifications and cache invalidation. Discovery is also where a host can filter capabilities before they reach the model, such as hiding write tools from a read-only session.

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

A tool call is a separate JSON-RPC request, not a magical continuation of the model's text. The host may receive a model-provider tool-use event, apply policy, ask for user approval, and then send `tools/call` to the MCP server. The server validates `name` and `arguments`, executes the allowed operation, and returns a structured result or a structured error. If a network failure happens after the server performs a side effect but before the response reaches the client, retry behavior becomes a distributed-systems problem. That is why state-changing tools need idempotency keys, request IDs, or "check before mutate" patterns when duplicate execution would be harmful.

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "check_deployment_policy",
    "arguments": {
      "service": "payments-api",
      "environment": "production",
      "replicas": 4
    }
  }
}
```

Stdio transport is simple but strict. The client launches the server as a subprocess, writes JSON-RPC messages to the server's standard input, and reads JSON-RPC messages from the server's standard output. Anything written to standard output that is not a valid MCP message corrupts the protocol stream. Logs, debug traces, progress messages meant for humans, and stack traces must go to standard error or a separate log sink. This one rule explains many local MCP failures: a harmless `print("starting")` can become a parse error in the client.

Streamable HTTP is a better fit when the server is remote or shared by multiple hosts. The client sends JSON-RPC messages to a single MCP endpoint using HTTP POST, and the server can return JSON directly or stream messages through Server-Sent Events when needed. HTTP introduces security obligations that stdio does not have: validate origins to reduce DNS rebinding risk, bind local development servers to `127.0.0.1` rather than all interfaces, authenticate remote clients, protect session identifiers, and treat transport headers as part of the security boundary rather than as incidental plumbing.

Timeouts, cancellation, progress, and error handling should be designed before production traffic arrives. A client should not wait forever for a hung tool. A server should not keep expensive work running after the user cancels. Long-running tools should emit progress where supported and should be safe to resume, poll, or cancel. JSON-RPC error codes give you a protocol vocabulary for malformed requests, missing methods, invalid parameters, and internal failures, but your application still needs domain-specific error messages that a host can display and a model can use for recovery.

## Building a Minimal MCP-Style Server

Real production code should use an SDK when one fits your language and deployment model, because SDKs handle many edge cases around message framing, validation, transports, pagination, and compatibility. For learning, however, a tiny stdio server is valuable because it exposes the actual protocol shape. The following standard-library Python example implements the core ideas: initialization, resource discovery, resource reading, prompt discovery, prompt retrieval, tool discovery, and tool execution. It intentionally logs to standard error so standard output remains reserved for JSON-RPC messages.

```python
# mcp_policy_server.py
import json
import logging
import sys
from typing import Any

PROTOCOL_VERSION = "2025-11-25"

POLICY_TEXT = """Deployment gate policy:
- Production services must run at least three replicas.
- Production deployments must include an owner label.
- Staging deployments may run with one replica for cost control.
"""

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(levelname)s %(message)s",
)


def rpc_result(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def rpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def list_tools() -> dict[str, Any]:
    return {
        "tools": [
            {
                "name": "check_deployment_policy",
                "title": "Check Deployment Policy",
                "description": (
                    "Evaluate whether a service deployment request satisfies "
                    "the example platform policy."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "service": {
                            "type": "string",
                            "description": "Service name, such as payments-api.",
                        },
                        "environment": {
                            "type": "string",
                            "enum": ["staging", "production"],
                        },
                        "replicas": {
                            "type": "integer",
                            "minimum": 1,
                        },
                        "owner": {
                            "type": "string",
                            "description": "Owning team label for production.",
                        },
                    },
                    "required": ["service", "environment", "replicas"],
                    "additionalProperties": False,
                },
            }
        ]
    }


def call_tool(params: dict[str, Any]) -> dict[str, Any]:
    if params.get("name") != "check_deployment_policy":
        return {
            "content": [{"type": "text", "text": "Unknown tool requested."}],
            "isError": True,
        }

    arguments = params.get("arguments") or {}
    service = arguments.get("service")
    environment = arguments.get("environment")
    replicas = arguments.get("replicas")
    owner = arguments.get("owner", "")

    violations: list[str] = []
    if not isinstance(service, str) or not service:
        violations.append("service must be a non-empty string")
    if environment not in {"staging", "production"}:
        violations.append("environment must be staging or production")
    if not isinstance(replicas, int) or replicas < 1:
        violations.append("replicas must be a positive integer")
    if environment == "production" and isinstance(replicas, int) and replicas < 3:
        violations.append("production deployments require at least three replicas")
    if environment == "production" and not owner:
        violations.append("production deployments require an owner label")

    allowed = not violations
    summary = "allowed" if allowed else "blocked"
    text = f"Deployment for {service!r} is {summary}."
    if violations:
        text += " Violations: " + "; ".join(violations)

    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": {
            "allowed": allowed,
            "violations": violations,
        },
        "isError": False,
    }


def list_resources() -> dict[str, Any]:
    return {
        "resources": [
            {
                "uri": "policy://deployment-gate",
                "name": "Deployment gate policy",
                "description": "Read-only policy used by the example tool.",
                "mimeType": "text/plain",
            }
        ]
    }


def read_resource(params: dict[str, Any]) -> dict[str, Any]:
    uri = params.get("uri")
    if uri != "policy://deployment-gate":
        raise ValueError(f"unknown resource URI: {uri}")
    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": "text/plain",
                "text": POLICY_TEXT,
            }
        ]
    }


def list_prompts() -> dict[str, Any]:
    return {
        "prompts": [
            {
                "name": "deployment_review",
                "title": "Deployment Review",
                "description": "Ask the model to review a deployment plan.",
                "arguments": [
                    {
                        "name": "service",
                        "description": "Service being deployed.",
                        "required": True,
                    }
                ],
            }
        ]
    }


def get_prompt(params: dict[str, Any]) -> dict[str, Any]:
    if params.get("name") != "deployment_review":
        raise ValueError("unknown prompt")
    service = (params.get("arguments") or {}).get("service", "the service")
    return {
        "description": "Review a deployment against the policy resource.",
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": (
                        f"Review {service} against policy://deployment-gate "
                        "before recommending a production deployment."
                    ),
                },
            }
        ],
    }


def handle(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}

    try:
        if method == "initialize":
            return rpc_result(
                request_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"listChanged": False},
                        "prompts": {"listChanged": False},
                    },
                    "serverInfo": {
                        "name": "policy-lab",
                        "version": "1.0.0",
                    },
                },
            )
        if method == "notifications/initialized":
            logging.info("client initialized")
            return None
        if method == "tools/list":
            return rpc_result(request_id, list_tools())
        if method == "tools/call":
            return rpc_result(request_id, call_tool(params))
        if method == "resources/list":
            return rpc_result(request_id, list_resources())
        if method == "resources/read":
            return rpc_result(request_id, read_resource(params))
        if method == "prompts/list":
            return rpc_result(request_id, list_prompts())
        if method == "prompts/get":
            return rpc_result(request_id, get_prompt(params))
        return rpc_error(request_id, -32601, f"method not found: {method}")
    except ValueError as exc:
        return rpc_error(request_id, -32602, str(exc))
    except Exception as exc:
        logging.exception("internal server error")
        return rpc_error(request_id, -32603, f"internal error: {exc}")


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            response = rpc_error(None, -32700, "parse error")
        else:
            response = handle(message)

        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
```

This example is intentionally small, but it already shows several production habits. The server validates every business rule inside `call_tool` instead of trusting the caller. It returns resources through a URI and marks them read-only by behavior, not by hope. It exposes prompts as templates rather than embedding workflow text into a hidden client. It keeps logs away from stdout. It distinguishes protocol errors, such as unknown methods or invalid parameters, from domain results, such as a deployment being blocked by policy.

## Building a Minimal Client and Reading the Transcript

An MCP client is responsible for connection management, request IDs, JSON-RPC correlation, and lifecycle order. A full host would also decide how capabilities are surfaced to the model, whether tool calls require user approval, and how tool results are appended to the conversation. The following minimal client does only the protocol work needed to test the server. That narrowness is useful because it lets you debug the integration before adding an LLM or framework.

```python
# mcp_policy_client.py
import json
import subprocess
from itertools import count
from typing import Any


class StdioRpcClient:
    def __init__(self, command: list[str]) -> None:
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.ids = count(1)

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_id = next(self.ids)
        message: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params is not None:
            message["params"] = params
        self._send(message)
        response = self._read()
        if response.get("id") != request_id:
            raise RuntimeError(f"response id mismatch: {response}")
        return response

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        self._send(message)

    def _send(self, message: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def _read(self) -> dict[str, Any]:
        assert self.process.stdout is not None
        line = self.process.stdout.readline()
        if not line:
            stderr = ""
            if self.process.stderr is not None:
                stderr = self.process.stderr.read()
            raise RuntimeError(f"server closed stdout. stderr={stderr!r}")
        return json.loads(line)

    def close(self) -> None:
        if self.process.stdin is not None:
            self.process.stdin.close()
        self.process.terminate()
        self.process.wait(timeout=5)


def main() -> None:
    client = StdioRpcClient([".venv/bin/python", "mcp_policy_server.py"])
    try:
        print("initialize")
        print(json.dumps(client.request("initialize", {
            "protocolVersion": "2025-11-25",
            "capabilities": {"sampling": {}},
            "clientInfo": {"name": "policy-lab-client", "version": "1.0.0"},
        }), indent=2))

        client.notify("notifications/initialized")

        print("tools/list")
        print(json.dumps(client.request("tools/list"), indent=2))

        print("resources/read")
        print(json.dumps(client.request("resources/read", {
            "uri": "policy://deployment-gate",
        }), indent=2))

        print("prompts/get")
        print(json.dumps(client.request("prompts/get", {
            "name": "deployment_review",
            "arguments": {"service": "payments-api"},
        }), indent=2))

        print("tools/call")
        print(json.dumps(client.request("tools/call", {
            "name": "check_deployment_policy",
            "arguments": {
                "service": "payments-api",
                "environment": "production",
                "replicas": 2,
                "owner": "platform",
            },
        }), indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
```

Read the transcript as a protocol debugger would. The `initialize` response tells you what the server claims to support. The `tools/list` response is the tool contract the host may expose to a model. The `resources/read` response proves that read-only context can travel separately from tool execution. The `prompts/get` response shows how a server-owned workflow template can become a user-visible prompt. The `tools/call` response returns both human-readable text and structured content, which gives the host a better basis for UI, logs, tests, and model feedback.

The client also demonstrates why request IDs matter. JSON-RPC responses can arrive out of order when concurrency is introduced, especially over network transports or long-running tools. A robust client cannot assume "the next line belongs to the last request" once it allows parallel calls, notifications, or streaming. It must correlate by `id`, handle notifications separately, apply timeouts, and decide how cancellation affects in-flight work. This minimal client stays sequential so the mechanics are visible, but production clients need a real request table.

## Designing Capability Contracts That Age Well

The hardest MCP design decisions are usually not about syntax. They are about naming, scope, risk, and ownership. A capability contract is the promise your server makes to hosts: these tools exist, these arguments mean this, these resources can be read, these prompts express supported workflows, these errors are recoverable, and these operations have these side effects. If that contract is sloppy, a perfect SDK cannot rescue the integration. The model may call the wrong thing, the host may present a misleading approval prompt, and the backend team may be unable to change behavior without breaking every client.

Start with tool names that describe domain intent rather than implementation mechanics. A tool named `post` or `execute` forces the host, user, and reviewer to inspect arguments before they understand risk. A tool named `create_incident_note`, `search_release_docs`, or `dry_run_deployment_policy` communicates the action class immediately. Names should be stable enough for host allowlists and observability dashboards, while descriptions can carry more detailed guidance about when the tool is appropriate. If you later need a materially different behavior, prefer a new tool name over silently changing the semantics of an old one.

Separate dry-run, read, and write operations even when they hit the same backend. A deployment server might expose a read resource for the current policy, a `dry_run_deployment_policy` tool that evaluates a proposed change, and a separate `request_deployment_approval` tool that starts a real workflow. That separation lets the host apply different approval rules, lets the model learn a safer plan-first pattern, and gives auditors a clearer trail. A single `deploy` tool with a `dry_run` boolean is tempting, but it makes policy enforcement and user messaging easier to get wrong.

Design arguments as a public API, not as whatever your internal function happens to accept. Use explicit enums for small domains, separate identifiers from display names, avoid overloaded strings that sometimes contain JSON, and include optional idempotency keys for state-changing calls. A good schema helps the host produce useful forms and approval dialogs, but it should also be pleasant for humans reading logs. If an argument would be dangerous when guessed by a model, require the server to derive it from authenticated context or a prior resource read instead of accepting it directly.

Treat tool results as part of the contract too. A model-visible text result is useful, but structured content can make the host safer. For example, returning `{ "allowed": false, "violations": [...] }` lets the host show a clear blocked state, lets tests assert behavior without parsing prose, and lets a model retry with specific corrections. Avoid returning secrets, raw tokens, or full records when the task only needs a status. If the result is large, return a summary plus a resource URI or cursor so follow-up reads can stay narrow.

Resources need naming discipline as well. URI schemes should communicate ownership and stability, such as `policy://deployment-gate` for a server-owned logical policy or `repo://src/app.py` for a workspace-root-relative file. Avoid exposing raw filesystem paths, database connection details, or tenant identifiers unless the host and server have a clear reason to reveal them. If a resource can change, include enough metadata for freshness decisions, and consider list-change or subscription behavior only when clients actually need it. "Everything is a resource" is as dangerous as "everything is a tool" because it hides intent.

Prompts should encode supported workflows without becoming an escape hatch for policy. A server-provided prompt can help users invoke a repeatable review, migration, or investigation pattern, but the server should not assume that prompt text enforces security. If the prompt says "only perform read-only analysis," the tools still need read-only permissions. If the prompt says "ask for confirmation before writing," the host still needs an approval flow. Prompts improve ergonomics; they do not replace authorization.

Sampling should be rare in simple servers and explicit in advanced ones. When a server requests model generation through the client, it is asking the host to spend model budget and potentially expose context. That can be appropriate for a mediator server, a workflow assistant, or a server that needs a model to transform retrieved data, but it should be visible to the user or policy layer. Servers should avoid sampling when deterministic code, search, or a narrow tool result would solve the problem. The more recursive the agent loop becomes, the more important observability and cancellation become.

## Debugging MCP Integrations Systematically

When an MCP integration fails, resist the urge to start by changing the model prompt. First decide which layer is failing. A transport failure means the client and server are not reliably exchanging JSON-RPC messages. A lifecycle failure means initialization or capability negotiation did not complete. A discovery failure means the server is reachable but not advertising what the host expects. An invocation failure means a listed tool, resource, or prompt cannot be used successfully. A reasoning failure means the protocol worked, but the model or host chose the wrong capability or misused a valid result.

For transport failures, capture the raw message stream in the smallest possible reproduction. With stdio, verify that every stdout line is valid JSON and that logs are on stderr. With HTTP, verify status codes, content types, accepted media types, protocol-version headers, session headers, and whether SSE streams are being opened or resumed as expected. If the protocol transcript is invalid, changing tool descriptions will not help. You need framing, buffering, timeout, or server process fixes first.

For lifecycle failures, inspect the `initialize` request and response before looking at tools. Confirm that the client sends a supported protocol version, the server responds with a version the client can use, and the client sends `notifications/initialized` before normal requests. Then inspect capabilities. A host that assumes prompts exist when the server did not advertise `prompts` is a client bug. A server that advertises `tools` but returns `method not found` for `tools/list` is a server contract bug. Capability negotiation turns vague incompatibility into a concrete diff.

For discovery failures, compare the server's advertised schema with the host's filtered tool list. Some hosts intentionally hide tools based on trust settings, workspace policy, duplicate names, server allowlists, or approval configuration. The server may be correct while the host is correctly refusing to expose a risky tool. Conversely, the host may show a stale cached tool list after a server update. In dynamic environments, list-change notifications and explicit cache invalidation become part of the operational design rather than optional polish.

For invocation failures, separate protocol errors from domain errors. A JSON-RPC `Invalid params` error means the request did not satisfy the method contract. A normal `tools/call` result with `isError` or a blocked status may mean the tool ran and returned a domain-level denial. Those outcomes should be logged and surfaced differently. Protocol errors usually point to client, schema, or compatibility problems. Domain denials usually point to user input, authorization, policy, or backend state. Blending them into one "tool failed" message makes both humans and models worse at recovery.

For reasoning failures, keep the protocol transcript but inspect the host's model-facing representation. Did the host expose too many similar tools? Did two servers publish a tool named `search` without server prefixes? Did the tool description omit the risk boundary? Did the model receive a huge result and miss the important field? Did a prompt template override the user's real intent? MCP makes capabilities discoverable, but host design still determines how those capabilities are converted into model context and user decisions.

The strongest debugging habit is to create a deterministic harness before involving a model. A small client script can initialize, list capabilities, read one resource, fetch one prompt, call one allowed tool, call one denied tool, and assert exact structured outputs. Once that harness passes, add the host and confirm its filtering or approval behavior. Only then ask whether the model chooses the right tool. This order keeps probabilistic reasoning from masking deterministic integration bugs.

## Security, Authorization, and Trust Boundaries

MCP standardizes communication, but it does not make exposed capabilities safe by itself. A server that exposes `delete_customer`, `run_shell`, or `read_file` is still exposing a powerful operation. The protocol gives you places to attach consent, schemas, authorization, and logs; it does not decide your business risk. Treat every MCP server as code running at a boundary between probabilistic model output and deterministic systems of record.

The first trust boundary is between model intent and host action. A model can propose a tool call, but the host should decide whether that proposal is allowed in the current session. Read-only tools might be automatic in a trusted workspace, while write tools might require explicit user confirmation, policy-engine approval, or a dry-run result before execution. The user interface should show which server and tool are being invoked, which arguments will be sent, and what data may return. Hidden tool calls are difficult to debug and easier to abuse.

The second trust boundary is between host/client and server. A local stdio server runs with the operating-system permissions of the process the host starts, unless you deliberately isolate it. That means a filesystem server, shell server, browser server, or database proxy can reach whatever its process account can reach. Use least-privilege accounts, workspace-root allowlists, canonical path checks, read-only modes, separate credentials per server, and operating-system sandboxing where appropriate. Never rely on "the model would not ask for that path" as a security control.

The third trust boundary is between remote clients and remote servers. Streamable HTTP brings normal web-service security requirements: TLS, authentication, authorization, secure session identifiers, origin validation, rate limits, request-size limits, audit logs, and incident playbooks. The MCP authorization specification describes OAuth-based patterns for HTTP transports, but your deployment still has to map identities to backend permissions. A remote server should know whether it is serving a human's delegated session, a service account, or a shared agent runtime, because those identities should not have the same authority.

Tool descriptions and prompt templates deserve special skepticism. They can influence model behavior, but they are not proof that the server is safe. The MCP specification explicitly treats tools as powerful because they can represent arbitrary code execution paths. A malicious or compromised server could advertise a harmless-looking tool while performing a different backend action. Hosts should give users clear server provenance, allowlist trusted servers, review server manifests where available, and apply policy based on server identity and tool risk rather than on prose descriptions alone.

Server-side validation remains mandatory even when input schemas are present. JSON schemas help the model and client produce well-shaped arguments, but they do not enforce domain rules by themselves. A schema can say `replicas` is an integer; the server must still decide whether two production replicas are allowed. A schema can say `path` is a string; the server must still resolve it, canonicalize it, and verify it remains under the permitted root. A schema can say `query` is a string; the server must still parameterize database access and restrict returned data.

## Production Deployment Patterns

A production MCP deployment should start with ownership. Every server needs a responsible team, a source repository, a release process, a security review path, and a way to revoke access. "An agent can use it" is not an operational model. The server is an integration service that may reach sensitive systems, so it should have the same service-management basics as any other internal API: dependency inventory, observability, alerting, rollbacks, vulnerability handling, and documentation.

Local stdio servers work well for developer productivity, but they are not automatically enterprise-ready. Installation configuration can drift across laptops, environment variables can leak into child processes, and local credentials may be broader than intended. Prefer narrowly scoped tokens, explicit workspace roots, deterministic command configuration, and reproducible packaging. For teams, provide a managed configuration generator or extension rather than asking every developer to paste arbitrary server commands into a local settings file.

Remote servers centralize control but increase blast radius. A shared incident-management MCP server can enforce one policy and one audit trail for many agents, but a bug can affect every host that depends on it. Design remote servers like public APIs even when they are internal: version endpoints or protocol behavior carefully, publish compatibility expectations, protect against high-cardinality or long-running requests, set per-tool timeouts, and make tool results small enough for model contexts. Large data should usually be represented through resources, pagination, summaries, or follow-up queries rather than dumped into a single tool response.

Observability should include both protocol-level and domain-level fields. At the protocol level, log server identity, client identity where available, session ID, method, request ID, latency, result or error class, payload size, and negotiated protocol version. At the domain level, log the backend object being read or changed, the authorization decision, the approval decision, and the idempotency key for side-effecting operations. Avoid logging raw secrets, full prompts, or sensitive tool results unless there is a deliberate retention policy and access model.

Version compatibility is another production concern. The initialization lifecycle exists because clients and servers may support different protocol revisions and optional capabilities. A server should reject unsupported protocol versions clearly, and a client should disconnect when it cannot safely use the server's selected version. Capability checks should gate optional behavior. For example, do not assume prompt templates, resource subscriptions, sampling, or list-change notifications exist just because another server supported them in a demo.

Finally, test the protocol surface directly. Unit tests should call server handlers with valid and invalid arguments. Integration tests should run the server over its intended transport and verify initialization, discovery, a successful read, a successful tool call, a denied tool call, malformed JSON, invalid parameters, timeout behavior, and shutdown. For write tools, include idempotency and duplicate-request tests. LLM-based evaluation can help with end-to-end behavior, but the protocol contract should pass deterministic tests before any model is in the loop.

## MCP, Native Function Calling, and Agent Frameworks

MCP and native function calling solve adjacent problems, not identical ones. Native function calling is a model-provider interface: you give the model a set of function schemas in a request, the model emits a tool call in the provider's response format, your application executes the function, and you return the result through that provider's conversation protocol. It is excellent when the functions are local to one application or tightly coupled to one provider flow.

MCP is a connector protocol between hosts and external context providers. It defines how a server advertises capabilities and how a client invokes them, independent of the model provider used by the host. A host may translate MCP tools into OpenAI function tools, Anthropic tool-use blocks, Gemini function calls, or an agent framework's internal tool abstraction. That translation belongs in the host or framework layer. The MCP server should not need to know which model eventually reasons over its tool description.

Agent frameworks sit above or beside MCP depending on their role. A framework such as a graph runner, planner, memory system, or orchestration library may use MCP clients to discover and call tools. It may also expose an MCP server so other hosts can reuse one of its workflows. The framework still owns planning, state, retries, memory, evaluator loops, or multi-agent coordination. MCP owns the interoperable boundary for capabilities. Keeping that boundary clean prevents a framework migration from becoming a rewrite of every backend connector.

A practical rule is to use native function calling for application-local tools, MCP for reusable cross-host connectors, and an agent framework when you need workflow control beyond a single model turn. Those layers can coexist. For example, an agent framework can connect to three MCP servers, filter their tools, expose a subset through a provider's function-calling API, and use framework state to decide when to retry. The architecture is healthy when each layer has one job and when backend authority remains on the server side.

## Did You Know?

1. MCP's public documentation compares its role to a standardized connector for AI applications, but the more useful engineering interpretation is narrower: it standardizes how hosts and servers exchange context, capabilities, and tool calls without standardizing how the host reasons.

2. MCP's stdio transport is deliberately strict about stdout because stdout carries protocol messages. A single human-oriented debug line on stdout can break parsing, while stderr remains available for logs that the client may capture, forward, or ignore.

3. MCP uses JSON-RPC 2.0 as its message envelope, which means request IDs are not decoration. They are the mechanism that lets clients correlate responses with requests when multiple operations, notifications, or streamed responses are in flight.

4. MCP resources and tools are different by intent, not by data format. A resource can contain generated text or binary content, and a tool can return text, images, embedded resources, or structured data, but the resource should remain read-oriented while the tool represents computation or action.

## Common Mistakes

| Mistake | Why it causes trouble | Better approach |
|---|---|---|
| Treating MCP as a replacement for all native function calling. | Native function calling is still useful for application-local functions, while MCP is strongest when the same capability should be reusable across hosts or served by another owner. | Use native tools for local application callbacks, use MCP for shared servers, and document which layer owns validation and execution. |
| Exposing destructive actions as resources because they are easy for the client to discover. | Hosts may prefetch or display resources as context, so a resource with side effects can bypass the approval path users expect for actions. | Model reads as resources and state-changing or expensive operations as tools with explicit approval, validation, and audit behavior. |
| Trusting the model because the tool has a JSON schema. | A schema can improve argument shape, but it cannot enforce business authorization, path boundaries, quota policy, or safe retry behavior. | Validate arguments on the server, authorize against the real caller, and treat every tool call as untrusted input crossing a service boundary. |
| Logging debug output to stdout in a stdio server. | The stdio transport reserves stdout for JSON-RPC messages, so ordinary prints can corrupt the message stream and appear as client parse failures. | Send logs to stderr or a structured log sink, and add an automated test that launches the server and parses every stdout line as JSON. |
| Building one giant tool that accepts arbitrary instructions. | A catch-all tool hides risk from the host, prevents meaningful approval prompts, and makes observability too coarse for incident response. | Expose narrow tools with clear names, typed arguments, domain validation, and separate risk levels for read, dry-run, and write operations. |
| Returning huge backend payloads directly to the model. | Large tool results can exceed context limits, increase latency and cost, and expose more sensitive data than the user needed for the task. | Return summaries, resource links, cursors, or paginated results, and let the host or model request narrower follow-up context when necessary. |
| Assuming every MCP host supports every optional capability. | Capabilities such as prompts, resource subscriptions, sampling, and list-change notifications are negotiated rather than universally guaranteed. | Inspect the initialization result and feature capabilities before using optional methods, then degrade gracefully when a capability is absent. |
| Deploying remote MCP servers without ordinary API controls. | Streamable HTTP servers are network services, so unauthenticated endpoints, weak origin handling, and unbounded requests can become security incidents. | Require authentication, validate origins, use TLS, bind local servers to loopback, enforce rate limits, and log protocol and domain decisions. |

## Knowledge Check

<details>
<summary>1. Your team has four AI hosts and ten backend systems. What architectural problem appears if every host integrates directly with every system, and how does MCP change the shape of that problem?</summary>

Direct integration creates a growing adapter matrix where each host-system pair may need its own schema mapping, authentication handling, retry behavior, and operational tests. MCP changes the shape by moving each backend integration behind a server that speaks a shared protocol. Hosts still need MCP clients and policy, but the backend owner can publish one server contract instead of bespoke code for every host.

</details>

<details>
<summary>2. A server exposes `restart_deployment` as a resource named `cluster://restart/payments`. Why is this a bad MCP design even if the URI is easy for the model to understand?</summary>

The design violates the semantic boundary between reads and actions. Resources should provide context without side effects, while restarting a deployment changes production state and should be a tool with explicit arguments, authorization, approval, audit logging, and retry semantics. Hiding the action behind a resource risks prefetching, accidental invocation, and misleading user interfaces.

</details>

<details>
<summary>3. During local testing, your client fails with a JSON parse error before `initialize` completes. The server works when you run it manually. What is the first stdio-specific bug you should check?</summary>

Check whether the server writes human-readable text to stdout before or during protocol handling. In stdio transport, stdout must contain only valid JSON-RPC messages, while logs should go to stderr. A banner, debug print, progress line, or stack trace on stdout can make the client parse ordinary text as JSON and fail before the protocol lifecycle begins.

</details>

<details>
<summary>4. Why is the `initialize` exchange more than a handshake formality?</summary>

The exchange establishes protocol version compatibility and negotiated capabilities before normal operation begins. Without it, a client might call methods or rely on optional features the server does not support, or a server might respond according to a revision the client cannot parse. The initialized lifecycle gives both sides a concrete compatibility contract.

</details>

<details>
<summary>5. A native OpenAI function tool and an MCP tool both use JSON schemas. What is the most important architectural difference between them?</summary>

The native function tool is part of one model-provider conversation interface, where the application gives schemas to the model and executes local callbacks. An MCP tool is advertised by a server through a reusable protocol connection, so multiple hosts or frameworks can discover and invoke it without copying the backend integration. A host may translate MCP tools into provider-native tool schemas, but the server remains the reusable connector boundary.

</details>

<details>
<summary>6. A remote MCP server executes a write operation, but the HTTP connection drops before the client receives the response. What production design issue does this reveal?</summary>

It reveals that side-effecting tools need distributed-systems safeguards, not just JSON schemas. The server and client need timeouts, idempotency keys or request IDs, status-check operations, and clear retry policy so a duplicate request does not perform the same write twice. The host should surface uncertainty rather than pretending the failed response proves the backend action did not happen.

</details>

## Hands-On Exercise

The goal of this exercise is to run the minimal stdio server and client from the module, inspect the protocol transcript, and then make one intentional policy change. Use the repository virtual environment for commands so the examples stay consistent with this project's local tooling.

- [ ] Create `mcp_policy_server.py` from the server example above, then run `.venv/bin/python -m py_compile mcp_policy_server.py` to confirm the server code has valid Python syntax before launching it.

- [ ] Create `mcp_policy_client.py` from the client example above, then run `.venv/bin/python -m py_compile mcp_policy_client.py` to confirm the client code has valid Python syntax before testing the transport.

- [ ] Run `.venv/bin/python mcp_policy_client.py` from the directory containing both files, then confirm the output shows `initialize`, `tools/list`, `resources/read`, `prompts/get`, and `tools/call` responses in that order.

- [ ] Inspect the `tools/call` response and verify that the production deployment with two replicas is blocked by policy while still returning a normal JSON-RPC result rather than a protocol-level parse failure.

- [ ] Change the client arguments to use three production replicas and an owner label, run `.venv/bin/python mcp_policy_client.py` again, and confirm the structured content reports that the request is allowed.

- [ ] Add a temporary `print("debug")` line to the server before it writes a response, run the client once to observe the stdio parsing failure, then remove the line and explain why logs must use stderr instead.

Success criteria: you can explain each JSON-RPC method in the transcript, identify which responses are discovery versus execution, describe why the blocked deployment is a domain result rather than a protocol error, and name at least three production controls you would add before exposing a write-capable MCP server to real agents.

## Next Module

Continue with [Module 1.9: Computer Use and Browser Automation Agents](/ai-ml-engineering/frameworks-agents/module-1.9-computer-use-agents/), where the agent integration problem moves from structured tool calls into browser and desktop environments with stronger observation and safety requirements.

## Sources

- [Model Context Protocol specification](https://modelcontextprotocol.io/specification) - Authoritative specification entry point for the current MCP protocol revision, including the overview, security principles, feature lists, and links into the detailed protocol pages.
- [MCP architecture overview](https://modelcontextprotocol.io/docs/learn/architecture) - Explains the host, client, and server roles, the data and transport layers, and the protocol's scope without tying the explanation to one SDK.
- [MCP lifecycle specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle) - Defines initialization, version negotiation, capability negotiation, operation, shutdown, timeouts, and error handling for client-server connections.
- [MCP transports specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) - Documents stdio, Streamable HTTP, message framing, protocol-version headers, session handling, and transport-specific security requirements.
- [MCP tools specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) - Defines model-controlled tools, discovery, invocation, results, schemas, security considerations, and why human review remains important for tool use.
- [MCP resources specification](https://modelcontextprotocol.io/specification/2025-11-25/server/resources) - Covers readable context resources, resource URIs, list and read operations, templates, subscriptions, and resource security considerations.
- [MCP prompts specification](https://modelcontextprotocol.io/specification/2025-11-25/server/prompts) - Describes server-provided prompt templates, prompt discovery, argument handling, message content, and prompt-specific injection concerns.
- [MCP sampling specification](https://modelcontextprotocol.io/specification/2025-11-25/client/sampling) - Explains server-initiated model sampling through the client, including model access control, tool-enabled sampling, and human-in-the-loop expectations.
- [MCP authorization specification](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) - Provides the protocol's HTTP authorization model, useful when designing remote MCP servers with delegated identity and protected resources.
- [JSON-RPC 2.0 specification](https://www.jsonrpc.org/specification) - Defines the request, response, notification, error, batch, and ID-correlation semantics that MCP uses for its data-layer message envelope.
- [MCP Python SDK repository](https://github.com/modelcontextprotocol/python-sdk) - Official Python SDK repository for developers who want production client or server implementations rather than hand-written educational message loops.
- [MCP TypeScript SDK repository](https://github.com/modelcontextprotocol/typescript-sdk) - Official TypeScript SDK repository for JavaScript and TypeScript hosts or servers that need maintained transport and protocol abstractions.
- [Anthropic announcement of MCP](https://www.anthropic.com/news/model-context-protocol) - Original public announcement describing MCP's purpose as an open standard for connecting AI assistants to systems where data lives.
- [OpenAI function calling guide](https://platform.openai.com/docs/guides/function-calling?api-mode=chat) - Official OpenAI documentation for native function or tool calling, useful for comparing provider-level tools with MCP connector servers.
- [OpenAI Agents SDK MCP documentation](https://openai.github.io/openai-agents-python/mcp/) - Official OpenAI Agents SDK documentation showing how an agent framework can consume MCP servers through framework-specific abstractions.
