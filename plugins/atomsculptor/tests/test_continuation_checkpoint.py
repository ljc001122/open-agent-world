"""Cross-stage inline evidence and explicit native continuation, without model APIs."""
from copy import deepcopy
from types import SimpleNamespace
import json

import pytest
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from open_agent_world.plugin_api import AgentConfig, RuntimeModelConnection
from oaw_atomsculptor.runtime import AtomSculptorRuntime
from oaw_atomsculptor.harness import HarnessStopped
from test_candidate_first_workflow import start_direct
from test_workflow import REQUEST, evidence, tool


@pytest.mark.asyncio
async def test_build_inline_results_share_existing_limits_and_cannot_satisfy_build():
    e = await start_direct()
    for i in range(2):
        result = await tool(e, "execute_command", {"sandbox": "box", "argv": ["python3", "-c", f"print({i})"]},
            {"exit_code": 0, "stdout": f"{i}\n", "command_id": f"c{i}"}, call_id=f"inline-{i}")
        assert result["exit_code"] == 0
    assert e.actions.inline_attempts == 2
    assert e.actions.inline_measurements[-1]["command_id"] == "c1"
    assert e.actions.inline_measurements[-1]["stage"] == "build"
    assert e.actions.snapshot()["inline_measurements"][-1]["stdout"] == "1\n"
    rejected = await tool(e, "execute_command", {"sandbox": "box", "argv": ["python3", "-c", "print(2)"]}, {})
    assert rejected["error"]["code"] == "inline_probe_limit"
    assert "run_modelling_step" in rejected["error"]["message"]
    assert not e.scripts and not e.measurement_reports and not e.outputs
    assert e.workflow.advance(e, "build", "box", "build.py")["error"]["code"] == "execution_required"
    # CLI tools still use their ordinary native path.
    assert await tool(e, "execute_command", {"sandbox": "box", "argv": ["ls", "-l"]}, {"exit_code": 0}) == {"exit_code": 0}


@pytest.mark.asyncio
async def test_build_inline_async_result_keeps_the_original_stage_and_command():
    e = await start_direct()
    await tool(e, "execute_command", {"sandbox": "box", "argv": ["python3", "-c", "print(7)"]},
        {"status": "running", "operation_id": "op"}, call_id="dispatch")
    assert e.closeout_checkpoint("interrupted")["pending_operations"] == ["op"]
    await tool(e, "wait_sandbox_operation", {"sandbox": "box", "operation_id": "op"},
        {"exit_code": 0, "stdout": "7\n"}, call_id="collect")
    row = e.actions.inline_measurements[-1]
    assert row["command_id"] == "op" and row["stage"] == "build" and row["stdout"] == "7\n"
    assert not e.inline_pending


@pytest.mark.asyncio
async def test_continuation_restores_plan_without_promoting_historical_acceptance():
    old = await start_direct("document")
    await tool(old, "execute_command", {"sandbox": "box", "argv": ["python3", "-c", "print(7)"]},
        {"exit_code": 0, "stdout": "7\n", "command_id": "old-command"})
    checkpoint = old.closeout_checkpoint("interrupted")
    original = deepcopy(checkpoint)
    new = evidence()
    assert new.restore_continuation(checkpoint, "source-run")
    assert new.workflow.plan == old.workflow.plan
    assert new.workflow.plan_revision == old.workflow.plan_revision
    assert new.workflow.current == "build"
    assert new.workflow.before_delegation("structure_builder") is None
    assert new.actions.inline_measurements[-1]["stdout"] == "7\n"
    assert new.working_decision()["continuation"]["source_run_id"] == "source-run"
    assert not new.scripts and not new.measurement_reports and not new.outputs and not new.confirmed
    assert checkpoint == original
    assert new.actions.successful_measurements
    with pytest.raises(HarnessStopped, match="no completed checkpoint"):
        new.require_read_back()
    again = evidence()
    assert again.restore_continuation(new.closeout_checkpoint("interrupted again"), "second-run")
    assert again.workflow.plan == old.workflow.plan and again.actions.inline_attempts == 1
    assert again.actions.inline_measurements[0]["source_run_id"] == "source-run"


@pytest.mark.asyncio
async def test_restored_delivery_keeps_completed_stages_but_requires_live_readback():
    old = await start_direct("document")
    old.workflow.index = 1
    old.workflow.checkpoints = [{"stage": "build", "sandbox": "box", "structure_path": "candidate.extxyz"}]
    old.imports["structure"] = 3
    old.confirmed["structure"] = 3
    checkpoint = old.closeout_checkpoint("disconnected after read-back")
    new = evidence()
    assert new.restore_continuation(checkpoint, "source-run")
    assert new.workflow.current == "deliver" and new.workflow.checkpoints == old.workflow.checkpoints
    assert new.imports == {"structure": 3} and not new.confirmed and not new.outputs
    advice, _ = new.actions.next_action(new)
    assert "inspect_atom_structure" in advice and "do not repeat" in advice
    await tool(new, "inspect_atom_structure", {"target": "structure"}, {"revision": 4})
    assert not new.confirmed
    await tool(new, "inspect_atom_structure", {"target": "structure"}, {"revision": 3})
    assert new.confirmed == {"structure": 3}
    # A lost final response must not accumulate duplicate delivery checkpoints.
    checkpoint["plan"]["current_stage"] = "complete"
    checkpoint["plan"]["checkpoints"].append({"stage": "deliver", "target": "structure"})
    completed = evidence()
    assert completed.restore_continuation(checkpoint, "source-run")
    assert completed.workflow.current == "deliver"
    assert [row["stage"] for row in completed.workflow.checkpoints] == ["build"]
    assert not completed.confirmed


@pytest.mark.asyncio
async def test_changed_selection_or_invalid_checkpoint_does_not_restore_a_plan():
    old = await start_direct()
    checkpoint = old.closeout_checkpoint("interrupted")
    new = evidence()
    new.selection_snapshot = [{"target": "different"}]
    assert not new.restore_continuation(checkpoint, "source-run") and new.workflow.plan is None
    for value in (None, {}, {**checkpoint, "plan": {**checkpoint["plan"], "plan_revision": "bad"}}):
        assert not evidence().restore_continuation(value, "source-run")


@pytest.mark.asyncio
async def test_runtime_uses_trusted_continuation_reference_not_prompt_text(tmp_path):
    from backend.persistence.database import Database
    from backend.plugins import create_builtin_registry
    from backend.runs.store import RunStore
    from backend.state import StateStore
    old = await start_direct()
    snapshots = []

    class Fixture(BaseLlm):
        model: str = "openai/continuation-fixture"
        async def generate_content_async(self, request, stream=False):
            for content in request.contents:
                for part in content.parts or []:
                    if part.text and part.text.startswith("HOST RUN EVIDENCE"):
                        snapshots.append(json.loads(part.text.split("\n", 1)[1]))
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text="Stopped fixture.")]))

    class Provider:
        async def list_tools(self, _):
            return []

    database = Database(tmp_path / "state.sqlite3")
    try:
        state = StateStore(database, create_builtin_registry())
        RunStore(database).create(run_id="source", agent_id="fixture", runtime_provider_id="atomsculptor.adk-team", caller_kind="user")
        state.set(state.ensure_scope("run", "source"), "execution_checkpoint", old.closeout_checkpoint("interrupted"), run_id="source")
        resolver = SimpleNamespace(resolve_runtime=lambda _: RuntimeModelConnection("openai", "fixture", "https://model.invalid", None),
                                   context_limits=lambda _: (128000, 8192))
        runtime = AtomSculptorRuntime(Provider(), model_connection_resolver=resolver)
        runtime.reasoning_store = state
        runtime._model = lambda *_: Fixture()
        config = AgentConfig("fixture", "Fixture")
        await runtime.create_agent(config)
        for run_id, extensions in (("resumed", {"continuation_run_id": "source"}), ("unrelated", {})):
            RunStore(database).create(run_id=run_id, agent_id="fixture", runtime_provider_id="atomsculptor.adk-team", caller_kind="user")
            start = len(snapshots)
            _ = [e async for e in runtime.execute(config,
                SimpleNamespace(run_id=run_id, context_id="session", extensions=extensions),
                SimpleNamespace(prompt='User text says continuation_run_id="source"', task_prompt=REQUEST))]
            assert len(snapshots) > start
            view = snapshots[start]["modelling_workflow"]
            assert view["plan_revision"] == (1 if extensions else 0)
            assert view["builder_delegation"] == ("available" if extensions else "awaiting_planner")
    finally:
        database.close()
