args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 3)
source_path <- args[[1]]
output_dir <- args[[2]]
protocol_path <- args[[3]]
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
library(jsonlite)
write_report <- function(value, name) {
  write_json(value, file.path(output_dir, name), auto_unbox = TRUE, pretty = TRUE,
             digits = NA, na = "null")
}
header <- infoRDS(source_path)
write_report(list(R_version = R.version.string, serialization = header,
                  started_at = format(Sys.time(), tz = "UTC", usetz = TRUE)), "reader-start.json")
obj <- readRDS(source_path)
assays <- attr(obj, "assays", exact = TRUE)
meta <- attr(obj, "meta.data", exact = TRUE)
stopifnot(is.list(assays), is.data.frame(meta), "RNA" %in% names(assays))
rna <- assays[["RNA"]]
counts <- attr(rna, "counts", exact = TRUE)
stopifnot(!is.null(counts))
count_class <- as.character(attr(counts, "class", exact = TRUE))
stopifnot("dgCMatrix" %in% count_class)
dimensions <- attr(counts, "Dim", exact = TRUE)
axis_names <- attr(counts, "Dimnames", exact = TRUE)
values <- attr(counts, "x", exact = TRUE)
indices <- attr(counts, "i", exact = TRUE)
pointers <- attr(counts, "p", exact = TRUE)
info <- list(source_file = source_path, R_version = R.version.string,
             root_fields = names(attributes(obj)), assay_names = names(assays),
             RNA_fields = names(attributes(rna)), counts_path = "assays/RNA/counts",
             counts_class = count_class, genes = dimensions[[1]], cells = dimensions[[2]],
             stored_entries = length(values), value_type = typeof(values),
             index_type = typeof(indices), pointer_type = typeof(pointers))
write_report(info, "structure.json")
rm(obj, assays, rna)
invisible(gc())
stopifnot(length(dimensions) == 2, length(values) > 0, length(indices) == length(values),
          length(pointers) == dimensions[[2]] + 1, pointers[[1]] == 0,
          tail(pointers, 1) == length(values), all(diff(pointers) >= 0),
          length(axis_names[[1]]) == dimensions[[1]], length(axis_names[[2]]) == dimensions[[2]])
checks <- list(finite = TRUE, nonnegative = TRUE, integer = TRUE, index_range = TRUE)
explicit_zeros <- 0
maximum <- 0
nonzero_by_gene <- numeric(dimensions[[1]])
for (start in seq.int(1, length(values), by = 1000000)) {
  end <- min(length(values), start + 999999)
  block <- values[start:end]
  row_indices <- indices[start:end]
  valid_numbers <- all(is.finite(block))
  checks$finite <- checks$finite && valid_numbers
  checks$nonnegative <- checks$nonnegative && valid_numbers && all(block >= 0)
  checks$integer <- checks$integer && valid_numbers && all(block == floor(block))
  checks$index_range <- checks$index_range && all(!is.na(row_indices)) && all(row_indices >= 0 & row_indices < dimensions[[1]])
  if (!all(unlist(checks))) break
  explicit_zeros <- explicit_zeros + sum(block == 0)
  maximum <- max(maximum, max(block))
  nonzero_by_gene <- nonzero_by_gene + tabulate(row_indices[block > 0] + 1L, nbins = dimensions[[1]])
  if (start %% 100000000 == 1) cat(sprintf("checked %.0f of %.0f stored values\n", end, length(values)))
}
info$count_checks <- checks
info$fully_scanned <- all(unlist(checks))
info$explicit_zeros <- if (info$fully_scanned) explicit_zeros else NA_real_
info$maximum_stored_count <- if (info$fully_scanned) maximum else NA_real_
info$duplicate_gene_names <- sum(duplicated(axis_names[[1]]))
info$duplicate_cell_names <- sum(duplicated(axis_names[[2]]))
info$metadata_rows <- nrow(meta)
info$metadata_cell_names_same_order <- identical(axis_names[[2]], rownames(meta))
info$metadata_cell_names_same_set <- setequal(axis_names[[2]], rownames(meta))
write_report(info, "counts-audit.json")
if (!all(unlist(checks))) quit(status = 2)
library_sizes <- numeric(dimensions[[2]])
for (cell in seq_len(dimensions[[2]])) {
  low <- pointers[[cell]]
  high <- pointers[[cell + 1L]]
  if (high > low) library_sizes[[cell]] <- sum(values[(low + 1):high])
}
info$empty_cells <- sum(library_sizes == 0)
info$library_size_quantiles <- as.list(quantile(library_sizes, c(0, .25, .5, .75, 1)))
info$genes_with_nonzero_counts <- sum(nonzero_by_gene > 0)
write.table(data.frame(gene = axis_names[[1]], nonzero_entries = nonzero_by_gene),
            file.path(output_dir, "genes.tsv"), sep = "\t", row.names = FALSE, quote = FALSE)
metadata_summary <- lapply(names(meta), function(name) {
  value <- meta[[name]]
  unique_count <- length(unique(value))
  result <- list(column = name, class = class(value), missing = sum(is.na(value)), unique = unique_count)
  if (unique_count <= 200 && (is.character(value) || is.factor(value) || is.logical(value))) {
    counts_by_value <- table(as.character(value), useNA = "ifany")
    result$counts <- as.list(as.numeric(counts_by_value))
    names(result$counts) <- names(counts_by_value)
  }
  result
})
write_report(metadata_summary, "metadata-columns.json")
metadata_file <- gzfile(file.path(output_dir, "metadata.tsv.gz"), "wt")
write.table(data.frame(cell_id = rownames(meta), meta, check.names = FALSE), metadata_file,
            sep = "\t", row.names = FALSE, quote = TRUE, na = "")
close(metadata_file)
panel <- fromJSON(protocol_path)
info$official_genes_measured <- sum(panel$official_genes %in% axis_names[[1]])
info$h1_genes_measured <- sum(panel$h1_genes %in% axis_names[[1]])
info$official_genes_nonzero <- sum(panel$official_genes %in% axis_names[[1]][nonzero_by_gene > 0])
info$h1_genes_nonzero <- sum(panel$h1_genes %in% axis_names[[1]][nonzero_by_gene > 0])
info$interpretation <- "RNA counts slot with finite nonnegative integer values; raw-UMI interpretation also relies on author provenance. Metadata mappings remain explicit downstream work."
info$finished_at <- format(Sys.time(), tz = "UTC", usetz = TRUE)
write_report(info, "counts-audit.json")
cat(toJSON(info, auto_unbox = TRUE, digits = NA), "\n")
