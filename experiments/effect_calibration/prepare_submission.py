"""Preserve exact integer values while preparing a fully checked official file."""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import h5py
import numpy as np


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()


def exact_float_copy(source,destination):
    """Bound storage conversion to 1M values; never change the scored artifact."""
    if destination.exists():
        raise FileExistsError(destination)
    temporary=destination.with_suffix(".partial.h5ad")
    if temporary.exists():
        raise FileExistsError("Interrupted conversion exists; retain/audit before retry")
    with h5py.File(source,"r") as src,h5py.File(temporary,"w") as dst:
        dst.attrs.update(dict(src.attrs))
        for name in src:
            if name!="X":
                src.copy(name,dst)
        matrix=dst.create_group("X")
        matrix.attrs.update(dict(src["X"].attrs))
        src.copy("X/indices",matrix,name="indices")
        src.copy("X/indptr",matrix,name="indptr")
        original=src["X/data"]
        count=len(original)
        data=matrix.create_dataset("data",shape=(count,),maxshape=(None,),dtype="float32",
                                   chunks=(min(max(count,1),262144),),compression="lzf")
        for start in range(0,count,1_048_576):
            block=original[start:start+1_048_576]
            converted=block.astype(np.float32)
            if (not np.isfinite(block).all() or (block<0).any() or (block>1_000_000).any()
                    or not np.equal(block,np.floor(block)).all()
                    or not np.array_equal(converted.astype(block.dtype),block)):
                raise ValueError("Count conversion would change an integer or accepts invalid values")
            data[start:start+len(block)]=converted
        dtype_before=str(original.dtype)
    temporary.replace(destination)
    # Verify the on-disk conversion, including sparse row/column structure.
    with h5py.File(source,"r") as src,h5py.File(destination,"r") as dst:
        for name in ["data","indices","indptr"]:
            first,second=src[f"X/{name}"],dst[f"X/{name}"]
            if first.shape!=second.shape:
                raise ValueError("Sparse shape changed during conversion")
            for start in range(0,len(first),1_048_576):
                if not np.array_equal(first[start:start+1_048_576],second[start:start+1_048_576]):
                    raise ValueError("On-disk sparse values or structure differ")
    return {"source_sha256":sha(source),"copy_sha256":sha(destination),"stored_entries":count,
            "source_dtype":dtype_before,"copy_dtype":"float32","all_values_exact":True,
            "all_indices_and_indptr_exact":True,"chunk_values":1_048_576}


def run(args):
    from vcc import prep
    from vcc.vccfile import validate_vcc

    work=args.work.resolve()
    release=json.loads((work / "release.json").read_text())
    if release["released"] is not True:
        raise ValueError("Local submission gate has not passed")
    source=work / "predictions/official.h5ad"
    exported=json.loads(source.with_suffix(".json").read_text())
    if (exported["arm"]!=release["selected_arm"] or exported["panel"]!="abc"
            or exported["decoding_seed"]!=42 or exported["rows"]!=360000
            or exported["effects_sha256"]!=release["effects_sha256"]
            or exported["fit_sha256"]!=release["fit_sha256"]
            or exported.get("checkpoint_sha256")!=release["checkpoint_sha256"]
            or sha(source)!=exported["sha256"]):
        raise ValueError("ABC export differs from the released predictor")
    prep_sha=sha(Path(prep.__file__))
    if importlib.metadata.version("vcc-cli")!="0.1.0" or prep_sha!="4a93e7d267379a32b661f7f9bd4de6543bb372816362a2a85e6f70e437240ad3":
        raise ValueError("Native prep differs from the previously audited memory patch")
    output=work / "submission"
    output.mkdir(exist_ok=True)
    (work / "tmp").mkdir(exist_ok=True)
    converted=output / "counts-float32.h5ad"
    conversion=exact_float_copy(source,converted)
    (work / "audit/count-storage-conversion.json").write_text(json.dumps(conversion,indent=2)+"\n")
    with h5py.File(converted,"r") as handle:
        csr_bytes=sum(handle[f"X/{k}"].size*handle[f"X/{k}"].dtype.itemsize for k in ["data","indices","indptr"])
        estimate=csr_bytes+2*conversion["stored_entries"]+2_000_000_000
    available=next(int(row.split()[1])*1024 for row in Path("/proc/meminfo").read_text().splitlines() if row.startswith("MemAvailable:"))
    if estimate>available*0.9:
        raise RuntimeError("Native prep estimate leaves insufficient memory headroom; use a reviewed bounded packer")
    artifact=output / "prediction.vcc"
    vcc=str(Path(sys.executable).with_name("vcc"))
    command=[vcc,"--json","prep",str(converted),"--genes",str(args.previous / "controls/gene_names.csv"),
             "--perts",str(args.previous / "controls/pert_counts.csv"),"--output",str(artifact),
             "--require-counts","--verify-targets","--check-cell-counts","--reject-controls"]
    env=os.environ.copy()
    env["TMPDIR"]=str(work / "tmp")
    for dry_run in [True,False]:
        label="submission-dry-run" if dry_run else "submission-prep"
        resource=work / "audit" / f"{label}-resources.log"
        invocation=["/usr/bin/time","-v","-o",str(resource),*command]
        if dry_run:
            invocation.append("--dry-run")
        process=subprocess.run(invocation,env=env,capture_output=True,text=True,timeout=3600)
        (work / "logs" / f"{label}.stdout").write_text(process.stdout)
        (work / "logs" / f"{label}.stderr").write_text(process.stderr)
        if process.returncode:
            raise RuntimeError(f"Native {label} failed with exit {process.returncode}; inspect private logs")
        result=json.loads(process.stdout)
        if (result.get("n_cells")!=360000 or result.get("n_genes")!=18533
                or result.get("dry_run") is not dry_run or result.get("verified_targets") is not True
                or result.get("normalization")!="counts-preserved"
                or result.get("cells_per_context")!={"A":120000,"B":120000,"C":120000}):
            raise ValueError("Native preflight did not verify the full official contract")
        (work / "audit" / f"{label}.json").write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps({"stage":label,"complete":True}),flush=True)
    validate_vcc(str(artifact))
    receipt={"selected_arm":release["selected_arm"],"release_sha256":sha(work / "release.json"),
             "original_prediction_sha256":exported["sha256"],"converted_prediction_sha256":conversion["copy_sha256"],
             "artifact_sha256":sha(artifact),"artifact_bytes":artifact.stat().st_size,"artifact_path":str(artifact),
             "prep_source_sha256":prep_sha,"native_prep_completed":True,"matrix_count_values_changed":False,
             "estimated_prep_peak_bytes":estimate,"available_bytes_before_prep":available,
             "finished_at_unix":time.time()}
    (work / "audit/submission-preparation.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt),flush=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--previous",type=Path,required=True)
    parser.add_argument("--work",type=Path,required=True)
    run(parser.parse_args())
