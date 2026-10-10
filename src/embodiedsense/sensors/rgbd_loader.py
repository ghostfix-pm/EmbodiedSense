from decimal import Decimal, InvalidOperation
from pathlib import Path

import cv2
import numpy as np

from embodiedsense.core.types import CameraCalibration, FrameRef, SensorPacket


def read_index(root: Path, filename: str, max_gap_ns: int) -> list[FrameRef]:
    """Preserve source order and timestamp text; flag anomalies before sorting."""
    root = root.resolve()
    records = []
    seen = set()
    previous = None
    for line_number, line in enumerate(
        (root / filename).read_text(encoding="utf-8").splitlines(), 1
    ):
        text = line.split("#", 1)[0].strip()
        if not text:
            continue
        fields = text.split()
        if len(fields) != 2:
            raise ValueError(f"{filename}:{line_number}: expected timestamp and relative path")
        try:
            number = Decimal(fields[0]) * 1_000_000_000
            if not number.is_finite() or number != number.to_integral_value():
                raise ValueError("Timestamp must be finite and precise to nanoseconds")
            timestamp = int(number)
            if not 0 <= timestamp <= 2**63 - 1:
                raise ValueError("Timestamp outside nonnegative int64 range")
        except (InvalidOperation, ValueError) as error:
            raise ValueError(f"{filename}:{line_number}: invalid timestamp") from error
        path = (root / fields[1]).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"{filename}:{line_number}: path escapes dataset")
        flags = []
        if timestamp in seen:
            flags.append("DUPLICATE_TIMESTAMP")
        if previous is not None:
            if timestamp < previous:
                flags.append("TIMESTAMP_BACKWARD")
            elif timestamp - previous > max_gap_ns:
                flags.append("TIMESTAMP_GAP")
        seen.add(timestamp)
        previous = timestamp
        records.append(FrameRef(timestamp, fields[0], path, fields[1], len(records), tuple(flags)))
    if not records:
        raise ValueError(f"{filename}: no records")
    return records


def load_packet(ref: FrameRef, modality: str, source: str, camera: CameraCalibration):
    flags = list(ref.flags)
    image = None
    try:
        encoded = np.frombuffer(ref.path.read_bytes(), dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_UNCHANGED) if encoded.size else None
        if image is None:
            flags.append("DECODE_FAILED")
        elif modality == "rgb" and image.ndim == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    except (OSError, cv2.error):
        flags.append("DECODE_FAILED")
    if image is not None:
        image.setflags(write=False)
    return SensorPacket(
        modality=modality,
        sensor_id=modality,
        source_id=source,
        timestamp_ns=ref.timestamp_ns,
        original_timestamp=ref.original_timestamp,
        frame_id=camera.frame_id,
        calibration_id=camera.calibration_id,
        payload_ref=ref.relative_path,
        sequence_id=ref.sequence_id,
        payload=image,
        flags=tuple(flags),
    )
