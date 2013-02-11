#!/bin/sh

# find python (local to tty) and note down pid
PROC=$(ps | grep python | awk -F ' ' '{print $1}')

# if there is a python process running then try and kill
if [ "$PROC" ]; then 
    echo "Killing process $PROC"

    kill -KILL $PROC
    RESULT=$?
    # Did we kill it properly
    if [ $RESULT == 0 ]; then
        echo "Success!"
        return $RESULT
    else
        echo "Failed with error: $RESULT"
        return $RESULT
    fi
fi
