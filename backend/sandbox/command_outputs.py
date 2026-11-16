"""Transfer completed per-write files to the existing immutable Artifact journal."""
import base64
import re

from backend.errors import DomainError, ResourceValidationError

from .files import parts
from .models import SandboxError
from .task_workspace import path_for
from .transfers import CHUNK_BYTES


async def retain_outputs(execution, staging):
    backend, sandbox = execution.backend, execution.sandbox_id
    receipt, services = execution.receipt, execution.services
    prefix = path_for(execution.directory, staging)
    entries = await backend.file_operation(sandbox, "capture_manifest", paths=[prefix], missing_ok=True)
    if not entries:
        return
    versions = []
    receipt["saved_outputs"] = versions
    for entry in entries:
        if entry["directory"]:
            continue
        sequence, _, relative = entry["path"].removeprefix(prefix + "/").partition("/")
        if not re.fullmatch(r"[0-9]{20}-[a-f0-9]{32}", sequence) or not relative:
            continue  # Incomplete writes stay in a .pending-* directory.
        workspace_path = "/".join(parts(relative))

        async def chunks():
            offset = 0
            while offset < entry["size"]:
                chunk = await backend.file_operation(sandbox, "read_chunk", path=entry["path"],
                    offset=offset, expected=entry["signature"])
                data = base64.b64decode(chunk["data"], validate=True)
                if not data or len(data) > CHUNK_BYTES or offset + len(data) > entry["size"]:
                    raise ResourceValidationError("Run output changed during transfer")
                offset += len(data)
                yield data

        try:
            record = await services.resources.artifacts.retain_run_output(services,
                parts(workspace_path)[-1], chunks(), agent_id=execution.agent_id,
                run_id=receipt["run_id"], sandbox_id=sandbox, command_id=receipt["id"],
                workspace_path=workspace_path, sequence=sequence, started_at=receipt["started_at"],
                authorize=execution._authorize)
            versions.append({"version_id": record["version_id"], "path": workspace_path})
        except (OSError, ValueError, DomainError, SandboxError) as error:
            versions.append({"path": workspace_path, "sequence": sequence, "error": type(error).__name__})
    if all("version_id" in version for version in versions):
        await backend.file_operation(sandbox, "delete", path=prefix)
