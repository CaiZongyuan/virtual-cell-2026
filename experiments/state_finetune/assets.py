"""Fetch pinned State/VC assets; large files stay outside the source tree."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import urllib.request
import zipfile

REVISION = "bb6a9562cbbf1fd152df14cc53b4cc7517c77175"
PARENT = f"https://huggingface.co/arcinstitute/ST-HVG-Replogle/resolve/{REVISION}/zeroshot/jurkat"
SUPPORT = "https://storage.googleapis.com/vcc_data_prod/datasets/state/competition_support_set.zip"
H1 = "https://storage.googleapis.com/arc-institute-virtual-cell-atlas/virtual-cell-challenge/2025"
DATA_FILES = {
    "gwps": "ReplogleWeissman2022_K562_gwps.h5ad",
    "k562": "ReplogleWeissman2022_K562_essential.h5ad",
    "rpe1": "ReplogleWeissman2022_rpe1.h5ad",
    "hepg2": "NadigOConner2024_hepg2.h5ad",
    "jurkat": "NadigOConner2024_jurkat.h5ad",
}


def ranged_download(url, partial: Path, size, workers=4):
    """Resume a sequential prefix, then fetch four disjoint validated ranges."""
    chunk_size = 128 << 20
    journal = partial.with_name(partial.name + ".ranges.json")
    count = (size + chunk_size - 1) // chunk_size
    if journal.exists():
        state = json.loads(journal.read_text())
        if state["url"] != url or state["size"] != size or state["chunk_size"] != chunk_size:
            raise ValueError("Range download journal does not match requested asset")
        complete = set(state["complete"])
    else:
        prefix = partial.stat().st_size if partial.exists() else 0
        if prefix > size:
            raise ValueError("Partial asset exceeds expected size")
        complete = set(range(prefix // chunk_size))
        state = {"url": url, "size": size, "chunk_size": chunk_size, "complete": sorted(complete)}
        journal.write_text(json.dumps(state))
    descriptor = os.open(partial, os.O_RDWR | os.O_CREAT, 0o600)
    os.ftruncate(descriptor, size)
    lock = threading.Lock()

    def fetch(index):
        start = index * chunk_size
        end = min(size, start + chunk_size) - 1
        for attempt in range(5):
            try:
                request = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
                with urllib.request.urlopen(request, timeout=90) as response:
                    if response.status != 206 or response.headers.get("Content-Range") != f"bytes {start}-{end}/{size}":
                        raise ValueError("Source did not honor requested byte range")
                    position = start
                    while position <= end:
                        data = response.read(min(1 << 20, end + 1 - position))
                        if not data:
                            raise OSError("Truncated download range")
                        written = 0
                        while written < len(data):
                            written += os.pwrite(descriptor, data[written:], position + written)
                        position += len(data)
                with lock:
                    complete.add(index)
                    state["complete"] = sorted(complete)
                    pending = journal.with_suffix(".tmp")
                    pending.write_text(json.dumps(state))
                    pending.replace(journal)
                    print(json.dumps({"asset": partial.name, "parts": len(complete), "total_parts": count}), flush=True)
                return
            except OSError:
                if attempt == 4:
                    raise
                time.sleep(2 + attempt)

    try:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for future in as_completed([executor.submit(fetch, index) for index in range(count) if index not in complete]):
                future.result()
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def digest(path: Path, algorithm="sha256"):
    value = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def download(url: str, path: Path, expected_hash=None, algorithm="sha256", size=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    receipt = path.with_name(path.name + ".receipt.json")
    if path.exists():
        if size is not None and path.stat().st_size != size:
            raise ValueError(f"Existing asset has wrong size: {path}")
        if expected_hash and receipt.exists():
            previous = json.loads(receipt.read_text())
            if (previous.get(algorithm) == expected_hash and previous.get("url") == url
                    and previous.get("bytes") == path.stat().st_size
                    and path.stat().st_mtime_ns <= receipt.stat().st_mtime_ns):
                print(json.dumps({"asset": str(path), "state": "unchanged-verified-asset", algorithm: expected_hash}), flush=True)
                return
        actual = digest(path, algorithm)
        if expected_hash and actual != expected_hash:
            raise ValueError(f"Existing asset checksum mismatch: {path}")
        print(json.dumps({"asset": str(path), "state": "verified-existing", algorithm: actual}), flush=True)
        return
    partial = path.with_name(path.name + ".part")
    print(json.dumps({"asset": str(path), "state": "downloading", "expected_bytes": size}), flush=True)
    if size and size > 500_000_000 and "zenodo.org/" in url:
        ranged_download(url, partial, size)
    else:
        subprocess.run([
            "curl", "--fail", "--location", "--retry", "5", "--retry-delay", "3",
            "--connect-timeout", "30", "--continue-at", "-", "--output", str(partial), url,
        ], check=True)
    if size is not None and partial.stat().st_size != size:
        raise ValueError(f"Downloaded asset has wrong size: {partial}")
    actual = digest(partial, algorithm)
    if expected_hash and actual != expected_hash:
        raise ValueError(f"Downloaded asset checksum mismatch: {partial}")
    partial.rename(path)
    receipt.write_text(json.dumps({
        "url": url, "bytes": path.stat().st_size, algorithm: actual,
        "verified_at_unix": time.time(), "expected_hash_verified": bool(expected_hash),
    }, indent=2) + "\n")
    print(json.dumps({"asset": str(path), "state": "ready", algorithm: actual}), flush=True)


class RemoteZip(io.RawIOBase):
    """Bounded HTTP Range reader. A server ignoring Range is rejected."""

    def __init__(self, url, size):
        self.url, self.size, self.position = url, size, 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        base = {0: 0, 1: self.position, 2: self.size}[whence]
        self.position = base + offset
        if self.position < 0:
            raise ValueError("Negative seek")
        return self.position

    def read(self, amount=-1):
        amount = self.size - self.position if amount < 0 else min(amount, self.size - self.position)
        if amount <= 0:
            return b""
        if amount > 16 << 20:
            raise ValueError("Range read exceeds 16 MiB bound")
        start = self.position
        request = urllib.request.Request(self.url, headers={"Range": f"bytes={start}-{start + amount - 1}"})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    if response.status != 206 or not response.headers.get("Content-Range", "").startswith(f"bytes {start}-"):
                        raise ValueError("Server did not honor requested range")
                    data = response.read(amount)
                if len(data) != amount:
                    raise OSError("Truncated range response")
                self.position += len(data)
                return data
            except OSError:
                if attempt == 3:
                    raise
                time.sleep(2)


def features(root: Path):
    path = root / "assets" / "ESM2_pert_features.pt"
    receipt = path.with_name(path.name + ".receipt.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and receipt.exists():
        expected = json.loads(receipt.read_text())
        if digest(path) != expected["sha256"]:
            raise ValueError("Feature checksum mismatch")
        print("Feature asset verified", flush=True)
        return
    partial = path.with_name(path.name + ".part")
    with zipfile.ZipFile(RemoteZip(SUPPORT, 8_716_992_349)) as archive:
        info = archive.getinfo("competition_support_set/ESM2_pert_features.pt")
        total, last_report = 0, time.monotonic()
        with archive.open(info) as source, partial.open("wb") as target:
            while chunk := source.read(4 << 20):
                target.write(chunk)
                total += len(chunk)
                if time.monotonic() - last_report > 15:
                    print(json.dumps({"asset": "ESM2", "bytes": total, "total": info.file_size}), flush=True)
                    last_report = time.monotonic()
        if total != info.file_size:
            raise ValueError("Incomplete feature extraction")
    partial.rename(path)
    receipt.write_text(json.dumps({
        "url": SUPPORT, "member": info.filename, "bytes": total,
        "crc32": f"{info.CRC:08x}", "sha256": digest(path),
        "zip_crc_verified": True,
    }, indent=2) + "\n")
    print("Feature asset ready", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("names", nargs="+", choices=["parent", "features", "h1", *DATA_FILES])
    args = parser.parse_args()
    for name in args.names:
        if name == "parent":
            folder = args.root / "assets" / "parent"
            download(PARENT + "/checkpoints/best.ckpt", folder / "best.ckpt",
                     "6fa4fe9a1c8a267d88d519d335e367b80594db64d2005abf1407260afccbfa6b", size=471_699_039)
            download(PARENT + "/pert_onehot_map.pt", folder / "pert_onehot_map.pt",
                     "f5621cab243a5135014af3867f63f8bf75cff19aee06d0f29a1bdecd2dbf47d0", size=16_746_593)
            for relative in ["config.yaml", "var_dims.pkl", "version_0/hparams.yaml"]:
                download(PARENT + "/" + relative, folder / Path(relative).name)
        elif name == "features":
            features(args.root)
        elif name == "h1":
            download(H1 + "/train/adata_Training.h5ad", args.root / "raw" / "h1.h5ad",
                     "a09977104fefb622368ca74b50c9d3c1e891733e6c83db07acfca49b0219c02b", size=15_482_497_461)
            download(H1 + "/gene_names.csv", args.root / "assets" / "h1_gene_names.csv")
            download(H1 + "/train/pert_counts_Training.csv", args.root / "assets" / "h1_pert_counts.csv")
        else:
            with urllib.request.urlopen("https://zenodo.org/api/records/13350497", timeout=30) as response:
                record = json.load(response)
            entry = next(item for item in record["files"] if item["key"] == DATA_FILES[name])
            algorithm, expected = entry["checksum"].split(":", 1)
            download(f"https://zenodo.org/records/13350497/files/{entry['key']}?download=1",
                     args.root / "raw" / f"{name}.h5ad", expected, algorithm, entry["size"])


if __name__ == "__main__":
    main()
