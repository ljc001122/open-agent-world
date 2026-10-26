# Run Knowledge Base without OAW

[Pack guide](../README.md)

## Running it without OAW

The pipeline does not import OAW at all — only `plugin.py` and `lifecycle.py` do,
and neither is loaded outside the backend. So the same code runs as a small
service with an HTTP API, an MCP server for an agent harness, and a `kb` CLI:

```sh
python -m venv .venv && .venv/bin/pip install -e 'plugins/knowledge_base[service]'
```

A **store** is a directory holding one `knowledge.db` plus a small settings file;
it defaults to `$KB_SERVICE_STORE`, else `~/.local/share/oaw-knowledge`. One store
can hold many **collections**, named per call (`--collection`, or the URL path) —
this is the same unit the OAW card calls a collection, and each one can in turn hold
several **groups** (`kb groups`), the same source-organizing unit the card's group
selector manages. A file belongs to exactly one group; a fresh collection starts
with a single unnamed default group, so nothing about groups is required to use
the store the way earlier versions did.

The whole loop in a terminal, no browser and no backend:

```sh
export KB_SERVICE_STORE=~/kb
kb ingest paper.pdf                       # uploads it; conversion is a separate step
kb process                                # converts every unconverted source, in a batch
kb sources                                # source id, record id, engine used
kb knowledge open --source SOURCE_ID      # a draft over one or more converted sources
kb knowledge extract DRAFT_ID             # your model, your credentials: one call per source (no chunking or review offline)
kb knowledge show DRAFT_ID                # the concepts and relations, each with its sources
kb knowledge publish DRAFT_ID             # the only command that writes the literature layer
kb graph --layer literature
```

Records read out of sources with a schema of your own are the other family:

```sh
kb schema add --file conductivity-schema.json   # name, definition, system_prompt
kb records extract --schema SCHEMA_ID --source SOURCE_ID [--replace]
kb records list --schema SCHEMA_ID
kb records publish RECORD_ID
```

`kb ingest` also accepts several files at once and, in process, waits for their
batch conversion the same way it always waited for one — pass `--group GROUP_ID`
to file them into a named group instead of the default one, and `kb groups create
--name Alloys` to make one first.

`kb tools` prints the agent manifest; `kb --help` lists the rest (`jobs --watch`,
`markdown --out`, `knowledge unpublish|delete`, `records show|unpublish|delete`,
`settings`, `groups`, `process`). Insights have their own family:

```sh
kb insights stats [--schema ID ...]               # the statistics, no model involved; no --schema:
                                                  # every experiment schema (--schema-kind literature for
                                                  # the Records tab's), with cross-schema stats
kb insights extract [--schema ID ...] [--replace]  # your model proposes draft insights over that scope
kb insights list [--schema ID] [--kind anomaly] [--status draft] [--query moisture]
kb insights publish INSIGHT_ID [...]              # writes the graph's experiment layer
kb insights unpublish INSIGHT_ID                  # removes exactly what publish wrote
kb graph --layer experiment                       # or --layer literature
```

### As a service

```sh
export KB_SERVICE_TOKEN=$(openssl rand -hex 16)
kb serve --store ~/kb            # 127.0.0.1:8931
curl -H "Authorization: Bearer $KB_SERVICE_TOKEN" \
     -d '{}' http://127.0.0.1:8931/v1/collections/default/overview
```

`POST /v1/collections/{collection}/{operation}` takes the action's arguments as the
body, for every operation the card has, because both read one table. `GET /v1/tools`
returns the manifest and `GET /v1/health` is the only unauthenticated route.
Binding anything other than loopback without a token is refused.

**Writing the graph is not reachable over the network.** `knowledge_review`, `knowledge_graph_audit_apply` and
`insight_review` with `operation=publish` return 403 unless `KB_ADMIN_TOKEN` is set
on the service *and* presented, and even then the first call returns
`confirmation_required` until the request repeats with `?confirm=true`. Out of the
box, publishing a knowledge draft or an insight happens on the canvas or at the
host's own terminal — nowhere else.

Point the CLI at a running service with `--service URL` (or `KB_SERVICE_URL`) and
it proxies instead of opening the store itself.

### For an agent harness (MCP)

```jsonc
{"command": "kb", "args": ["mcp", "--store", "/home/you/kb", "--collection", "default"]}
```

The server exposes the shared operation table's agent tools on stdio, including
selected-source processing, schema management, draft opening and upload preparation.
Raw file bodies, broad management actions and publication are not tools.
`knowledge_import_artifact` is OAW-only: it requires the host's independently
authorized Conversation/Artifact reference. OAW also adds bounded `wait_seconds`
to `knowledge_jobs`; standalone callers can poll jobs after ingesting through CLI/HTTP.

### The two modes coexist — one writer per store

A card and a service are separate stores by default: the card's store is its node
storage directory inside the OAW profile, the service's is `--store`. Both may run
at once.

What must not happen is **two processes writing one store**: each opens MKB's job
thread, and two of them race the same job rows in one SQLite file. `kb serve`
writes `.kb-service.lock` (pid, url) into the store; an in-process `kb` command on
a locked store refuses and prints the `--service` URL to use instead. The lock is
removed on shutdown and ignored if its pid is gone.

## Tests

```sh
cd plugins/knowledge_base && pytest    # pipeline, service and the layering guard
```

That suite needs no OAW on the path — `test_layering.py` asserts as much by
importing the core in a clean interpreter and failing if `open_agent_world` or
`backend` appears in `sys.modules`. The host seam (registration, the error
conversion, create/delete) is covered by
`backend/tests/test_knowledge_base_plugin.py`.
