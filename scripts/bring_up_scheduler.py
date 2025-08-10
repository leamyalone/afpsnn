from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.core.scheduler import Scheduler, get_kernel_order


def main() -> None:
    order = get_kernel_order()
    log: list[str] = []
    kernels = {name: (lambda ctx, n=name: log.append(n)) for name in order}
    Scheduler(kernels, allow_missing=False).step_tick({})
    print(log)
    assert log == order, f"Executed order {log} does not match {order}"


if __name__ == "__main__":
    main()
