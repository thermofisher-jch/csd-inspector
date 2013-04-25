#!/bin/bash

ARCHIVE=$1
OUTPUT=$2
export OUTPUT

#Check if the file exists in the ARCHIVE directory
OTFILE=`find $ARCHIVE -name "onetouch.log"`
if [ ! $OTFILE ]
then
        echo "Warning"
        echo "30"
        echo "Unable to find the OT csv file"
else
        #Remove output from  a possible previous run
        echo "Removing csv file from a previous run" >&2
        rm -f $OUTPUT/*

        #For some users' log file, the 1st line is the header and does not have a "Script ..." line
        TEST=`awk 'NR==1 {if($0 ~/^Script/) {print 1}else{print 0}}' $OTFILE`
        if [ $TEST == 1 ]
        then
            #Get the useful info from the first line of the file; send the rest of the file to OUTPUT
            V=(`perl -wna -F, -e ' \
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
                        if($.==2) {$_ =~ s/[ |-]//g;$_="$_\n"}\
                        print CSVFILE $_ \
                    }' $OTFILE`)
        else
            V=($OTFILE)
            sed -e '1 s/[ |-]//g' $OTFILE > $OUTPUT/csvfile.csv
        fi

        R --vanilla --slave --args $OUTPUT/ csvfile.csv ${V[@]} < ./OT_plots.R
fi

