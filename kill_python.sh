#!/bin/bash -e

# Find locally running python process and kill it!

# find python (local to tty) and note down pid
PROC=$(ps | grep python | awk -F ' ' '{print $1}')

# if there is a python process running then try and kill
if [ -n "$PROC" ]; then 
    echo "Killing process $PROC"

    kill -KILL $PROC
    RESULT=$?
    # Did we kill it properly
    if [ $RESULT -eq 0 ]; then
        echo "Success!"
        return $RESULT
    else
        echo "Failed with error: $RESULT"
        return $RESULT
    fi
else
    echo "Nothing to be done here."
fi
# Nothing to be done here. Move on.
return 0
