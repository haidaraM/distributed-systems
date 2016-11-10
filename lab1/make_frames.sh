#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "You must specify the port number"
    exit 1
fi

port=$1
echo "<html><body>"
for y in `cat neighborlist.txt` 
do 
echo "<iframe src=\"http://$y:${port}\" width="48%" height=400></iframe>"
done
echo "</body></html>"
