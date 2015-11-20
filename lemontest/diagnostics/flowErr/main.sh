#!/bin/bash

ARCHIVE=$1
OUTPUT=$2

var=$(./flowErr_lemon.pl -e ${ARCHIVE}/rawlib.ionstats_error_summary.h5 -o $OUTPUT 2>&1)
if [ "$?" = "0" ]; then
  echo Info
  echo 20
  echo Plots of flowErr.
else
  echo N/A
  echo 0
  echo $var
fi  
