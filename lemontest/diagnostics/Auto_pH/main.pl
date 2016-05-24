#!/usr/bin/perl -w
#Creates plots for the autopH data in an initlog.txt file
#Takes 2 arguments: 1st is the ARCHIVE Directory where the initLog.txt file is expected, 2nd is the RESULTS directory

use Chart::Gnuplot;

my $OUTDIR=$ARGV[1];
my $ARCHIVE=$ARGV[0];
my $fh;                 	#filehandle for initlog.txt
my $html_file; 				#filehandle for html output file
my $initLog_name="InitLog.txt";	#the name of the file that is expected in the ARCHIVE directory
my $status=0; 				#status of the autopH test: 0 => passed
my @x=();					#x, y hold the current vectors to be plotted since there might be
my @y=();				
my $dx;						#dx holds the dx of the iteration


sub pgm{					#parses pgm files
	my ($pgmfh,$x,$y,$status,$dx)=@_;
	my $numlogs=1;			#the number of logs ina file is expected to be 1
	my $diff=999999;		#stores the diff value in a line like 1) <diff=3427 target=-124 limit=-36>   W2Avg = 11364 W3Avg=7937
	my $ll=0;				#lower limit, upper limit and target in a line like    -300  <  target=-124  < -36 
	my $ul=0;
	my $target=0;
	my $curr_it=0;			#current iteration while adding W2	
	my $total_w1_added=0;	#holds the total w1 added to detect undershot
	my $W2PH;
	my @x1=();				#x1,y1 hold the last set of values used to generate output
	my @y1=();


	while(<$pgmfh>){
		if(/^Chip\s+Type\s+(\S+)/){
			$diff=999999;
       		$numlogs++;
		}elsif(/^\s+(-?\d+)\s+<\s+target=(-?\d+)\s+<\s+(-?\d+)/){
			$ll=$1;
			$target=$2;
			$ul=$3;
		}elsif(/(^\d+)\)\s+W2\s+pH=(\S+)/){
			$curr_it=$1;
			$W2PH = $2;
	        push @y,$W2PH;
		}elsif(/^\Q$curr_it\E\)\s+<diff=(-?\d+)/){
			$diff=$1;
			#is overshot?
			if($diff<$ll){
				#$status = 1 => overshot
				$$status=1;
				$$dx ="OVERSHOT TARGET PH: W2 PH=$W2PH Failed ($diff) < $ll\n";
				&output(\@x,\@y,$numlogs,$dx);
				# &print_arrays(\@x,\@y);
				#keep the values before reseting x,y
				@x1=@x; @y1=@y;
				@x=();@y=();push @x,0;
			}
		}elsif(/^\Q$curr_it\E\)\s+Adding\s+(\S+)/){
			$total_w1_added=$1+$x[-1];
			#push @y,$W2PH;
			push @x, $total_w1_added;
			#is undershot?
			if ($total_w1_added>=175 && $diff > $ul){
				#$status = 2 => undershot
				$$status=2;
				$$dx="FAILED UNDERSHOT TARGET PH: W2 PH=$W2PH Failed ($diff) > $ul\n";
				&output(\@x,\@y,$numlogs,$dx);
				# &print_arrays(\@x,\@y);
				#keep the values before reseting x,y
				@x1=@x; @y1=@y;
				@x=();@y=();push @x,0;
			}
		#there are cases in which the undershot registering does not follow the "standard" 
		#however those cases can be captured by the error line in the log		
		}elsif(/^FAILEDUNDERSHOT/){
			#$status = 2 => undershot
			$$status=2;
			$$dx="$_\n";
			&output(\@x,\@y,$numlogs,$dx);
			# &print_arrays(\@x,\@y); 
			#keep the values before reseting x,y
			@x1=@x; @y1=@y;
			@x=();@y=();push @x,0;

		}elsif($diff>$ll && $diff < $ul){
			#$status = 0 => passed
			$$status=0;
			$$dx="Passed\n";
			&output(\@x,\@y,$numlogs,$dx);
			# &print_arrays(\@x,\@y);
			#keep the values before reseting x,y
			@x1=@x; @y1=@y;
			@x=();@y=();push @x,0;
			$diff=$ul=$ll=0;
		}
	}
	@x=@x1; @y=@y1;
}

sub proton{					#parses proton files
	my ($Hfh,$x,$y,$status,$dx)=@_;
	my @autophRow;

	while(<$Hfh>){
		if(/^AUTOPH/){
			@autophRow=split(" ",$_);
			push @x,$autophRow[8]+$x->[-1];
			$y->[-1]=$autophRow[4]; 
			push @y,$autophRow[6];
		}elsif(/ErrorMsgBeginOvershot Target pH: W2 pH=(.*?) /){
			#$status = 1 => overshot
			$$status=1;
			$$dx ="OVERSHOT W2 PH=$1\nFailed\n";			
		}elsif(/ErrorMsgBeginUndershot Target pH: W2 pH=(.*?) /){
			#$status = 2 => overshot
			$$status=2;
			$$dx ="UNDERSHOT W2 PH=$1\nFailed\n";
		}	
	}
	if($$status==0){
		$$dx="Passed\n";
		&output(\@x,\@y,1,$dx);
	}

}

#sub to generate the output plot and csv file with the plot info
sub output{
	my($x,$y,$num,$dx)=@_;
	my $ofile;    #output filehandle
	#Prepare files for output

	open ($ofile, ">> $OUTDIR/plot_data.csv") or die "Can't open output file\n";
	print $ofile "Run $num\n";
	print $ofile "W2_pH,W1_ml_added\n";

	# open (HTML_FILE, ">>$OUTDIR/results.html") or die "Can't open html file\n";	
	open ($html_file, ">>$OUTDIR/results.html") or die "Can't open html file\n";	

	#desired output is generated only if the x,y vectors contain the same amount of data
	if($#$x==$#$y){
		#create directory for Results
		#print data to file

		for(my $i=0;$i<=$#$x;$i++){
			# print OFILE "$y->[$i],$x->[$i]\n";
			print $ofile "$y->[$i],$x->[$i]\n";
		}
		#print OFILE "$$dx\n";
		print $ofile "$$dx\n";

		#$$dx=0;
     
		#Create chart object and specify the properties of the chart
		my $chart = Chart::Gnuplot->new(
		    output => "$OUTDIR/plot$num.png",
		    title  => "Initialization AutopH Profile run $num",
		    xlabel => "W1 added (ml)",
		    ylabel => "W2 pH"
		);
	 
		# Create dataset object and specify the properties of the dataset
		my $dataSet = Chart::Gnuplot::DataSet->new(
		    xdata => \@x,
		    ydata => \@y,
		    style => "linespoints"
		);

		$chart->plot2d($dataSet);

		#print to html file in the Results directory
		print $html_file "<p style=\"text-align:center;\"><img src=\"plot$num.png\" /></p>";

	#if not enough data in the vectors it is some case not considered in the program => fail
	}else{
		#print to csv file and HTML a note and return
		print $ofile "Data can't be plotted!";
		print $html_file "<br></br> <h2 align=\"center\">Data can't be plotted!</h2>";

	}

	# add a reference to the raw init
	print $html_file "<br /><h2 align=\"center\">Raw Init Plot</h2><p style=\"text-align:center;\"><img src=\"../../RawInit.jpg\" /></p>" if -e "$ARCHIVE/RawInit.jpg";

	#close (OFILE); 
	close ($ofile); 
	#close (HTML_FILE);
	close ($html_file);
}

sub finish{
	my ($x,$y,$status,$dx)=@_;
	#print final output to stdout
	# output is generated only if there is the same amount data in the x,y vectors,
	# otherwise something went wrong

	open ($html_file, ">>$OUTDIR/results.html") or die "Can't open html file\n";
	
	if($#x==$#y){
		#print results only for the last test
		#$status = 1 => overshot, 2=> undershot, $status = 0 => OK
		if($$status!=0){
			print "Alert\n";
			print "40\n";
			print $html_file "<br></br> <h5 align=\"left\">$$dx</h2><br></br>";
		#$status = 0 => OK
		}else{
			print "OK\n";
			print "10\n";
			print "Starting pH: $y->[0]\n";
			print "W1 added (ml): $x->[-1]\n";
			#print $html_file "<br></br> <h5 align=\"left\">$$dx</h2><br></br>";
		}
		print "$$dx\n"	

	}else{
		print "Warning\n";
		print "30\n";
		print "Sorry, can't generate plot\n";
		print $html_file "<br></br><br></br> <h2 align=\"center\">Sorry, can't generate plot</h2>";
	}

	#finalize the HTML results file
	print $html_file "</body></html>";
	close ($html_file);
}


#the first value of array x is always 0
push @x,0;

#initialize the HTML results file

open ($html_file, ">$OUTDIR/results.html") or die "Can't open html file\n";
print $html_file "<html><link rel=stylesheet href=some.css type=text/css>\n";
print $html_file "</head><body>";
print $html_file "<h1 align=\"center\">AutopH plot</h1>";
close ($html_file);

#Open the initLog.txt file
open ($fh,"$ARCHIVE/$initLog_name")or die "Can't open InitLog.txt file\n";

while (<$fh>){
	if(/^Chip\s+Type\s+(\S+)/){
		#parsing is different for PGM & for Proton
		if($1 eq "BB1"){
			push @y,0;	# structure of the InitLog requires this previous to parsing
			&proton($fh,\@x,\@y,\$status,\$dx);
		}else{
			&pgm($fh,\@x,\@y,\$status,\$dx);
		}
        
	}
}

#close init file
close($fh);

&finish(\@x,\@y,\$status,\$dx);












