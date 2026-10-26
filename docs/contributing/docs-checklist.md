# Documentation checklist

[简体中文](docs-checklist.zh-CN.md)

1. Choose one reader and one task. Put steps in a guide, exact contracts in
   reference, and host operation in the maintainer path.
2. Verify product facts against current code, tests and examples. Use visible UI
   labels. Mark experimental features and distinguish dev from released builds.
3. State prerequisites, commands, expected results and the next useful step.
   Prefer one complete example over disconnected snippets.
4. Link the authoritative explanation instead of repeating it. Preserve useful
   old paths and anchors when moving content. Use repository-relative links
   with exact filename case; do not link ignored local outputs.
5. Keep English and Chinese facts consistent. English pages use `.md`, Chinese
   pages `.zh-CN.md`; translating every low-level reference is optional, but
   both languages need a complete user and developer entry path.
6. Register pages in the same reader group in `mkdocs.yml` and
   `frontend/src/shell/documentation.ts`. Run the [documentation checks](../developers/documentation.md).

Do not put dated test counts, PR summaries, migration diaries or future roadmaps
in maintained instructions. Keep only historical evidence with continuing value
in `docs/internal/`, explicitly non-authoritative; otherwise rely on Git history.
