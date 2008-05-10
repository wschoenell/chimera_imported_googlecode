#!/bin/bash

#
# Add Chimera's source and scripts directory to 
# PATH and PYTHONPATH, respectively.
#
# WARNING: This script must be sourced '$ source setup-chimera.sh' not executed
#          This script modifies environment variables (PATH and PYTHONPATH)
#

PYTHON="/usr/bin/env python"

# older bashs doesn't have $BASH_SOURCE
if [ ! -z $BASH_SOURCE ]; then

 CHIMERA_ROOT=$($PYTHON - `dirname $BASH_SOURCE` <<EOF
import os.path
import sys
print os.path.abspath(sys.argv[1])
EOF
)

else
 CHIMERA_ROOT=`pwd`
fi

CHIMERA_PYTHON_PATH=$CHIMERA_ROOT/src
CHIMERA_BIN=$CHIMERA_ROOT/src/scripts

if [ ! -f $CHIMERA_ROOT/setup.py ]; then
    echo "$0 doesn't have a valid Chimera installation."
    exit 1
fi


PYRO_PATH=

if [ -d $CHIMERA_ROOT/../Pyro-3.7 ]; then
        PYRO_PATH=$CHIMERA_ROOT/../Pyro-3.7
fi

# export PYTHONPATH if needed

if ( ! $($PYTHON - <<EOF
import sys
try:
 import chimera
 sys.exit (0)
except ImportError:
 sys.exit (1)
EOF
)); then

    export PYTHONPATH=$CHIMERA_PYTHON_PATH:$PYRO_PATH:$PYTHONPATH

fi

# export PATH if needed

if [[ ! `which chimera &> /dev/null` ]]; then
    export PATH=$PATH:$CHIMERA_BIN
fi


echo "Ready! Chimera installed at $CHIMERA_ROOT"
echo "Try run chimera -h"
