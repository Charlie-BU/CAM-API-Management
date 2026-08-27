#!/usr/bin/env bash

set -euo pipefail

readonly CLOUD_MATERIALS_REPOSITORY="git@github.com:Charlie-BU/cloud-materials-common.git"
readonly CONSUMER_ROOT="$(cd "${1:-.}" && pwd)"
readonly TARGET_DIRECTORY="${CONSUMER_ROOT}/cloud-materials-common"
readonly CONSUMER_GITIGNORE="${CONSUMER_ROOT}/.gitignore"
readonly IGNORE_ENTRY="/cloud-materials-common/"

if [[ ! -f "${CONSUMER_ROOT}/package.json" ]]; then
    echo "Error: ${CONSUMER_ROOT} is not a JavaScript project root (package.json is missing)." >&2
    exit 1
fi

if [[ -d "${TARGET_DIRECTORY}/.git" ]]; then
    echo "cloud-materials-common already exists; keeping the current checkout."
elif [[ -e "${TARGET_DIRECTORY}" ]]; then
    echo "Error: ${TARGET_DIRECTORY} exists but is not a Git checkout." >&2
    exit 1
else
    echo "Cloning offline @cloud-materials repository into ${TARGET_DIRECTORY} ..."
    git clone --depth 1 "${CLOUD_MATERIALS_REPOSITORY}" "${TARGET_DIRECTORY}"
fi

if [[ ! -f "${TARGET_DIRECTORY}/@cloud-materials/common/package.json" ]]; then
    echo "Error: @cloud-materials/common is missing from the cloned repository." >&2
    exit 1
fi

if [[ ! -d "${TARGET_DIRECTORY}/node_modules/.pnpm" ]]; then
    echo "Error: the offline pnpm dependency tree is missing from the cloned repository." >&2
    exit 1
fi

touch "${CONSUMER_GITIGNORE}"
if ! grep -Fqx "${IGNORE_ENTRY}" "${CONSUMER_GITIGNORE}"; then
    printf '\n%s\n' "${IGNORE_ENTRY}" >> "${CONSUMER_GITIGNORE}"
fi

echo "Offline @cloud-materials/common is ready."
echo "Package path: ${TARGET_DIRECTORY}/@cloud-materials/common"