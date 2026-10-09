#!/usr/bin/env bash
set -euo pipefail

cd "${0%/*}/.."
repo_dir=$PWD
stage_dir=$(mktemp -d)
trap cleanup EXIT

cleanup() {
    rm -rf "$stage_dir"
}

mkdir -p "$repo_dir/dist" "$stage_dir/osc_score_bridge"
cp "$repo_dir"/*.py "$repo_dir/README.md" "$repo_dir/LICENSE" "$stage_dir/osc_score_bridge/"
rm -f "$repo_dir/dist/osc_score_bridge-1.2.0.zip"
(
    cd "$stage_dir"
    zip -qr "$repo_dir/dist/osc_score_bridge-1.2.0.zip" osc_score_bridge
)
echo "$repo_dir/dist/osc_score_bridge-1.2.0.zip"
