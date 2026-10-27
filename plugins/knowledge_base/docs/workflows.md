# Knowledge Base workflows

[Pack guide](../README.md)

## The Lab Manager formation

The card is most useful with someone to ask about it. The plugin registers a Legion
preset, **Lab Manager**, in the Legion deck: deploying it places a knowledge
base, a **Lab assistant** Agent and a Conversation, already wired and already laid out —
the card on one side with a rail for its two workflows, **Literature** and
**Experiment**, and the conversation beside it.

**Ask the Lab assistant to work with your files.** The formation uses **Knowledge
research**: attach a PDF, text file, spreadsheet or supported image in the
Conversation and ask for reading, comparison or extraction. The assistant imports
the authorized attachment and starts conversion, follows the job, then reads and
cites its contents. No Sandbox or second upload through Sources is required.
Reading and document search do not require schemas, a graph or publication.

For structured work the assistant can prepare a schema, an experiment upload or a
knowledge draft, extract the requested records or concepts, and review drafts.
It can also inspect and query a separately connected database through that card's
own tools and read permission. It never receives arbitrary database/file access.
You still review and publish records, knowledge and insights. Model settings and
destructive management remain outside the assistant's tools. The narrower
**Knowledge read**, **Knowledge extract** and **Knowledge experiment** relationships
retain their existing scopes for assistants that need less access.

Saving your own knowledge Legion works too, but note what a copy is: the node type is
templateable while the database is not captured, so **a deployed copy is an empty
knowledge base** with the same name and wiring — no sources, no groups, no graph,
and settings back at their defaults. This is the same promise the card's deletion warning
makes.

## Using the card

Open the **Knowledge base** pack in the card library, place a card, then open its
workspace. The card's own rail switches between its two workflows; each workflow
keeps its own tab strip of sections, so only what belongs to the workflow you are in
ever shows.

### Literature

1. **Sources** — organize documents into **groups** (create, rename or delete one
   from **Manage groups** beside the group selector), then add PDF,
   markdown, text, CSV, TSV, Excel (`.xlsx`), image or JSON files up to 32 MiB each.
   Drop files onto the source area or choose **Add documents**. Each uploaded file
   starts conversion automatically; the source row shows its status and offers
   **Retry** after a failure. Existing pending files can still be processed alone
   or in a batch. Detailed conversion jobs are available below the source list.
   Ready documents offer **Read documents**, **Build knowledge**, and **Extract
   records**; reading does not require a schema or a published graph. Sources also holds full-text
   **search** over every already-converted document — ranked, each result carrying
   the source filename and the heading it falls under, and a click jumps straight
   to that source. Click a converted source to read its formatted document (a
   real table for spreadsheets, a model's transcription for images). **Markdown**
   switches to the raw text.
2. **Knowledge** — the concept graph of your literature, with no schema to write.
   **New draft** picks one or more converted sources and opens a **knowledge
   draft** over them. A draft is an extraction task over a chosen set of documents;
   selecting sources does not run extraction or copy the documents. **Build knowledge**
   in Sources continues your current work. Explicitly checked sources open a matching
   saved draft, or a creation form for exactly those sources. Opening the same source
   set and title reuses its draft. Tab changes retain the form, selected draft and run;
   the host's transient card/session state also restores your place after closing the workspace.
   The draft's **Extract → Review → Publish** stages show actual source and review
   progress, with the current action beside it. Review and publication unlock once
   the draft contains concepts; the primary **Extract** button starts that work.
   **Extract** reads each source a few sections at a time —
   through a connected Agent holding **Knowledge extract** when there is one, else
   one model call per chunk of sections (a short document is one call) — and names
   the concepts it is about and the relations it states between them. Nodes are
   **concepts only** (a material, a phenomenon, a method, a property — never a bare
   value or a figure number), each with **aliases** for its other spellings; a
   relation is a statement as first-class as a concept: a **free predicate** in
   the active voice (`improves`, `caused_by`, `measured_by` …, normalised to
   snake_case), a one-sentence **statement** of what the document claims about the
   pair, with the values and conditions that matter, MKB's **evidence level** (1
   causal … 4 inferred) and the **snippet** that states it. Predicates that only
   say a link exists (`related_to`, `associated_with` …) are flagged by the review,
   which gives each such relation the specific verb its statement supports. Concepts are keyed by
   name, so a concept two papers both name becomes one node with both as evidence;
   before each chunk the model is handed the names and predicates already in the
   draft and the published concepts the text mentions, so it reuses them. **Review
   draft** then has a model — the Agent, or one call — go over the draft against
   findings the card computes (predicate frequencies, look-alike names, isolated
   concepts, pairs related both ways, contradicting predicates, names the published
   graph already uses) and propose typed operations: merge concepts (the dropped
   names become aliases), rename a predicate, add an alias, delete a relation or a
   metadata-only concept, or flag something for you. They are applied to the draft
   at once and listed in its **review log**; `set_predicate` retypes one relation
   from its statement. **Edit** the concept and relation
   tables (rename, alias, change a predicate or evidence level, remove, add), then
   **Publish** — after an explicit confirmation, the **only** thing that writes
   the graph's literature layer. Below the drafts, **Review graph** runs the same
   review over the whole published layer: the model's proposed operations are
   shown first and, once you confirm, applied to every published draft that
   asserts the affected elements, after which the layer is rebuilt from the
   drafts — so what the graph holds is always exactly what its drafts assert.
   **Unpublish** removes exactly what the draft wrote, except elements another
   published draft also asserts. The published layer is drawn as a map below:
   click a concept to read its description, aliases, sources and relations;
   switch the side list to **Relations** (or click a relation line in a concept's
   panel) to read a relation on the same footing — its statement, predicate,
   evidence level, snippet, sources and both endpoints; double-click a concept to
   traverse outward. **Replace** empties a draft and reads every source again.
3. **Records** — structured data read out of sources with a schema of your own.
   **Schemas** here are **literature**-kind (the Experiment workflow has its own);
   a schema is a JSON Schema object plus the system prompt that explains it — e.g.
   one record per solid electrolyte, with its ionic conductivity and the
   temperature it was measured at. Pick a schema, select converted sources and
   **Extract**: one model call (or Agent run) per source produces zero or more
   draft records, each validated against the schema and linked to the source it
   came from. Rows unfold to a table; a draft edits in place as a form or JSON;
   **Publish** marks it approved data. **Insights** at the bottom of the tab are
   the same meta-knowledge extraction the Experiment workflow has, scoped to the
   literature schemas: statistics the card computes over the published records,
   draft insights a model proposes, and publication into the graph's experiment
   layer.

### Experiment

1. **Experiments** — drop files onto the strip under the toolbar (or **Choose
   files**): a photographed handwritten table, an Excel sheet, a PDF, a note. One
   experiment's files become one **upload**, created on the spot and named after
   its files; each file converts to markdown as soon as it lands (images through
   the vision engine). Uploads line up as chips below the strip; pick one to see
   its files, drop or **Add files** onto it, or edit its details — the strip's
   **New upload from files** starts another upload instead. Once every file is converted, **Extract
   records** opens a window to confirm the upload's name, description (units, which
   specimen a photo shows) and **experiment**-kind schema (choose one in the window,
   or **New schema** first: one JSON Schema object describes one specimen record;
   the schema is fixed once the upload has records). Confirming reads the whole
   upload as one document, projects it onto the schema and saves one draft record
   per specimen, each linked to the files it was read from — by starting the
   connected Lab assistant when one is connected, or else with one model call
   through the selected model. The records list below as folded rows; the toolbar's
   schema filter (or **All schemas**), the upload chips, a status filter and a
   search box (over names, values, file names and notes) narrow them, and a toggle
   shows the same records as a table with one column per schema field. Unfold a
   record to read its data as a table (nested lists and objects as sub-tables,
   missing required fields flagged), then **Edit** it in a form generated from the
   schema (typed inputs per field, a **JSON** toggle for the raw data) or ask the
   Lab assistant to in the conversation, and **Publish** — after an explicit
   confirmation — to mark it approved data. **Re-extract** offers to replace an
   upload's drafts and leaves its published records alone; **Unpublish** reopens a
   record; **Remove upload** deletes its records and keeps its files out of
   Literature. An experiment record never touches a draft, a review or the
   published graph.
2. **Insights** — the toolbar's schema selector sets the **scope**: one experiment
   schema, or **All schemas (cross-schema)** — every experiment schema that has
   published records, read together. The scope's **published** records (optionally
   one group's) are read as one table per schema together with **Statistics** the
   card computes over them — per schema and numeric field the count, mean, std,
   min, median and max, outliers beyond |z| > 2.5 (click one to open the record),
   pairwise correlations with |r| ≥ 0.6, value counts for categorical fields; and,
   across schemas, how many specimens appear in more than one schema (records
   matched by name — the sample id) and the correlations between fields of
   *different* schemas over them, so "crystallinity rises with sintering
   temperature" can be seen even when synthesis and XRD live in separate schemas.
   **Extract insights** hands all of that to the connected Lab assistant (or makes
   one model call) and saves what comes back as **draft insights**: each has a kind
   — `anomaly`, `rule`, `trend`, `correlation`, `threshold` or `note` — a title, a
   statement, the fields it is about (`<schema name>.<field>` when it spans
   schemas), an optional confidence and its **evidence**: the records it rests on,
   each with a role (supports, contradicts, observed_in), shown as chips that jump
   to the record. An insight is listed under every schema it involves.
   A kind filter narrows both lists. **Edit** a draft (or ask the Lab assistant to),
   **Delete** it, **Publish** it after an explicit confirmation — or **Publish all**
   under one — and it becomes part of the knowledge graph's **experiment layer**:
   one node per insight (typed by its kind), one `field` node per field it involves,
   one `experiment_record` node per record it cites, and `involves`, `supported_by`,
   `contradicted_by` and `observed_in` edges between them. Published insights are
   drawn as a map below, click one to read its statement and evidence; **Unpublish**
   removes exactly what publishing wrote and drops record and field nodes nothing
   cites any more. A draft whose cited record was since unpublished is marked
   *unpublished* on the chip and cannot be published until its evidence is fixed.
   Re-extracting with **Replace this schema's draft insights** replaces the drafts
   and never a published insight.
3. **Schemas** — the same schema list as Literature's, so an experiment-kind
   schema created here shows up there too, and back.

   A worked example lives in [`examples/solid_electrolyte/`](../examples/solid_electrolyte):
   `schema.json` (a solid-electrolyte production batch: feedstock, yield,
   conductivities, moisture, XRD, particle size) and a simulated
   `production_log_2026-07.txt` to upload and extract.

The group selector — in Sources, or the toolbar for other sections — narrows every
section to one group at a time, or shows everything across every group. A source
belongs to exactly one group for its whole life; markdown, knowledge drafts,
records, experiment uploads and the entities and relations a draft publishes all
trace back to the group their source came from, so a knowledge base with several
document sets stays as easy to browse group by group as it is to see as a whole. A
file uploaded into an experiment upload stays in the Experiment workflow: Literature's
source list leaves it out (`sources` with `workflow="experiment"` or `"all"` lists it).

Model output is never presented as fact. A draft of any kind is a candidate; a
published record is a person's checked judgment, not a graph element; a published
insight is a person's checked statement *about* records, in the graph's experiment
layer and traceable to every record it cites; a published knowledge draft is what
the literature layer holds, and every entity and relation in it carries the
`source_ids` it was read from.

## Deploying it as a locked application

The card declares a `NodeDeploymentDefinition` (Plugin API 1.21+, see
[plugin deployment](../../../docs/plugin-deployment.md)), so a saved Lab Manager
Legion can be [published](../../../docs/deployment.md) as a locked, password-protected
application the same way a Conversation or a Text card can. Every business action a
person uses to drive the pipeline publishes: upload, convert (alone or batched),
organize sources into groups, search, open a knowledge draft and extract, edit,
publish or unpublish it, read records out of sources with a schema, create an
experiment upload and add its files, review, publish or unpublish records, and
extract and publish insights over them — publishing a knowledge draft and
publishing an insight are still the only things that write the graph. The **Settings**
section never publishes: the collection name, PDF engine and MinerU URL stay
engineering-only and the section does not even mount in a deployed release,
regardless of whether its pane stays visible in the published layout.

A deployment mounts no live model picker (`docs/deployment.md`: "it does not mount
... model settings"), so every **Extract** button there uses one model chosen ahead
of time: set **Default model for deployment** in the engineering Settings section
before publishing. `POST /api/knowledge/{card_id}/knowledge`, `.../records`,
`.../extract` and `.../insights` are engineering-only routes; a deployment reaches
the same underlying calls through `POST
/api/runtime-app/workspace/knowledge/{card_id}/knowledge`, `.../records`,
`.../extract` and `.../insights` instead, each gated on the release granting both
halves of the pipeline it drives. A release carries no agent edges, so extraction
there is always the one-call path.

See [`examples/knowledge-legion-deploy`](../../../examples/knowledge-legion-deploy/README.md)
for a runnable end-to-end example — it also installs this plugin and its declared
dependencies into `backend/.venv` if they are missing
before publishing and serving a release.
