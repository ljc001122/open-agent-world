"""Bound output-limit recovery to one retry per observed action.

Hold complete responses until clean EOF. Never commit truncated tool calls,
restart delegations, or replay already executed capabilities.
"""
from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Mapping
from contextlib import aclosing
from typing import Any

from open_agent_world.plugin_api import AgentRuntimeError


RECOVERY_INSTRUCTION = """HOST OUTPUT-LIMIT RECOVERY: the previous model response exhausted its
output allowance before producing a usable action. That response was not committed;
no tool from it was dispatched. Existing tool receipts and the original request
remain authoritative. This is the only output-limit retry for this action.
Do not repeat the long derivation or enumerate alternative algorithms. Use the next
authorized tool to collect a pending receipt or measure the single condition
that determines the next step. Use confirmed artifact handoffs as inputs. For
uncertain counts, parameters or invariants, submit a small Sandbox calculation
whose result decides what to do next. Keep user constraints unchanged. If you cannot take
an authorized next step, report the actual blocker concisely via your normal delivery
path. Do not claim unexecuted construction or validation succeeded."""


def _reason(response: Any) -> str:
    value = getattr(response, "finish_reason", None) or getattr(response, "error_code", None)
    return str(getattr(value, "name", None) or getattr(value, "value", value)).rsplit(".", 1)[-1].upper()


def _finished_execution_recovery(evidence, declarations, stages):
    """Focus a retry that still owes an assessment of a finished command."""
    if (stages != ["observe"] or evidence.workflow.current not in {"probe", "build"}
            or evidence.executions or evidence.pending or evidence.inline_pending or evidence.skill_operations
            or evidence.steps.pending_input_check() or evidence.steps.argument_issue
            or "resume_modelling_step" in declarations):
        return None
    latest = evidence.latest_experiment()
    if latest is None or not latest.command_id:
        return None
    allowed = {"advance_modelling_stage", "finish_task", "patch_modelling_step",
               "read_modelling_source", "read_tool_result"} & declarations.keys()
    measured = evidence.measurement_reports.get(latest.execution_sequence, {})
    checks = measured.get("metadata", {}).get("checks", {})
    failed_script_checks = [key[:160] for key, value in checks.items() if value is False] if isinstance(checks, Mapping) else []
    from .measurements import constraint_failures

    return allowed, {
        "stage": evidence.workflow.current, "plan_revision": evidence.workflow.plan_revision,
        "command_id": latest.command_id, "sandbox": latest.sandbox, "script_path": latest.path,
        "script_version": latest.version, "exit_code": latest.exit_code, "measurement_kind": measured.get("kind"),
        "failed_constraints": [row["name"][:160] for row in constraint_failures(measured)[:8]],
        "failed_script_checks": failed_script_checks[:8],
        "confirmed_artifact_paths": evidence.workflow.execution_artifact_paths(evidence, latest)[:8],
    }


def _project_action(request, evidence, role, bindings, *, recovering_output):
    """Project preparation, refinement or assessment on an outbound request copy."""
    if not evidence.actions.enabled(evidence, role) or request.config is None:
        return request
    preparation = evidence.actions.preparation_tool
    declarations = {d.name: d for tool in request.config.tools or []
                    for d in tool.function_declarations or []}
    advance = declarations.get("advance_modelling_stage")
    properties = (advance.parameters_json_schema or {}).get("properties", {}) if advance else {}
    stages = properties.get("stage", {}).get("enum", [])
    refine = recovering_output and not preparation and evidence.steps.available and "refine" in stages
    finished = (_finished_execution_recovery(evidence, declarations, stages)
                if recovering_output and not preparation and not refine and evidence.steps.available else None)
    if not preparation and not refine and not finished:
        return request
    from open_agent_world.plugin_api.model_runtime import signed_history, snapshot_request

    if finished:
        allowed, facts = finished
    elif refine:
        allowed = {"finish_task", "advance_modelling_stage"}
    else:
        allowed = {"finish_task", *(name for name in declarations if evidence.semantic_tool(name) == preparation)}
    if not (declarations.keys() & (allowed - {"finish_task"})):
        return request
    projected = snapshot_request(request)
    selected = []
    for tool in projected.config.tools or []:
        tool.function_declarations = [d for d in tool.function_declarations or [] if d.name in allowed]
        if tool.function_declarations:
            selected.append(tool)
    projected.config.tools = selected
    if finished:
        actions = ("Call advance_modelling_stage(stage='observe') with a brief assessment of this command. "
                   "If one measured failure has a small fix and patch_modelling_step is advertised, submit the patch "
                   "with previous_assessment instead. Use an advertised reader for one specific missing fact. "
                   "If blocked or a measured contradiction needs plan review, report it through finish_task. "
                   "Treat script checks as diagnostics; existing acceptance and validation still apply.")
        projected.contents.append(bindings.types.Content(role="user", parts=[bindings.types.Part.from_text(
            text="HOST FINISHED EXECUTION RECOVERY\n" + json.dumps(facts, ensure_ascii=False) + "\n" + actions)]))
        return projected
    for tool in selected:
        for declaration in tool.function_declarations:
            if declaration.name == "finish_task":
                declaration.parameters = None
                declaration.parameters_json_schema = {"type": "object", "properties": {"result": {
                    "type": "object", "properties": {
                        "status": {"type": "string", "enum": ["blocked"]}, "reason": {"type": "string"}},
                    "required": ["status", "reason"], "additionalProperties": False}},
                    "required": ["result"], "additionalProperties": False}
            elif declaration.name == "advance_modelling_stage":
                declaration.parameters = None
                declaration.parameters_json_schema = {"type": "object", "properties": {
                    "stage": {"type": "string", "enum": ["refine"]}, "reason": properties["reason"],
                    "next_experiment": properties["next_experiment"], "sandbox": properties["sandbox"]},
                    "required": ["stage", "reason", "next_experiment"], "additionalProperties": False}
    window = getattr(evidence.trace, "context_windows", {}).get(role)
    if (signed_history(request) or getattr(request, "previous_interaction_id", None)
            or getattr(request.config, "cached_content", None) or getattr(request, "cache_config", None)
            or getattr(getattr(window, "capabilities", None), "preserve_tool_reasoning", False)):
        # Keep the content of provider-bound exchanges and apply only the tool projection.
        return projected
    if preparation:
        instruction = ("Prepare the authorized Sandbox for this modelling run. Call the advertised preparation "
                       "tool once, or finish_task with status=blocked and a reason. Use the original request only "
                       "for resource selection and user restrictions. Leave scientific planning to the next turn.")
        facts = {"action": preparation, "observed_sandbox_states": evidence.actions.sandbox_states}
    else:
        instruction = ("The first modelling action exhausted its output allowance. Call advance_modelling_stage "
                       "with stage=refine and propose one small executable next_experiment. Choose a saved "
                       "intermediate or measure the condition that decides the next construction step. Leave "
                       "dependent work for its result. Keep the user requirements and acceptance checks unchanged.")
        decision = evidence.working_decision()
        facts = {"stage": decision["stage"], "current_subtask": decision["current_subtask"],
                 "retained_artifact_paths": [a["path"] for a in evidence.artifact_handoffs.values()]}
    projected.config.system_instruction = instruction
    projected.contents = [bindings.types.Content(role="user", parts=[bindings.types.Part.from_text(text=
        "HOST ACTION STATE\n" + json.dumps(facts, ensure_ascii=False) +
        "\nOriginal user request (verbatim):\n" + evidence.original_request)])]
    return projected


def bounded_output_model(model: Any, trace: Any, role: str, evidence: Any,
                         bindings: Any, output_limit: int | None) -> Any:
    if not callable(getattr(model, "generate_content_async", None)):
        return model
    from google.adk.models.base_llm import BaseLlm
    from pydantic import Field
    from open_agent_world.plugin_api.model_runtime import snapshot_request as _snapshot

    class BoundedOutputModel(BaseLlm):
        delegate: Any = Field(exclude=True)

        @property
        def capabilities(self):
            return self.delegate.capabilities

        async def generate_content_async(self, llm_request, stream=False):
            request = _snapshot(llm_request)
            recovering_action = False
            recovering_output = False
            while True:
                responses = []
                action_mode = evidence.actions.enabled(evidence, role)
                # Recovery allowance applies only to this request, never later
                # actions. A retry retains at least the ordinary reasoning time.
                # The cumulative action recovery count is telemetry, not a fuse.
                seconds = evidence.limits.model_action_seconds if action_mode else None
                if seconds is not None and recovering_action:
                    seconds = max(seconds, evidence.limits.action_recovery_seconds or seconds)
                deadline = asyncio.timeout(seconds)
                timed_out = False
                outbound = _project_action(request, evidence, role, bindings, recovering_output=recovering_output)
                try:
                    async with deadline:
                        if seconds is not None:
                            trace.recovery_deadlines[role] = (deadline, seconds)
                        try:
                            async with aclosing(self.delegate.generate_content_async(outbound, stream=stream)) as source:
                                async for response in source:
                                    if getattr(response, "partial", False):
                                        yield response  # Preview only; ADK never dispatches partial calls.
                                    else:
                                        responses.append(response)
                        finally:
                            trace.recovery_deadlines.pop(role, None)
                except TimeoutError:
                    if not deadline.expired():
                        raise  # A provider TimeoutError belongs to transport recovery.
                    timed_out = True
                    preview = trace.interrupted_reasoning(role)
                    if preview:
                        trace.queue.put_nowait(("progress", preview))
                    pending = trace.pending.pop(role, None)
                    now = time.monotonic()
                    last = trace._last_activity.get(role)
                    evidence.notice(role, f"Model request hard ceiling reached ({seconds}s); "
                        "response incomplete, no tools dispatched",
                        phase="model", model_request=pending[0] if pending else None,
                        model_attempt=trace.request_attempts.get(role, 1), run_attempt=trace.run_attempt,
                        elapsed_ms=round((now - pending[1]) * 1000) if pending else seconds * 1000,
                        input_tokens=None, output_tokens=None,
                        finish_reason="HOST_ACTION_TIMEOUT", interrupted=True,
                        timeout_kind="request_wall_clock", deadline_seconds=seconds,
                        received_content=last is not None,
                        idle_seconds=round(now - (last if last is not None else pending[1]), 3) if pending else None)
                evidence.actions.deduplicate_starts(evidence, role, responses)
                truncated = any(_reason(r) in {"MAX_TOKENS", "LENGTH"} for r in responses)
                parts = [p for r in responses for p in getattr(getattr(r, "content", None), "parts", None) or ()]
                calls = any(getattr(p, "function_call", None) is not None for p in parts)
                usable = calls or any(not getattr(p, "thought", False) and bool(getattr(p, "text", None)) for p in parts)
                if action_mode:
                    provider_error = any(getattr(r, "error_code", None) for r in responses)
                    # Output exhaustion uses its own recovery below. It is not
                    # a permission/action error or a stream timeout.
                    action_failure = timed_out or (not truncated and not provider_error and not calls)
                    if action_failure:
                        for response in responses:
                            evidence.after_model(response)
                            if not timed_out:
                                await trace.callbacks(role)["after_model_callback"](None, response)
                        reason = "request_deadline" if timed_out else "no_tool_action"
                        messages = {
                            "request_deadline": "The model response exceeded this request's hard ceiling; no calls were dispatched.",
                            "no_tool_action": "This stage needs an authorized tool action or an actual blocker reported through finish_task.",
                        }
                        rejected = evidence.workflow.error(reason, messages[reason])
                        proposed = [p.function_call for p in parts if getattr(p, "function_call", None)]
                        rejected["error"]["calls"] = [{"call_id": c.id, "tool": c.name} for c in proposed]
                        if timed_out:
                            if recovering_action:
                                evidence.stop("Builder made no permitted executable action (request_deadline) "
                                              "after the bounded action recovery; current stage=" + evidence.workflow.current)
                        else:
                            # Reuse the native unchanged-rejection detector. Call IDs
                            # change on retries; tool semantics/arguments and host facts
                            # identify the action that has actually received feedback.
                            evidence.record_rejection(role, "model_response", {"calls": [
                                {"tool": evidence.semantic_tool(c.name), "arguments": c.args} for c in proposed]}, rejected)
                            if evidence.block_reason:
                                evidence.stop(evidence.block_reason)
                        evidence.actions.recoveries += 1
                        recovering_action = True
                        evidence.notice(role, "Correcting the rejected response; no tools dispatched or replayed",
                            recovery_event="model_action_recovery", recovery_scope="model_response", retrying=True,
                            reason=reason, error=rejected["error"])
                        request.contents.append(bindings.types.Content(role="user", parts=[
                            bindings.types.Part.from_text(text=evidence.actions.recovery_instruction(rejected["error"]))]))
                        evidence.before_model(role, request, bindings, output_limit)
                        await trace.callbacks(role)["before_model_callback"](None, request)
                        continue
                if not truncated and usable:
                    parts = [p for r in responses for p in getattr(getattr(r, "content", None), "parts", None) or ()]
                    if action_mode:
                        evidence.actions.prepare_response(evidence, parts, outbound, role)
                    try:
                        route_error = evidence.workflow.accept_delegations(evidence, role, parts)
                    except AgentRuntimeError:
                        # A capability/budget rejection discards this call before
                        # SDK dispatch, but its actual model usage still happened.
                        for response in responses:
                            evidence.after_model(response)
                            await trace.callbacks(role)["after_model_callback"](None, response)
                        raise
                    if route_error is not None:
                        for response in responses:
                            evidence.after_model(response)
                            await trace.callbacks(role)["after_model_callback"](None, response)
                        if evidence.workflow.routing_recoveries:
                            evidence.stop("coordinator repeatedly bypassed the required Planner")
                        evidence.workflow.routing_recoveries += 1
                        evidence.notice(role, "Planner required before custom modelling · correcting delegation once; no tools dispatched",
                            workflow_event="modelling_route_recovery", error=route_error["error"])
                        request.contents.append(bindings.types.Content(role="user", parts=[
                            bindings.types.Part.from_text(text="HOST MODELLING ROUTE: " + route_error["error"]["message"])]))
                        evidence.before_model(role, request, bindings, output_limit)
                        await trace.callbacks(role)["before_model_callback"](None, request)
                        continue
                if not truncated and (usable or any(getattr(r, "error_code", None) for r in responses)):
                    for response in responses:
                        yield response
                    return
                # ADK will never see this discarded response, so settle its
                # actual usage/trace here. The next accepted one uses callbacks.
                pending = trace.pending.get(role)
                discarded_request = pending[0] if pending else None
                discarded_attempt = trace.request_attempts.get(role, 1)
                for response in responses:
                    evidence.after_model(response)
                    await trace.callbacks(role)["after_model_callback"](None, response)
                if truncated and not calls and evidence.claim_output_recovery(role):
                    recovering_output = True
                    request.contents.append(bindings.types.Content(role="user", parts=[
                        bindings.types.Part.from_text(text=RECOVERY_INSTRUCTION +
                            ("\n" + evidence.actions.recovery_instruction() if action_mode else ""))]))
                    evidence.before_model(role, request, bindings, output_limit)
                    await trace.callbacks(role)["before_model_callback"](None, request)
                    retry_request = trace.pending[role][0]
                    evidence.notice(role, f"{role.replace('_', ' ')} · request {discarded_request} discarded at the "
                        f"output limit; retrying as request {retry_request}. No tools dispatched.",
                        recovery_event="model_output_recovery", recovery_scope="model_response", retrying=True,
                        run_attempt=trace.run_attempt, source_model_request=discarded_request,
                        source_model_attempt=discarded_attempt, recovery_model_request=retry_request,
                        response_disposition="discarded_output_limit")
                    continue
                reason = ("model output reached its token limit; truncated tool calls were not dispatched"
                          if truncated and calls else
                          "model output reached its token limit after the single bounded recovery"
                          if truncated else "model returned no final text or tool call")
                if truncated:
                    evidence.notice(role, f"{role.replace('_', ' ')} · request {discarded_request} discarded at the "
                        "output limit. No tools dispatched.",
                        recovery_event="model_output_discarded", run_attempt=trace.run_attempt,
                        source_model_request=discarded_request, source_model_attempt=discarded_attempt,
                        response_disposition="discarded_output_limit", retrying=False)
                if truncated and evidence.output_recovery_used(role):
                    # Reuse native unfinished-checkpoint closeout. The discarded
                    # response contains no confirmed action or task completion.
                    evidence.stop(f"{role.replace('_', ' ')}: {reason}")
                raise AgentRuntimeError(f"AtomSculptor {role.replace('_', ' ')} stopped: {reason}. "
                    "Completed tools were not replayed; inspect existing Sandbox files and document state before continuing.")

    return BoundedOutputModel(model=model.model, delegate=model)
