# Maintain the documentation

Follow the [writing checklist](../contributing/docs-checklist.md). The site and
in-app manual read the same Markdown under `docs/`; plugin READMEs document their
own packages. `docs/internal/` is excluded from both public readers.

## Preview and check

From the repository root, use a Python environment with:

```sh
python -m pip install -r scripts/docs-requirements.txt
python scripts/docs.py serve
python scripts/docs.py check
```

`check` validates the published inventory, headings/language, repository links,
strict MkDocs build, generated anchors and search output. It needs no backend.

After changing navigation, links or Help behavior, run from `frontend`:

```sh
npx vitest run src/shell/documentation.test.ts src/shell/DocumentationPanel.test.tsx src/shell/HelpMenu.test.tsx
npm run build
```

The existing browser scenario is `e2e/documentation.spec.ts`; it checks offline
reading, modal focus, images, language switching and small layouts. Use
`node scripts/run-e2e.mjs e2e/documentation.spec.ts` after preparing the test host.

## Navigation and links

List every public page once in `mkdocs.yml`. Place translations next to their
English page in the same audience group. Mirror that classification in
`frontend/src/shell/documentation.ts`; its test compares both group inventories.
There is no separate content copy or generated taxonomy.

Use relative Markdown links for pages and tracked source files. MkDocs sends
source links to GitHub `dev`; the in-app resolver keeps pages/assets local and
marks repository resources as online. New pages and assets are bundled at build
time, so a website edit does not update an already installed application's manual.

Keep stable old entry URLs when they have useful inbound links. A short pointer
is enough; do not keep a second tutorial. Never describe ignored local logs as
portable evidence.

## Publication

The docs workflow checks PRs and branch pushes. Pages publication on `dev` is
separate from validation and from desktop releases; inspect the workflow result
when checking whether a website update is live. This repository's site follows
dev, while release users should consult their bundled manual and release notes.
