# Knowledge Base

Collect literature and experiment files, review extracted data, and publish
knowledge with evidence. Each card stores its collection in a managed SQLite
file; no separate database server is needed.

## Install

Install the Pack through Library/Store and follow its dependency plan. In a source
checkout, run `scripts/install-plugins.py plugins/knowledge_base` with OAW's
prepared backend interpreter and the intended `--profile`. Dependencies are
owned by the Pack declaration in [oaw.pack.toml](oaw.pack.toml); discovery does
not install them. See [source setup](../../docs/developers/setup.md).

## First collection

1. Open **Knowledge base** in the Library, collect its card and place it. Or use
   **Lab Manager** from the Legion deck for a preconnected Agent and Conversation.
2. Open **Literature → Sources**, import a document and convert it to Markdown.
3. Search the converted text, or select sources to create a knowledge draft.
4. Configure a model or connect the Lab assistant for extraction. Review the
   evidence and edit the draft before publishing it.

For experiments, import an experiment's files as an upload, choose a record schema,
extract and review records, then publish approved data. Insights are separately
reviewed and published. Neither raw uploads nor model drafts silently become
approved knowledge. The graph is optional for search and record workflows.

## Continue

- [Literature, experiments, Lab Manager and deployment](docs/workflows.md).
- [Agent tools, model calls and persistence](docs/agent-contract.md).
- [Standalone HTTP service, MCP server and CLI](docs/standalone.md).

Source and draft data, model settings and deployment permissions have distinct
owners. Follow the contracts above when extending the card; do not bypass graph
permissions or publish a draft merely because extraction completed.

## Install the engines

See [the maintained guide](../../docs/developers/setup.md).

## The Lab Manager formation

See [the maintained guide](docs/workflows.md#the-lab-manager-formation).

## Using the card

See [the maintained guide](docs/workflows.md#using-the-card).

## Where the model call happens

See [the maintained guide](docs/agent-contract.md#where-the-model-call-happens).

## Deploying it as a locked application

See [the maintained guide](docs/workflows.md#deploying-it-as-a-locked-application).

## Running it without OAW

See [the maintained guide](docs/standalone.md#running-it-without-oaw).

## Tests

See [the maintained guide](docs/standalone.md#tests).

## Agent connections

See [the maintained guide](docs/agent-contract.md#agent-connections).

## Persistence and failure behavior

See [the maintained guide](docs/agent-contract.md#persistence-and-failure-behavior).
