#!/bin/bash

ARCHIVE=$1
OUTPUT=$2

R --vanilla --slave --args $ARCHIVE $OUTPUT < ./filter_metrics.R
