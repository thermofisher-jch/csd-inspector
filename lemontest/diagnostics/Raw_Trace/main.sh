#!/bin/bash

ARCHIVE=$1
OUTPUT=$2

var=$(./rawTrace_lemon.pl -a $ARCHIVE -o $OUTPUT 2>&1)
if [ "$?" = "0" ]; then
  echo Info
  echo 25
  echo Plots of NucStep traces.
else
  echo NA
  echo 100
  echo $var
fi  
