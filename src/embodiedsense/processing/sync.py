from bisect import bisect_left
from collections.abc import Iterator, Sequence

from embodiedsense.core.types import FrameRef


def associate(
    rgb: Sequence[FrameRef], depth: Sequence[FrameRef], tolerance_ns: int
) -> Iterator[tuple[FrameRef, FrameRef | None]]:
    """Offline nearest neighbor, inclusive tolerance, earlier timestamp wins ties.

    Depth reuse is permitted and reported. This is not a one-to-one or causal online matcher.
    Every RGB record yields one observation, including unmatched records.
    """
    if tolerance_ns < 0:
        raise ValueError("tolerance_ns cannot be negative")
    ordered = sorted(depth, key=lambda x: (x.timestamp_ns, x.sequence_id))
    times = [item.timestamp_ns for item in ordered]
    for reference in sorted(rgb, key=lambda x: (x.timestamp_ns, x.sequence_id)):
        index = bisect_left(times, reference.timestamp_ns)
        candidates = ordered[max(0, index - 1) : index + 1]
        best = min(
            candidates,
            key=lambda item: (abs(item.timestamp_ns - reference.timestamp_ns), item.timestamp_ns),
            default=None,
        )
        if best is not None and abs(best.timestamp_ns - reference.timestamp_ns) > tolerance_ns:
            best = None
        yield reference, best
