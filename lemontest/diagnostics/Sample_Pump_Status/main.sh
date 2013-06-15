#! /bin/sh

#This test does not require an OUTPUT directory
ARCHIVE=$1

#The name onetouch.log is harcoded
test=`find $ARCHIVE -name "onetouch.log"`

if [ ! -z  $test ]
	then
		awk -F"," '
		    BEGIN{ 
			    found=0
		 	}
		 	NF != 34 {
			     	print "N/A";
			     	print "0";
			     	print "Test only applies to OT2";
			     	found = -1;
			     	exit;
			}
		    /^Script/ {} 
		    /^Step/ { 
		        for(i=1;i<=NF;i++){ 
		            if($i~/Sample Pump Status/){ 
		                col=i 
		            } 
		        } 
		    } 
		    /^[0-9]/ { 
		        if($col==5){
		            found=1; 
		            print "Warning";
		            print "30";
		            print "Sample pump status failed";
		        } 
		    } 
		    END{ 
		        if(found==0){ 
		            print "OK"; 
		            print "10"; 
		            print "Sample pump status is OK" 
		        } 
		   }' $test
	else
		echo "Warning"
		echo "30"
		echo "Unable to find onetouch.log file"
fi



