#! /bin/sh

#This test does not require an OUTPUT directory
ARCHIVE=$1


#The name InitLog.txt is harcoded
test=`find $ARCHIVE -name "InitLog.txt"`
if [ ! -z  $test ]
	then
		perl nuc_pH.pl $test
	else
		echo "Unable to find InitLog.txt file. Please upload it manually"
fi



