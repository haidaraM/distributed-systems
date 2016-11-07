#!/bin/bash
echo "<html><body>"
for y in `cat neighborlist.txt` 
do 
echo "<iframe src=\"http://$y\" width="48%" height=300></iframe>"
done
echo "</body></html>"