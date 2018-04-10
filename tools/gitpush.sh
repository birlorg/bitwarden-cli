#!/bin/bash
~/src/bitwarden/bitwarden-cli/tools/fsl2git.sh
cd ~/src/bitwarden/bitwarden-cli.git
git checkout trunk
git push -u origin trunk
