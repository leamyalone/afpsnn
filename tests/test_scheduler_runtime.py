import importlib
from typing import Callable

import pytest

from models.core import scheduler


# Helper for test kernels: each stage appends its name to log.
def _make_kernels(log: list[str], stages: list[str]) -> dict[str, Callable[[object], None]]:
    return {name: (lambda ctx, n=name: log.append(n)) for name in stages}


def test_get_kernel_order_exposed_and_copy_safe() -> None:
    order1 = scheduler.get_kernel_order()
    assert order1 == list(scheduler.KERNEL_ORDER), "get_kernel_order should return a list copy of KERNEL_ORDER"

    # Mutating the returned list must not affect the module's KERNEL_ORDER
    order1[0] = "bogus"
    order2 = scheduler.get_kernel_order()
    assert order2[0] == scheduler.KERNEL_ORDER[0], "Mutating returned list should not change KERNEL_ORDER"

    # Reloading should also show the canonical order unaffected
    importlib.reload(scheduler)
    assert scheduler.get_kernel_order() == list(scheduler.KERNEL_ORDER)


def test_scheduler_execution_order_matches_spec() -> None:
    log: list[str] = []
    stages = scheduler.get_kernel_order()
    kernels = _make_kernels(log, stages)
    sch = scheduler.Scheduler(kernels, allow_missing=False)
    sch.step_tick({})
    assert log == stages, f"Scheduler executed order {log}, expected {stages}"


def test_missing_kernel_behavior_strict_mode() -> None:
    stages = scheduler.get_kernel_order()
    log: list[str] = []
    # Omit the first stage
    kernels = _make_kernels(log, stages[1:])
    sch = scheduler.Scheduler(kernels, allow_missing=False)
    with pytest.raises(NotImplementedError):
        sch.step_tick({})


def test_missing_kernel_behavior_lenient_mode_runs_only_bound() -> None:
    stages = scheduler.get_kernel_order()
    last = stages[-1]
    log: list[str] = []
    kernels = {last: (lambda ctx: log.append(last))}
    sch = scheduler.Scheduler(kernels, allow_missing=True)
    sch.step_tick({})
    assert log == [last], f"Only bound stage '{last}' should execute"


def test_validate_kernel_bindings_reports_missing_and_extras() -> None:
    stages = scheduler.get_kernel_order()

    def _noop(ctx: object) -> None:
        pass

    full = {name: _noop for name in stages}

    # Remove first and last stages
    partial = {name: _noop for name in stages[1:-1]}
    missing, extras = scheduler.validate_kernel_bindings(partial)
    expected_missing = (stages[0], stages[-1])
    assert missing == expected_missing, f"Missing {missing}, expected {expected_missing}"
    assert extras == tuple(), f"Extras should be empty, got {extras}"

    # Add an extra bogus key
    with_extra = dict(full)
    with_extra["bogus"] = _noop
    missing, extras = scheduler.validate_kernel_bindings(with_extra)
    assert missing == tuple(), f"No stages should be missing, got {missing}"
    assert extras == ("bogus",), f"Extras {extras} should contain only 'bogus'"


def test_bind_api_rejects_unknown_and_noncallable() -> None:
    sch = scheduler.Scheduler({})
    with pytest.raises(ValueError):
        sch.bind("not_a_stage", lambda ctx: None)
    stage = scheduler.get_kernel_order()[0]
    with pytest.raises(TypeError):
        sch.bind(stage, "not callable")  # type: ignore[arg-type]


def test_bind_can_replace_existing_callable() -> None:
    stages = scheduler.get_kernel_order()
    target = stages[0]
    log: list[str] = []
    sch = scheduler.Scheduler({target: lambda ctx: log.append("old")}, allow_missing=True)
    sch.bind(target, lambda ctx: log.append("new"))
    sch.step_tick({})
    assert log == ["new"], "bind should replace existing callable"


def test_step_tick_bubbles_exceptions() -> None:
    class Boom(RuntimeError):
        pass

    stages = scheduler.get_kernel_order()
    failing = stages[3]
    log: list[str] = []

    def make_fn(name: str):
        if name == failing:

            def _boom(ctx: object) -> None:
                raise Boom(name)

            return _boom
        return lambda ctx, n=name: log.append(n)

    kernels = {name: make_fn(name) for name in stages}
    sch = scheduler.Scheduler(kernels, allow_missing=False)
    with pytest.raises(Boom) as exc:
        sch.step_tick({})
    assert str(exc.value) == failing
    assert log == stages[: stages.index(failing)], "Stages after failing one should not run"


def test_idempotent_construction() -> None:
    # allow_missing=True should skip all stages without error
    scheduler.Scheduler({}, allow_missing=True).step_tick({})

    # allow_missing=False should raise on the first missing stage
    with pytest.raises(NotImplementedError):
        scheduler.Scheduler({}, allow_missing=False).step_tick({})
