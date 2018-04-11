#!/bin/bash
# docs see: http://fossil-scm.org/index.html/doc/trunk/www/inout.wiki
cd ~/src/bitwarden/bitwarden-cli.git
fossil export --git --import-marks ~/fossil/bitwarden-cli-fossil.marks  \
       --export-marks ~/fossil/bitwarden-cli-fossil.marks               \
       ~/fossil/bitwarden-cli.fossil | git fast-import            \
       --import-marks=/Users/zie/fossil/bitwarden-cli-git.marks                \
       --export-marks=/Users/zie/fossil/bitwarden-cli-git.marks
