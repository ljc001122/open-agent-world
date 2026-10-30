# Office Skills 0.1.0 validation

Date: 2026-10-30 (Asia/Shanghai).

The independent Schema 3 distribution is `oaw.office@0.1.0`. Its adapter uses only
the public OAW SDK and standard library. Document engines are declared as managed,
on-use Sandbox environments. The Pack includes three Skill documents, reusable
helpers, a custom-Python entrypoint per Skill and an Office Workbench preset.

## Executed checks

- `plugins/office/tests/test_helpers.py`: **8 passed**, using real python-docx
  1.2.0, openpyxl 3.1.5 and python-pptx 1.0.2 in a separate validation venv.
  Covered real DOCX/XLSX/PPTX create/read/edit round trips, Chinese output, original
  preservation, formula caches and formulas, windows, notes, custom scripts with
  literal arguments, overwrite/traversal refusal and invalid/oversized input.
- `backend/tests/test_office_pack.py`: **2 passed**. Covered formation creation,
  progressive reading, dependency binding and live Skill access revocation through
  the real capability provider with the repository's fake Windows native API.
- Existing `test_skill_packages.py`, `test_skill_runtime.py` and
  `test_sandbox_pack_profiles.py`: **89 passed, 1 skipped** overall. Four profile
  subprocess cases initially hit Windows path-length errors in a long temporary
  path; those four passed unchanged with `--basetemp .tmp/op`. The skipped case is
  the existing opt-in real native Skill isolation test.
- Skill Creator's `quick_validate.py`: all three SKILL.md files passed.
- `open_agent_world.pack doctor`, adapter wheel build and `build-project` passed.
- The resulting archive installed into a fresh disposable OAW profile. A registry
  with source discovery and third-party entrypoints excluded loaded the installed
  Pack and instantiated its Office Workbench through the local management API.

## Evidence boundaries

The real-engine tests execute in an isolated validation venv, not an OAW native
Sandbox. The capability integration uses the existing fake native API. An attempt
to enable networking for a real Windows Sandbox was rejected because the local
Windows network-policy broker was unavailable. Therefore native Sandbox package
preparation and complete model-driven attachment-to-result execution remain
**Not Verified**. No broker, firewall policy or production application was changed.

This release contains no document renderer or formula recalculation engine.
Structural reopen, text inspection and formula preservation do not establish visual
fidelity, complete embedded-object extraction or current formula results. Browser UI,
installed desktop and macOS/Linux native execution were not exercised by these checks.

## Reproduction

Run helper tests in an environment with pytest and the three declared Office engine
dependencies, using `python -m pytest plugins/office/tests/test_helpers.py`.
Run the backend integration with the existing backend test environment. On Windows,
use a short, disposable `--basetemp` for profile subprocess tests and `--tb=short`.

Build the adapter wheel from `plugins/office`, then run:

```sh
python -m open_agent_world.pack build-project plugins/office \
  .outputs/office-release/oaw.office-0.1.0.oawpack \
  --backend-wheel .outputs/office-release/oaw_office-0.1.0-py3-none-any.whl
```
