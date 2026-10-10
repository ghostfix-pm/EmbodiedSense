# EmbodiedSense contributor instructions

- Current scope is the RGB-D MVP 1; see README and docs/roadmap.md.
- Use commands and APIs. Do not manipulate the user's screen or launch viewers automatically.
- Prefer project/data/output/environment/cache storage on D: for this Windows machine.
- Keep the core independent of Rerun, ROS and GPU dependencies.
- Preserve source timestamps, units, calibration IDs and raw files.
- Synthetic samples and estimated values must be labelled explicitly.
- Run relevant numeric and integration tests, ruff check and format before committing.
- Do not commit data/, outputs/, environments, credentials or personal machine paths.
- Report actual measured results and clearly identify unimplemented modules.
