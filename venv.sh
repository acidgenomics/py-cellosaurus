#!/usr/bin/env bash
set -Eeuo pipefail

install_venv() {
    if [[ ! -d '.venv' ]]
    then
        local python_version
        [[ -f '.python-version' ]] || return 1
        IFS= read -r python_version < '.python-version'
        if ! uv python find "$python_version" > /dev/null 2>&1
        then
            echo "Error: Python ${python_version} is not installed." >&2
            echo "Install Python ${python_version} and ensure it is on PATH." >&2
            return 1
        fi
        uv venv .venv \
            --no-python-downloads \
            --python "$python_version"
    fi
    # shellcheck source=/dev/null
    source '.venv/bin/activate'
    rm -f uv.lock
    uv pip install \
        --all-extras \
        --editable . \
        --only-binary=':all:' \
        --requirements 'pyproject.toml' \
        --upgrade
    uv lock
    uv export \
        --format requirements-txt \
        --output-file requirements.txt \
        --all-extras \
        --no-hashes \
        --no-emit-project \
        --frozen \
        > /dev/null
    uv pip list
    return 0
}

main() {
    local -a cache_dirs
    if ! command -v 'uv' &> /dev/null
    then
        echo 'uv is required.'
        return 1
    fi
    cache_dirs=(
        'build'
    )
    rm -fr "${cache_dirs[@]}"
    install_venv
    rm -fr "${cache_dirs[@]}"
    return 0
}

main "$@"
