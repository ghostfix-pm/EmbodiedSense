"""Download only fr1/xyz from TUM; validate and safely extract under data/."""

import argparse
import hashlib
import tarfile
import urllib.request
from pathlib import Path

URL = "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_xyz.tgz"
# SHA256 observed on the official download, 2026-10-10; not a publisher signature.
SHA256 = "a0236d97b8c30cd93b653656d2b6c293ff7c982a4130ef2a1a8beecdb124ef98"


def main():
    parser = argparse.ArgumentParser(description="Download approximately 428 MiB from TUM")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    root = args.data_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    archive = root / "fr1_xyz.tgz"
    destination = root / "rgbd_dataset_freiburg1_xyz"
    if destination.exists():
        raise FileExistsError(f"Will not overwrite existing dataset: {destination}")
    if not archive.exists():
        partial = archive.with_suffix(".tgz.part")
        print(f"Downloading ~428 MiB: {URL}", flush=True)
        with urllib.request.urlopen(URL, timeout=60) as response, partial.open("wb") as output:
            while block := response.read(1024 * 1024):
                output.write(block)
        partial.rename(archive)
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != SHA256:
        raise ValueError("Archive checksum mismatch; existing file retained for inspection")
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getmembers()
        for member in members:
            path = (root / member.name).resolve()
            if (
                not path.is_relative_to(destination)
                or member.issym()
                or member.islnk()
                or not (member.isfile() or member.isdir())
            ):
                raise ValueError(f"Unexpected archive member: {member.name}")
        tar.extractall(root, members=members, filter="data")
    print(f"Verified SHA256 {digest}\nExtracted: {destination}")


if __name__ == "__main__":
    main()
