"""Save a structure and stage its exact bytes for the native command receipt."""
import os
import re
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from time import time_ns
from uuid import uuid4


def save_structure(path, writer, *, append=False):
    """Use the original serializer; preserve each completed save in command order."""
    staging = os.environ.get("OAW_COMMAND_OUTPUTS")
    target = Path(path)
    if not staging or not re.fullmatch(r"\.oaw-command-output-[a-f0-9]{32}", staging):
        return writer(target)
    workspace = Path.cwd().resolve()
    target = target.absolute()
    relative = (target.parent.resolve() / target.name).relative_to(workspace)
    target = workspace / relative
    if target.is_symlink() or relative.parts[0] == staging:
        raise ValueError("Structure output must be a regular workspace file")
    versions = workspace / staging
    versions.mkdir(mode=0o700, exist_ok=True)
    if versions.is_symlink():
        raise ValueError("Structure version directory cannot be a symlink")
    version = f"{time_ns():020d}-{uuid4().hex}"
    with TemporaryDirectory(dir=target.parent) as scratch:
        original = Path(scratch) / target.name
        if append and target.exists():
            shutil.copyfile(target, original)
        result = writer(original)
        with TemporaryDirectory(dir=versions, prefix=".pending-") as pending:
            pending = Path(pending)
            copy = pending / "file" / relative
            copy.parent.mkdir(parents=True)
            shutil.copyfile(original, copy)
            os.replace(original, target)
            (pending / "file").rename(versions / version)
    return result


def write_structure(path, atoms, **options):
    from ase.io import write
    return save_structure(path, lambda target: write(target, atoms, **options), append=options.get("append", False))
