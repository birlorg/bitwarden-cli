#!/bin/bash
cd ~/src/bitwarden/bitwarden-cli.git
git fast-export --import-marks=../bitwarden-cli/git.marks                  \
    --export-marks=../bitwarden-cli/git.marks --all | fossil import --git  \
    --incremental --import-marks ../bitwarden-cli/fossil.marks             \
    --export-marks ../bitwarden-cli/fossil.marks ~/fossil/bitwarden-cli.fossil
