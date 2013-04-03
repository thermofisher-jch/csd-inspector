#!/bin/bash

ARCHIVE=$1
OUTPUT=$2
export OUTPUT

#Check if the file exists in the ARCHIVE directory
OTFILE=`find $ARCHIVE -name "*.log"`

if [ ! $OTFILE ]
then
	echo "Warning"
	echo "30"
	echo "Unable to find the OT csv file"
else
	#Remove csvfile.csv from  a possible previous run
	if [ -e $OUTPUT/csvfile.csv ]
	then
		echo "Removing csv file from a previous run" >&2
		rm -f $OUTPUT/csvfile.csv
	fi

	#Get the useful info from the first line of the file; send the rest of the file to OUTPUT
	V=(`perl -na -F, -e ' \
		if(! defined fileno CSVFILE){ \
			open(CSVFILE, ">> $ENV{'OUTPUT'}/csvfile.csv"); \
		} \
		if($.==1){ \
			@a=split("/",$F[0]); \
			$a[-1] =~ /(\S+)_(\S+)\.txt/; \
			print "$1 $2\n"; \
			$F[2] =~ /(\S+)\s+(\S+)/; \
			print "$2\n"; \
		}else{ \
			print CSVFILE $_ \
		}' $OTFILE`)

	#make sure the html file does not exist in the OUTPUT directory from a previous run
	if [ -e $OUTPUT/results.html ]
    then
    	echo "Removing html output from previous run" >&2
        rm $OUTPUT/results.html
        rm -R $OUTPUT/results_files
	fi

	R --vanilla --slave --args $OUTPUT/ csvfile.csv ${V[@]} < ./OT_plots.R
fi