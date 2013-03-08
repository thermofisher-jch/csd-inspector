#!/usr/bin/perl 

use strict;
use warnings;
my $kit;
my $RT_R1=-1; 
my $RT_R2=-1; 
my $RT_R3=-1; 
my $RT_R4=-1;
my $file=$ARGV[0];
my $found=0;

open(FILE, $file) or die "Unable to open file $file $!";

#Scan the file for the data, getting the last values in the log
while (<FILE>){
	if( /^Sequencing\s+Kit\s+Used:\s+(\S+)/){
		$kit=$1;
		$found++;
	}elsif(/^RawTraces\s+R1:\s+(\S+)/){
		$RT_R1 = $1;
		$found++;
	}elsif(/^RawTraces\s+R2:\s+(\S+)/){
		$RT_R2 = $1;
		$found++;
	}elsif(/^RawTraces\s+R3:\s+(\S+)/){
		$RT_R3 = $1;
		$found++;
	}elsif(/^RawTraces\s+R4:\s+(\S+)/){
		$RT_R4 = $1;
		$found++;
	}
}

#test fails if one or more of the values are not present in the file
if($found < 5 ){
	print "Fail\n";
	print "40\n";
	print "Unable to find all the data needed for the test!\n";
}elsif($kit eq 'IonPGM200Kit'){  
	if($RT_R1 < 7.0){
		print "Fail\n";
		print "40\n";
		print "pH for nuc R1 is less than 7: $RT_R1 \n";
	}elsif ($RT_R2 < 7.0){
		print "Fail\n";
		print "40\n";
		print "pH for nuc R2 is less than 7: $RT_R2 \n";
	}elsif ($RT_R3 < 7.0){
		print "Fail\n";
		print "40\n";
		print "pH for nuc R3 is less than 7: $RT_R3 \n";
	}elsif ($RT_R4 < 7.0){
		print "Fail\n";
		print "40\n";
		print "pH for nuc R4 is less than 7: $RT_R4\n";
	}else{
		print "OK\n";
		print "10\n";
		print "Test passed: pH for all nucleotides is >= 7\n";
	}      	
}else{
	print "N/A\n";
	print "0\n";
}

close(FILE);
