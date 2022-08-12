from typing import Any, List, Optional

import modal
from redun.config import Config
from redun.executors.local import LocalExecutor
from redun.scheduler import Scheduler
from redun.task import Task, get_task_registry
from redun.utils import get_func_source


def modal_task(
    func: Optional[modal.Function] = None,
    *,
    stub: Optional[str] = None,
    namespace: Optional[str] = None,
    version: Optional[str] = None,
    compat: Optional[List[str]] = None,
    script: bool = False,
    hash_includes: Optional[list] = None,
    **task_options_base: Any,
):
    def deco(func: modal.Function) -> Task[modal.Function]:

        func = stub.function(func)
        raw_f = func.get_raw_f()
        source = get_func_source(func=raw_f)

        _task: Task[modal.Function] = Task(
            func,
            name=raw_f.__name__,
            namespace=namespace,
            version=version,
            compat=compat,
            script=script,
            task_options_base=task_options_base,
            hash_includes=hash_includes,
            source=source,
        )
        get_task_registry().add(_task)
        func.lazy = _task
        return func

    if func:
        return deco(func)
    else:
        return deco


def remote_scheduler(db_uri: str):
    config = Config()
    config.read_dict({"backend": {"db_uri": db_uri}})
    executor = LocalExecutor("default")
    scheduler = Scheduler(executor=executor, config=config)
    scheduler.backend.load()

    return scheduler
