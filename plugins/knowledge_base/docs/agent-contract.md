# Knowledge Base Agent and persistence contract

[Pack guide](../README.md)

## Where the model call happens

Every extraction needs a configured model, and plugins never see API credentials.
Each Extract button therefore either starts a connected Agent that does the work
through the plugin's own tools, or posts to a small bridge route in the OAW backend
that reads the prompt from the card, resolves the model connection, calls the
provider and writes the result back through the card's own save action. Provider
response bodies are never returned to the browser — they can carry request
credentials — and the card never writes an extraction result itself.

**Extract knowledge** is `knowledge_source_outline` → (`knowledge_lookup` →
`knowledge_extract_prompt` → `knowledge_save`) per section or group of sections,
for each source of the draft — a port of MKB's agent workflow (list headings, read a
section, search the existing graph, save incrementally) as plugin tools. The outline
returns each section as a character window; the prompt takes `section` (or
`heading`) and carries the instruction and suggested predicates
(`knowledge_prompt.py`), the names and predicates already in the draft, the published
concepts the text mentions, and that section's markdown; the save normalises the
reply — predicates to snake_case, endpoints that name nothing dropped, aliases
unioned — and merges it into the draft by content-keyed id (`concept:<slug>`,
`<source>|<predicate>|<target>`). With an Agent holding **Knowledge extract**
connected, the card starts it with a `KNOWLEDGE EXTRACTION REQUEST`; without one,
`POST /api/knowledge/{card_id}/knowledge` reads the outline, groups consecutive
sections into ~40k-character chunks and makes one call per chunk in the backend.
**Review draft** is `knowledge_audit_prompt` → `knowledge_audit_apply`
(`knowledge_audit.py`): the prompt carries the findings the card computes and the
draft; the apply takes typed operations (`merge_concepts`, `rename_predicate`,
`add_alias`, `delete_relation`, `delete_concept`, `set_evidence`, `flag`), applies
them through the same normalisation and appends them to the draft's `review_log`
(`set_predicate` retypes one relation and may correct its statement).
The bridge route is `POST /api/knowledge/{card_id}/audit`; an Agent can read a
source section before deciding on a merge. On the engineering canvas the three
knowledge bridge routes stream NDJSON — one `progress` line per section chunk or
review stage, then a `done` or `error` line — which the card shows as a progress
bar; the deployment routes return plain JSON. **Review graph** is
`knowledge_graph_audit_prompt` → `POST /api/knowledge/{card_id}/graph-audit`
(proposes only) → `knowledge_graph_audit_apply`, which asks for confirmation like
publishing does, applies the operations to every published draft in scope, and
rebuilds the literature layer from all published drafts; neither action has a tool
name, as rewriting published knowledge is a person's decision. `knowledge_update` is how a connected
agent edits a draft when asked to; `knowledge_draft_manage` (open, retitle, delete)
and `knowledge_review` (publish, unpublish) have no tool name on any transport.
Research agents open or reuse an unpublished draft with the separate
`knowledge_draft_open` tool, which does not expose deletion or publication.
Publishing a concept another published draft already wrote unions its aliases and
sources with the node's. Databases from before this model are re-keyed once on open
(`knowledge_migration.py`): typed nodes with one name collapse onto one concept, and
old relation types become predicates.

**Extract records** from literature is `record_extract_prompt` → `record_save`, once
per selected source: the schema, the instruction and the source's markdown in; zero
or more records out, each validated against the schema and linked to that source.
The bridge route is `POST /api/knowledge/{card_id}/records`; the Agent path uses the
same two tools (`knowledge_record_extract_prompt`, `knowledge_record_save`).

**Extract records** from an experiment upload has the same two paths over its own two
actions.**Extract insights** is the same shape a third time. `insight_prompt` takes a
scope — one `schema_id`, several `schema_ids`, or neither for every experiment
schema with published records — and returns each schema with its statistics, the
cross-schema statistics, the insights already published, and the records as one
markdown table per schema with a `record_id` column (windowed); `insight_save`
takes the same scope and stores the insights produced, refusing any whose evidence
is not a published record of those schemas in that group. With a Lab assistant
connected the card starts it with an `INSIGHT EXTRACTION REQUEST`; without one,
`POST /api/knowledge/{card_id}/insights` makes one JSON-mode call and writes back
through `insight_save`. Publishing — `insight_review` — is the one write to the graph
from insights, and it has no tool name on any transport. The scope's open form
takes every schema of one `schema_kind` (experiment by default; the Records tab
passes `literature`), so each section's insights stay over its own records.

Outside OAW, `kb knowledge extract`, `kb records extract` and `kb insights extract`
are the other callers of those same prompt builders, using a model from your own
shell (`KB_MODEL_BASE_URL`, `KB_MODEL_API_KEY`, `KB_MODEL`). The standalone service
never holds model credentials and never calls a provider.

## Agent connections

| Relationship | Tools and permissions |
| --- | --- |
| Knowledge read | `knowledge_overview`, `knowledge_sources`, `knowledge_markdown`, `knowledge_document_search`, `knowledge_schemas`, `knowledge_drafts`, `knowledge_source_outline`, `knowledge_lookup`, `knowledge_experiments`, `knowledge_experiment_bundles`, `knowledge_insights`, `knowledge_graph`, `knowledge_jobs` |
| Knowledge extract | Read tools plus `knowledge_extract_prompt`, `knowledge_save`, `knowledge_update`, `knowledge_audit_prompt`, `knowledge_audit_apply`, `knowledge_record_extract_prompt`, `knowledge_record_save` |
| Knowledge experiment | Read tools plus `knowledge_experiment_extract_prompt`, `knowledge_experiment_save`, `knowledge_experiment_update`, `knowledge_insight_prompt`, `knowledge_insight_save`, `knowledge_insight_update` |
| Knowledge research | Both extraction paths plus `knowledge_import_artifact`, `knowledge_process`, `knowledge_schema_manage`, `knowledge_draft_open`, `knowledge_experiment_bundle_prepare` and `knowledge_graph_index_build` |

`knowledge_schemas` allows only list/get for agents. Schema writes require the
separate management capability; schemas used by published records cannot be
changed by an agent. `knowledge_graph_index` reports status; explicit index
building requires its own capability. The existing desktop actions stay compatible.

An import takes a live `source` selector, `version_id` and `path`, plus an optional
group or experiment upload. The host validates the source session, reference,
manifest, size and checksum; only then can the plugin retain the bytes. Both
source and destination permissions are rechecked before persistence. File bytes
never appear in the tool arguments or results. A repeated reference in the same
group/upload reuses its persisted source, including after restart. The result
includes the source, conversion job and `next_step`; poll `knowledge_jobs` with
`job_id` and `wait_seconds` (up to 30) to await completion without holding the
resource mutation lock. A failed conversion can resume through `knowledge_process`;
changing converter settings creates a separate attempt and retains failure history.

`knowledge_graph` answers "what does the base say about X (and Y)" and is the first
tool the Lab assistant calls for any question about the base. It has **one search
path**: whatever is passed — `query=<question>`, `names=[...]` (name, alias or acronym;
spacing and punctuation aside) or, from the UI and CLI, `name_contains` /
`relation_contains` — is searched the same way: by words (name and acronym match,
statement text) and, when the card has an embedding model, by meaning, fused with
reciprocal-rank fusion. The result holds the best-fitting concepts (`matched: true`),
the relations ranked best first — each readable as `source_name → predicate →
target_name` with its statement, evidence level and snippet (the relations are the
published claims; a concept's description is background) — and `connections`: the
shortest relation chains between any two concepts the question names.
`operation="connect"` with `names=[X, Y]` returns only those chains (`max_depth`,
default 3) or `connected: false`; `traverse` walks outward from an entity id. The
agent's tool schema exposes only `query` and `names`, so no lexical-only knob can be
picked by mistake; the graph map's name filter passes `semantic: false` and stays
lexical.

Meaning-based matching is on when the card's **Settings → Embedding model for graph
search** names an OpenAI-compatible embedding model (a connection from OAW's Models &
connections that serves `/embeddings`). Every search then reports `semantic: true`, or
`semantic: false` plus `semantic_error` when the model could not be used — the answer
is still the word-based one. Concept and relation vectors live in the card's SQLite
file (`oaw_kb_vectors`) and are brought up to date on each search (only changed
elements are embedded); **Settings → Semantic index** shows coverage and the last error
and can build the index up front, and `knowledge_graph_index` reports the same to the
assistant. A hit must stand out from the rest of the graph (two standard deviations
above the mean cosine) *and* clear an absolute floor (0.45, tuned on qwen3
text-embedding), so an unrelated question matches nothing. The graph text is sent to
the chosen endpoint. Empty means off, and a chat default model is never used for this.

The Lab assistant's instruction and connection are copied when the formation is
created. Existing formations keep their saved instructions and narrower grants;
updating the Pack does not silently broaden them or overwrite custom instructions.
To upgrade an existing assistant while preserving its KB and history, change its
connection to **Knowledge research** and replace its old stock instruction with
`INSTRUCTION` from `preset.py` (merge deliberately if it was customized). Do not
delete or recreate the Knowledge Base card to upgrade its assistant.

Uploading raw data (`ingest`, `experiment_ingest`), converting it (`process`),
managing groups (`groups`), knowledge drafts (`knowledge_draft_manage`) and
experiment uploads (`experiment_bundle_manage`), changing card settings
(`settings`) and publishing, unpublishing or deleting a knowledge draft
(`knowledge_review`), reviewing the published graph (`knowledge_graph_audit_prompt`,
`knowledge_graph_audit_apply`), a record (`experiment_review`) or an insight
(`insight_review`) have **no capability kind at all**, so no relationship can reach
them directly. The research connection instead grants the bounded import,
selected-source conversion, schema management, draft opening and upload preparation
operations described above. Publishing anything stays a human act performed on
the canvas. Agents
cannot pass desktop confirmation arguments. `knowledge_overview` still reports every
group by name and count, and every read tool accepts an optional `group_id` to
narrow its answer to one group, so the Lab assistant can talk about how the base is
organized without being able to reorganize it.

Every Agent connected by a Knowledge read, extract, experiment or research edge is listed under
**Connected agents** in the engineering Settings section, each with its own model
picker — the same catalog of connections configured on the canvas. This exists
because the Agent's own card is not part of this workspace's layout, so there would
otherwise be no way to change which model it answers with without leaving the
Lab Manager workspace to find that card on the canvas. Changing it here edits
the Agent's own `model` field directly (`updateCard`, exactly what its own card's
picker would do) — it changes what that Agent uses everywhere, not just in this one
conversation.

## Persistence and failure behavior

Each card owns `knowledge.db` under its node storage directory. Sources,
artifacts, markdown records, schemas, evidence, the integration outbox and the
knowledge graph itself all live in that one file — the graph in plugin-owned
`oaw_kg_entity` / `oaw_kg_relation` tables, so it survives a restart. The search
index (`oaw_kb_chunks_fts`, an FTS5 virtual table populated as each document
converts), knowledge drafts (`oaw_kb_knowledge_draft` /
`oaw_kb_knowledge_draft_source`), experiment uploads (`oaw_kb_experiment_bundle` /
`oaw_kb_experiment_bundle_source`), records from either side
(`oaw_kb_experiment_record` / `oaw_kb_experiment_record_source`; a literature
record has no `bundle_id`) and insights (`oaw_kb_insight` / `oaw_kb_insight_record`)
are plugin-owned tables in the same file too, alongside MKB's own schema, not a
second database. An insight table from before cross-schema insights existed is
rebuilt on first open so `schema_id` may be null and `schema_ids` lists every schema
an insight spans. The two graph tables carry a `layer` column — `literature` for
what a published knowledge draft wrote, `experiment` for a published insight and
the record and field nodes it cites — so one graph holds both and a query narrows
to either. Projections, MKB drafts and facts written by earlier versions stay in
the file untouched and unreachable; entities they published remain in the
`literature` layer and on the Knowledge map. A database from before uploads existed is migrated on first open: its
records gain the new columns, `confirmed` becomes `published`, and the old
projection-keyed evidence table is folded into the source-keyed one. The
file uses WAL and a 30-second busy timeout because the job thread and resource
actions write concurrently. Groups are plain MKB collections in the same file, so
they persist and restart exactly the same way; opening an older `knowledge.db` for
the first time after upgrading adds the `group_id` and `layer` columns those two
tables need automatically, leaving every existing element in place (tagged to no
group until the next publication touches it, and to the `literature` layer), and
backfills the search index for any record converted before it existed.

Deleting a card permanently removes `knowledge.db` and its WAL/SHM companions
through OAW's journaled lifecycle finalizer. Canvas undo, copy/paste and Legion
templates do not snapshot the file. Back up the profile while OAW is closed.

Uploads are capped at 32 MiB and results at 1 MiB, so long documents page through
`offset`/`limit` rather than arriving whole. Uploading a file only stores it —
processing is a separate, explicit batch step, alone or with others, so a large
drop of files never floods the job thread on its own (an experiment upload's files
are the exception: they only exist to be projected together, so each converts as it
lands). A conversion that no engine
can handle fails the job with the engine named, leaving the source in place to
retry after installing the engine. Interrupted jobs are recovered when the card
reopens.
