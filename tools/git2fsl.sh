#!/bin/bash
cd ~/src/bitwarden/bitwarden-cli.git
git fast-export --import-marks=~/fossil/bitwarden-cli-git.marks                  \
    --export-marks=~/fossil/bitwarden-cli-git.marks --all | fossil import --git  \
    --incremental --import-marks ~/fossil/bitwarden-cli-fossil.marks             \
    --export-marks ~/fossil/bitwarden-cli-fossil.marks ~/fossil/bitwarden-cli.fossil
