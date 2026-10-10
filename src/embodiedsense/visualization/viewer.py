import numpy as np


class RerunWriter:
    """Write an RRD for later viewing. No windows, servers or browser tabs are opened."""

    def __init__(self, path):
        import rerun as rr

        self.rr = rr
        self.recording = rr.RecordingStream("embodiedsense")
        self.recording.save(path)
        self.recording.log("camera", rr.ViewCoordinates.RDF, static=True)

    def write(self, obs):
        rr = self.rr
        rec = self.recording
        rec.set_time("sensor_time", timestamp=np.datetime64(obs.rgb.timestamp_ns, "ns"))
        # Clear previous data first: an invalid frame must not display stale imagery/geometry.
        rec.log("camera/rgb", rr.Clear(recursive=True))
        rec.log("camera/depth", rr.Clear(recursive=True))
        rec.log("camera/points", rr.Clear(recursive=True))
        if obs.rgb.payload is not None and obs.rgb.payload.ndim == 3:
            rec.log("camera/rgb", rr.Image(obs.rgb.payload))
        if obs.depth is not None and obs.depth.payload is not None and obs.depth.payload.ndim == 2:
            rec.log(
                "camera/depth", rr.DepthImage(obs.depth.payload, meter=obs.calibration.depth_scale)
            )
        if len(obs.points_m):
            rec.log("camera/points", rr.Points3D(obs.points_m, colors=obs.colors_rgb))
        rec.log(
            "quality/status",
            rr.TextDocument(obs.quality.status + "\n" + ", ".join(obs.quality.flags)),
        )
        if obs.sync_delta_ns is not None:
            rec.log("quality/sync_delta_ms", rr.Scalars(obs.sync_delta_ns / 1e6))

    def close(self):
        self.recording.flush()
