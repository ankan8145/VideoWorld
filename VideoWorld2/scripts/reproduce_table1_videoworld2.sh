#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

RUN_WARMUP=0
RUN_TRAIN=0
RUN_LATENT=0
RUN_INFER=0

usage() {
  cat <<'EOF'
Usage:
  bash scripts/reproduce_table1_videoworld2.sh [options]

Options:
  --project-root PATH   Override project root (default: auto-detected VideoWorld2 root)
  --run-all             Run warmup + train + latent-codes + inference
  --run-warmup          Run scripts/train_dldm_warmup.sh
  --run-train           Run scripts/train_dldm.sh
  --run-latent          Run scripts/inference_dldm_codes.sh
  --run-infer           Run scripts/test.sh
  -h, --help            Show this help

Notes:
  - This script orchestrates VideoWorld2 stages used for Table-1 style reproduction.
  - Full baseline reproduction still requires external baseline repos and evaluation rubric.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root)
      PROJECT_ROOT="$2"
      shift 2
      ;;
    --run-all)
      RUN_WARMUP=1
      RUN_TRAIN=1
      RUN_LATENT=1
      RUN_INFER=1
      shift
      ;;
    --run-warmup)
      RUN_WARMUP=1
      shift
      ;;
    --run-train)
      RUN_TRAIN=1
      shift
      ;;
    --run-latent)
      RUN_LATENT=1
      shift
      ;;
    --run-infer)
      RUN_INFER=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "$RUN_WARMUP" -eq 0 && "$RUN_TRAIN" -eq 0 && "$RUN_LATENT" -eq 0 && "$RUN_INFER" -eq 0 ]]; then
  echo "No stage selected. Use --run-all or one/more stage flags." >&2
  usage
  exit 1
fi

cd "$PROJECT_ROOT"

check_file() {
  local p="$1"
  if [[ ! -f "$p" ]]; then
    echo "Missing file: $p" >&2
    exit 1
  fi
}

check_dir() {
  local p="$1"
  if [[ ! -d "$p" ]]; then
    echo "Missing directory: $p" >&2
    exit 1
  fi
}

if [[ "$RUN_WARMUP" -eq 1 || "$RUN_TRAIN" -eq 1 || "$RUN_LATENT" -eq 1 ]]; then
  check_dir "datasets/Video-CraftBench/Paper_and_Block_clips"
  check_dir "datasets/openx_untar"
  check_file "datasets/openx_videocraft_cache.json"
  check_file "datasets/openx_videocraft_meta.json"
fi

if [[ "$RUN_INFER" -eq 1 ]]; then
  check_file "checkpoints/VideoWorld2_dLDM_2B/VideoWorld2_dLDM_DiT.pth"
  check_file "checkpoints/VideoWorld2_dLDM_2B/VideoWorld2_dLDM_VAE.pt"
  check_file "checkpoints/VideoWorld2_dLDM_2B/VideoCraft-dLDM-codes.pt"
fi

if [[ "$RUN_WARMUP" -eq 1 ]]; then
  echo "[Stage] warmup training"
  bash scripts/train_dldm_warmup.sh
fi

if [[ "$RUN_TRAIN" -eq 1 ]]; then
  echo "[Stage] main dLDM training"
  bash scripts/train_dldm.sh
fi

if [[ "$RUN_LATENT" -eq 1 ]]; then
  echo "[Stage] latent-code inference"
  bash scripts/inference_dldm_codes.sh
fi

if [[ "$RUN_INFER" -eq 1 ]]; then
  echo "[Stage] benchmark inference"
  bash scripts/test.sh
  echo "Inference output expected under: $PROJECT_ROOT/infer_output"
fi

echo "Done."

