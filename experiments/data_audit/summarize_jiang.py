"""Audit explicit author metadata and coverage without loading the RNA matrix."""

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import json
from pathlib import Path

import numpy as np


def run(args):
    protocol=json.loads((args.previous / "protocol.json").read_text())
    records=Counter()
    guides=defaultdict(set)
    targets=set()
    library_groups=Counter()
    columns=json.loads((args.audit / "metadata-columns.json").read_text())
    observed_columns={v["column"]:Counter() for v in columns if "counts" in v}
    with gzip.open(args.audit / "metadata.tsv.gz","rt") as stream:
        reader=csv.DictReader(stream,delimiter="\t",escapechar="\\")
        required={"cell_type","pathway","Batch_info","orig.ident","sample_ID","gene","guide"}
        if not required.issubset(reader.fieldnames):
            raise ValueError("Author metadata schema changed")
        for row in reader:
            key=tuple(row[k] for k in ["cell_type","pathway","Batch_info","orig.ident","gene"])
            records[key]+=1
            library_groups[(*key[:4],row["sample_ID"],row["gene"])]+=1
            targets.add(row["gene"])
            guides[row["gene"]].add(row["guide"])
            for field,counter in observed_columns.items():
                counter[row[field]]+=1
    if guides["NT"]!={f"NTg{i}" for i in range(1,15)}:
        raise ValueError("NT control labels differ from the inspected author metadata")
    targets.remove("NT")
    counts=json.loads((args.audit / "counts-audit.json").read_text())
    if sum(records.values())!=counts["cells"]:
        raise ValueError("Metadata and matrix row totals differ")
    for item in columns:
        if item["column"] not in observed_columns:
            continue
        counter=observed_columns[item["column"]]
        if counter.get("",0)!=item["missing"] or sum(counter.values())!=counts["cells"]:
            raise ValueError("Metadata missing-value representation requires manual review")
        corrected=dict(sorted(counter.items()))
        if "" in corrected:
            if "__MISSING__" in corrected:
                raise ValueError("Missing-value sentinel collides with a real label")
            corrected["__MISSING__"]=corrected.pop("")
        item["counts"]=corrected
    (args.audit / "metadata-columns-reviewed.json").write_text(json.dumps(columns,indent=2)+"\n")
    grouped=defaultdict(Counter)
    for key,n in records.items():
        grouped[key[:4]][key[4]]+=n
    strict=defaultdict(Counter)
    for key,n in library_groups.items():
        strict[key[:5]][key[5]]+=n
    with (args.audit / "conditions.csv").open("w") as stream:
        writer=csv.writer(stream)
        writer.writerow(["cell_type","pathway","Batch_info","orig.ident","gene","cells","matched_NT_cells"])
        for key,n in sorted(records.items()):
            writer.writerow([*key,n,grouped[key[:4]]["NT"]])
    with (args.audit / "strata.csv").open("w") as stream:
        writer=csv.writer(stream)
        writer.writerow(["cell_type","pathway","Batch_info","orig.ident","cells","NT_cells","perturbed_targets"])
        for key,group in sorted(grouped.items()):
            writer.writerow([*key,sum(group.values()),group["NT"],len(set(group)-{"NT"})])
    with (args.audit / "genes.tsv").open() as stream:
        gene_rows=list(csv.DictReader(stream,delimiter="\t"))
    genes={r["gene"] for r in gene_rows}
    nonzero={r["gene"] for r in gene_rows if float(r["nonzero_entries"])>0}
    with np.load(args.campaign / "effects.npz") as archive:
        old_mask=archive["masks"].any(0)
    old={g for g,measured in zip(protocol["genes"],old_mask) if measured}
    official=set(protocol["official_genes"])
    report={"cells":sum(records.values()),"NT_cells":sum(v["NT"] for v in grouped.values()),
            "cell_lines":sorted({k[0] for k in grouped}),"pathway_labels":sorted({k[1] for k in grouped}),
            "replicate_labels":sorted({k[2] for k in grouped}),"perturbed_targets":len(targets),
            "target_symbols":sorted(targets),"NT_gene_label":"NT","NT_guides":sorted(guides["NT"]),
            "metadata_mapping":{"cell_line":"cell_type","pathway_annotation":"pathway","replicate":"Batch_info","author_sample":"orig.ident","library_annotation":"sample_ID","target":"gene","guide":"guide"},
            "stimulus_boundary":"All rows have pathway TGFB1 and sample labels ending TGFB1; no separate cell-level stimulus/dose/time field. Exposure follows author methods, not an inferred unstimulated state.",
            "batch_boundary":"Preserve both orig.ident and sample_ID; do not infer that either is safely ignorable without author processing provenance.",
            "primary_strata":len(grouped),"primary_strata_without_NT":sum(v["NT"]==0 for v in grouped.values()),
            "minimum_NT_per_primary_stratum":min(v["NT"] for v in grouped.values()),
            "library_strata":len(strict),"library_strata_without_NT":sum(v["NT"]==0 for v in strict.values()),
            "minimum_NT_per_library_stratum":min(v["NT"] for v in strict.values()),
            "library_strata_with_at_least_16_NT":sum(v["NT"]>=16 for v in strict.values()),
            "library_strata_without_NT_details":[{"cell_type":k[0],"pathway":k[1],"Batch_info":k[2],"orig.ident":k[3],"sample_ID":k[4],"cells":sum(v.values())} for k,v in sorted(strict.items()) if v["NT"]==0],
            "official_target_overlap":sorted(targets & set(protocol["official_targets"])),
            "public_h1_target_overlap":sorted(targets & set(protocol["h1_targets"])),
            "official_genes_before":len(old & official),"official_genes_in_jiang":len(genes & official),
            "official_genes_in_union":len((old|genes)&official),
            "new_official_genes_measured":sorted((genes & official)-old),
            "new_official_genes_nonzero":sorted((nonzero & official)-old),
            "use":"asset/metadata audit only; no change to current frozen training or submitted predictor"}
    (args.audit / "metadata-coverage.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in {"new_official_genes_measured","new_official_genes_nonzero","target_symbols","metadata_mapping"}}),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--previous",type=Path,required=True)
    parser.add_argument("--campaign",type=Path,required=True)
    parser.add_argument("--audit",type=Path,required=True)
    run(parser.parse_args())
