#!/bin/bash

file=$1

sed -i "s/\\$\\$/\$/g" $file
sed -i "s/<sub>/\$_\{/g" $file
sed -i "s/<\/sub>/\}\$/g" $file
sed -i "s/<sup>/\$^\{/g" $file
sed -i "s/<\/sup>/\}\$/g" $file
sed -i 's/<br>/\\newline /g' $file

