#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/mineru-pdf-to-markdown.sh INPUT.pdf [OUTPUT_DIR]

Convert a local PDF with MinerU's precise API. The default output directory is
next to the PDF and uses the PDF basename. MINERU_KEY is loaded from the
repository's .env file unless MINERU_ENV_FILE points elsewhere.
EOF
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage >&2
  exit 2
fi

for command_name in curl node unzip; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing required command: $command_name" >&2
    exit 1
  fi
done

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "$script_dir/.." && pwd)
input_pdf=$1
input_name=$(basename -- "$input_pdf")
stem=${input_name%.*}
output_dir=${2:-${input_pdf%.*}}

if [[ ! -f $input_pdf ]]; then
  echo "Input PDF does not exist: $input_pdf" >&2
  exit 1
fi

case "$input_name" in
  *.pdf | *.PDF) ;;
  *)
    echo "Input must be a PDF: $input_pdf" >&2
    exit 1
    ;;
esac

if [[ -e $output_dir ]]; then
  echo "Output path already exists; refusing to overwrite it: $output_dir" >&2
  exit 1
fi

env_file=${MINERU_ENV_FILE:-$repo_root/.env}
if [[ ! -f $env_file ]]; then
  echo "Environment file not found: $env_file" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$env_file"
set +a

if [[ -z ${MINERU_KEY:-} ]]; then
  echo "MINERU_KEY is missing from $env_file" >&2
  exit 1
fi

model_version=${MINERU_MODEL_VERSION:-vlm}
poll_interval=${MINERU_POLL_INTERVAL_SECONDS:-5}
max_poll_attempts=${MINERU_MAX_POLL_ATTEMPTS:-120}

case "$model_version" in
  pipeline | vlm) ;;
  *)
    echo "MINERU_MODEL_VERSION must be pipeline or vlm for PDF input" >&2
    exit 1
    ;;
esac

if [[ ! $poll_interval =~ ^[1-9][0-9]*$ || ! $max_poll_attempts =~ ^[1-9][0-9]*$ ]]; then
  echo "MinerU polling settings must be positive integers" >&2
  exit 1
fi

api_host=mineru.net
api_base=https://mineru.net/api/v4
doh_host=${MINERU_DOH_HOST:-dns.alidns.com}
doh_ip=${MINERU_DOH_IP:-223.5.5.5}

without_proxy() {
  env \
    -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u NO_PROXY \
    -u http_proxy -u https_proxy -u all_proxy -u no_proxy \
    "$@"
}

resolve_ipv4() {
  local hostname=$1
  local response

  response=$(
    without_proxy curl --noproxy '*' -4 -fsS \
      --resolve "$doh_host:443:$doh_ip" \
      "https://$doh_host/resolve?name=$hostname&type=A"
  )

  DNS_RESPONSE=$response node -e '
    const result = JSON.parse(process.env.DNS_RESPONSE);
    const address = (result.Answer || []).find((answer) => answer.type === 1)?.data;
    if (!address) process.exit(1);
    process.stdout.write(address);
  '
}

direct_curl() {
  local hostname=$1
  local address
  shift
  address=$(resolve_ipv4 "$hostname")
  without_proxy curl --noproxy '*' -4 --resolve "$hostname:443:$address" "$@"
}

url_hostname() {
  URL_VALUE=$1 node -e 'process.stdout.write(new URL(process.env.URL_VALUE).hostname)'
}

tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/mineru-pdf.XXXXXX")
cleanup() {
  rm -rf -- "$tmp_dir"
}
trap cleanup EXIT

create_response=$tmp_dir/create.json
status_response=$tmp_dir/status.json
result_zip=$tmp_dir/result.zip
extracted_dir=$tmp_dir/extracted
image_manifest=$tmp_dir/referenced-images.txt

payload=$(
  INPUT_NAME=$input_name DATA_ID=$stem MODEL_VERSION=$model_version node -e '
    process.stdout.write(JSON.stringify({
      files: [{name: process.env.INPUT_NAME, data_id: process.env.DATA_ID}],
      model_version: process.env.MODEL_VERSION,
    }));
  '
)

echo "Creating MinerU $model_version task for $input_name"
direct_curl "$api_host" -fsS --request POST "$api_base/file-urls/batch" \
  --header "Authorization: Bearer $MINERU_KEY" \
  --header 'Content-Type: application/json' \
  --data "$payload" \
  --output "$create_response"

CREATE_RESPONSE=$create_response node -e '
  const fs = require("fs");
  const result = JSON.parse(fs.readFileSync(process.env.CREATE_RESPONSE, "utf8"));
  if (result.code !== 0 || typeof result.data?.batch_id !== "string" || result.data?.file_urls?.length !== 1) {
    console.error(`MinerU task creation failed: ${result.msg || "invalid response"}`);
    process.exit(1);
  }
'

batch_id=$(CREATE_RESPONSE=$create_response node -e '
  const fs = require("fs");
  const result = JSON.parse(fs.readFileSync(process.env.CREATE_RESPONSE, "utf8"));
  process.stdout.write(result.data.batch_id);
')
upload_url=$(CREATE_RESPONSE=$create_response node -e '
  const fs = require("fs");
  const result = JSON.parse(fs.readFileSync(process.env.CREATE_RESPONSE, "utf8"));
  process.stdout.write(result.data.file_urls[0]);
')
upload_host=$(url_hostname "$upload_url")

echo "Uploading PDF directly to MinerU storage"
direct_curl "$upload_host" -fsS --request PUT --upload-file "$input_pdf" "$upload_url"

state=unknown
for ((attempt = 1; attempt <= max_poll_attempts; attempt++)); do
  direct_curl "$api_host" -fsS --request GET "$api_base/extract-results/batch/$batch_id" \
    --header "Authorization: Bearer $MINERU_KEY" \
    --output "$status_response"

  state=$(STATUS_RESPONSE=$status_response node -e '
    const fs = require("fs");
    const result = JSON.parse(fs.readFileSync(process.env.STATUS_RESPONSE, "utf8"));
    if (result.code !== 0 || !result.data?.extract_result?.[0]) {
      console.error(`MinerU status request failed: ${result.msg || "invalid response"}`);
      process.exit(1);
    }
    process.stdout.write(result.data.extract_result[0].state || "unknown");
  ')

  echo "MinerU state: $state ($attempt/$max_poll_attempts)"
  if [[ $state == done ]]; then
    break
  fi
  if [[ $state == failed ]]; then
    STATUS_RESPONSE=$status_response node -e '
      const fs = require("fs");
      const result = JSON.parse(fs.readFileSync(process.env.STATUS_RESPONSE, "utf8"));
      console.error(result.data.extract_result[0].err_msg || "MinerU parsing failed");
    '
    exit 1
  fi
  sleep "$poll_interval"
done

if [[ $state != done ]]; then
  echo "MinerU task did not finish within the configured polling window" >&2
  exit 1
fi

zip_url=$(STATUS_RESPONSE=$status_response node -e '
  const fs = require("fs");
  const result = JSON.parse(fs.readFileSync(process.env.STATUS_RESPONSE, "utf8"));
  const url = result.data.extract_result[0].full_zip_url;
  if (!url) process.exit(1);
  process.stdout.write(url);
')
zip_host=$(url_hostname "$zip_url")

echo "Downloading MinerU result"
direct_curl "$zip_host" -fsS "$zip_url" --output "$result_zip"
mkdir -p "$extracted_dir"
unzip -q "$result_zip" full.md 'images/*' -d "$extracted_dir"

if [[ ! -s $extracted_dir/full.md ]]; then
  echo "MinerU result did not contain a non-empty full.md" >&2
  exit 1
fi

mkdir -p "$output_dir"
cp "$extracted_dir/full.md" "$output_dir/$stem.md"

MARKDOWN_PATH=$extracted_dir/full.md node -e '
  const fs = require("fs");
  const markdown = fs.readFileSync(process.env.MARKDOWN_PATH, "utf8");
  const paths = new Set();
  for (const match of markdown.matchAll(/!\[[^\]]*\]\((images\/[^)]+)\)/g)) {
    paths.add(match[1]);
  }
  process.stdout.write([...paths].join("\n"));
' > "$image_manifest"

while IFS= read -r relative_image; do
  [[ -z $relative_image ]] && continue
  source_image=$extracted_dir/$relative_image
  destination_image=$output_dir/$relative_image
  if [[ ! -f $source_image ]]; then
    echo "Markdown references a missing image: $relative_image" >&2
    exit 1
  fi
  mkdir -p "$(dirname -- "$destination_image")"
  cp "$source_image" "$destination_image"
done < "$image_manifest"

echo "Markdown written to $output_dir/$stem.md"
echo "Treat generated Markdown as a reading copy; verify quotations against the PDF."
