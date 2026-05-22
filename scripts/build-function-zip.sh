#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FUNCTION_DIR="${ROOT_DIR}/function"
PACKAGE_DIR="${ROOT_DIR}/package"
BUILD_DIR="${ROOT_DIR}/.build/function-package"
PACKAGE_ARCHIVE_SCRIPT="${ROOT_DIR}/scripts/package_archive.py"

AWS_BUILD_DIR="${BUILD_DIR}/aws-lambda"
AWS_DEPENDENCY_DIR="${AWS_BUILD_DIR}/_deps"
AWS_ZIP="${PACKAGE_DIR}/aws-lambda.zip"

GCP_BUILD_DIR="${BUILD_DIR}/gcp-cloud-function"
GCP_VENDOR_DIR="${GCP_BUILD_DIR}/_vendor"
GCP_ZIP="${PACKAGE_DIR}/gcp-cloud-function.zip"

PYTHON_BIN="${PYTHON_BIN:-}"
AWS_PYTHON_RUNTIME="${AWS_PYTHON_RUNTIME:-${PYTHON_RUNTIME:-python3.13}}"
AWS_PYTHON_VERSION="${AWS_PYTHON_RUNTIME#python}"
GCP_PYTHON_RUNTIME="${GCP_PYTHON_RUNTIME:-python3.13}"
GCP_PYTHON_VERSION="${GCP_PYTHON_RUNTIME#python}"
LAMBDA_ARCHITECTURE="${LAMBDA_ARCHITECTURE:-arm64}"

if [[ -z "${PYTHON_BIN}" ]]; then
  if command -v "${AWS_PYTHON_RUNTIME}" >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v "${AWS_PYTHON_RUNTIME}")"
  else
    PYTHON_BIN="python3"
  fi
fi

case "${LAMBDA_ARCHITECTURE}" in
  arm64)
    AWS_PIP_PLATFORM="manylinux_2_28_aarch64"
    AWS_PIP_PLATFORM_COMPAT="manylinux2014_aarch64"
    ;;
  x86_64)
    AWS_PIP_PLATFORM="manylinux_2_28_x86_64"
    AWS_PIP_PLATFORM_COMPAT="manylinux2014_x86_64"
    ;;
  *)
    echo "Unsupported LAMBDA_ARCHITECTURE=${LAMBDA_ARCHITECTURE}; use arm64 or x86_64." >&2
    exit 1
    ;;
esac

if [[ ! -f "${FUNCTION_DIR}/requirements.txt" ]]; then
  echo "Missing ${FUNCTION_DIR}/requirements.txt" >&2
  exit 1
fi

if [[ ! -f "${PACKAGE_ARCHIVE_SCRIPT}" ]]; then
  echo "Missing ${PACKAGE_ARCHIVE_SCRIPT}" >&2
  exit 1
fi

if [[ ! "${AWS_PYTHON_RUNTIME}" =~ ^python3\.(12|13)$ ]]; then
  echo "Unsupported AWS_PYTHON_RUNTIME=${AWS_PYTHON_RUNTIME}; use python3.12 or python3.13." >&2
  exit 1
fi

if [[ "${GCP_PYTHON_RUNTIME}" != "python3.13" ]]; then
  echo "Unsupported GCP_PYTHON_RUNTIME=${GCP_PYTHON_RUNTIME}; terraform-gcp deploys python313." >&2
  exit 1
fi

copy_function_source() {
  local target_dir="$1"

  mkdir -p "${target_dir}"
  cp "${FUNCTION_DIR}"/*.py "${target_dir}/"
  cp -R "${FUNCTION_DIR}/extractor" "${target_dir}/extractor"
  find "${target_dir}" -type d -name "__pycache__" -prune -exec rm -rf {} +
  find "${target_dir}" -type f -name "*.pyc" -delete
}

echo "Cleaning package workspace"
rm -rf "${BUILD_DIR}" "${AWS_ZIP}" "${GCP_ZIP}"
mkdir -p "${AWS_DEPENDENCY_DIR}" "${GCP_VENDOR_DIR}" "${PACKAGE_DIR}"

echo "AWS package target: ${AWS_PYTHON_RUNTIME} ${LAMBDA_ARCHITECTURE}"
echo "Installing AWS Lambda dependencies into ${AWS_DEPENDENCY_DIR}"
"${PYTHON_BIN}" -m pip install \
  --platform="${AWS_PIP_PLATFORM}" \
  --platform="${AWS_PIP_PLATFORM_COMPAT}" \
  --only-binary=:all: \
  --python-version="${AWS_PYTHON_VERSION}" \
  --implementation=cp \
  --target="${AWS_DEPENDENCY_DIR}" \
  --requirement="${FUNCTION_DIR}/requirements.txt"

copy_function_source "${AWS_BUILD_DIR}"
cp "${FUNCTION_DIR}/requirements.txt" "${AWS_BUILD_DIR}/requirements.txt"

echo "GCP package target: ${GCP_PYTHON_RUNTIME} x86_64"
echo "Downloading GCP copied dependencies into ${GCP_VENDOR_DIR}"
"${PYTHON_BIN}" -m pip download \
  --platform="manylinux_2_28_x86_64" \
  --platform="manylinux2014_x86_64" \
  --only-binary=:all: \
  --python-version="${GCP_PYTHON_VERSION}" \
  --implementation=cp \
  --dest="${GCP_VENDOR_DIR}" \
  --requirement="${FUNCTION_DIR}/requirements.txt"

copy_function_source "${GCP_BUILD_DIR}"
cp "${FUNCTION_DIR}/requirements.txt" "${GCP_BUILD_DIR}/requirements.txt"

find "${BUILD_DIR}" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "${BUILD_DIR}" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete

echo "Creating ${AWS_ZIP}"
"${PYTHON_BIN}" "${PACKAGE_ARCHIVE_SCRIPT}" "${AWS_BUILD_DIR}" "${AWS_ZIP}"

echo "Creating ${GCP_ZIP}"
"${PYTHON_BIN}" "${PACKAGE_ARCHIVE_SCRIPT}" "${GCP_BUILD_DIR}" "${GCP_ZIP}"

echo "Built packages:"
ls -lh "${AWS_ZIP}" "${GCP_ZIP}"
