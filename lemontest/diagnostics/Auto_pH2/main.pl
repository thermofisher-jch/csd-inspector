#!/usr/bin/perl 
#Creates plots for the autopH data in an initlog.txt file
#Takes 2 arguments: 1st is the initlog.txt file, 2nd is the results file

use Chart::Gnuplot;

my $OUTDIR=$ARGV[1];
my $proton=0;
my $numlogs=0;			#keeps track of the number of logs in a single file
my $ll=0;				#lower limit, upper limit and target in a line like    -300  <  target=-124  < -36 
my $ul=0;
my $target=0;
my $curr_it=0;			#current iteration while adding W2
my $diff=0;				#stores the diff value in a line like 1) <diff=3427 target=-124 limit=-36>   W2Avg = 11364 W3Avg=7937
my $status=0; 			#status 0 => passed
my $total_w1_added=0;	#holds the total w1 added to detect undershot
my @x=();				#x, y hold the current vectors to be plotted
my @y=();
my @x1=();				#x1,y1 hold the last set of values used to generate output
my @y1=();
my $dx;					#dx holds the dx of the current iteration


#the first value of array x is always 0
push @x,0;

#print "@ARGV\n";


#initialize the HTML results file
open (HTML_FILE, ">$OUTDIR/results.html") or die "Can't open html file\n";
print HTML_FILE "<html><link rel=stylesheet href=some.css type=text/css>\n";
print HTML_FILE "</head><body>";
print HTML_FILE "<h1 align=\"center\">AutopH plot</h1>";
close (HTML_FILE);

while (<>){
	if(/^Chip\s+Type\s+(\S+)/){
		#stop parsing if chip is Proton
		if($1 eq "BB1"){
			$proton=1;
			last;
		}
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
			$status=1;
			$dx ="OVERSHOT TARGET PH: W2 PH=$W2PH Failed ($diff) < $ll\n";
			&output(\@x,\@y,$numlogs,\$dx);
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
			$status=2;
			$dx="FAILED UNDERSHOT TARGET PH: W2 PH=$W2PH Failed ($diff) > $ul\n";
			&output(\@x,\@y,$numlogs,\$dx);
			# &print_arrays(\@x,\@y);
			#keep the values before reseting x,y
			@x1=@x; @y1=@y;
			@x=();@y=();push @x,0;
		}
	#there are cases in which the undershot registering does not follow the "standard" 
	#however those cases can be captured by the error line in the log		
	}elsif(/^FAILEDUNDERSHOT/){
		#$status = 2 => undershot
		$status=2;
		$dx="$_\n";
		&output(\@x,\@y,$numlogs,\$dx);
		# &print_arrays(\@x,\@y); 
		#keep the values before reseting x,y
		@x1=@x; @y1=@y;
		@x=();@y=();push @x,0;
	# }elsif(/^OVERSHOT/){
		# &print_arrays(\@x,\@y);
		# @x=();@y=();push @x,0;
		# print "line $_\n";
	}elsif($diff>$ll && $diff < $ul){
		#$status = 0 => passed
		$status=0;
		$dx="Passed\n";
		&output(\@x,\@y,$numlogs,\$dx);
		# &print_arrays(\@x,\@y);
		#keep the values before reseting x,y
		@x1=@x; @y1=@y;
		@x=();@y=();push @x,0;
		$diff=$ul=$ll=0;
	}
}

#test does not apply for proton
if($proton==0){
	#finalize the HTML results file
	open (HTML_FILE, ">>$OUTDIR/results.html") or die "Can't open html file\n";
	print HTML_FILE "</body></html>";
	close (HTML_FILE);

	#print output to stdout
	#desired output is generated only if there is enough data in the x,y vectors
	if($#x1==$#y1){
		print "Starting pH: $y1[0]\n";
		print "W1 added (ml): $x1[-1]\n";

		#print results only for the last test
		#$status = 1 => overshot, 2=> undershot
		if($status!=0){
			print "Alert\n";
			print "40\n";
			print "$dx\n"
		#$status = 0 => OK
		}else{
			print "OK\n";
			print "10\n";
			print "$dx\n"	
		}

	}else{
		print "Warning\n";
		print "30\n";
		print "Plot can't be generated";
	}

#if proton is true
}else{
	#close files and exit  
	open (HTML_FILE, ">>$OUTDIR/results.html") or die "Can't open html file\n";
	print HTML_FILE "<br></br><br></br> <h2 align=\"center\">Test does not apply: Proton initlog.txt detected!</h2>";
	close (HTML_FILE);
	print "N/A\n";
	print "0\n";
	print "Proton initlog.txt detected\n";
}


#sub to generate the output
sub output{
	my($x,$y,$num,$dx)=@_;

	#Prepare files for output
	open (OFILE, ">> $OUTDIR/plot_data.csv") or die "Can't open output file\n";
	print OFILE "Run $num\n";
	print OFILE "W2_pH,W1_ml_added\n";

	open (HTML_FILE, ">>$OUTDIR/results.html") or die "Can't open html file\n";	

	#desired output is generated only if there is enough data in the x,y vectors
	if($#$x==$#$y){
		#create directory for Results
		#print data to file
		# open (OFILE, ">> $OUTDIR/plot_data.csv") or die "Can't open output file\n";
		# print OFILE "Run $num\n";
		# print OFILE "W2_pH,W1_ml_added\n";
		for($i=0;$i<=$#$x;$i++){
			print OFILE "$y->[$i],$x->[$i]\n";
		}
		print OFILE "$$dx\n";
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

	
		print HTML_FILE "<img src=\"plot$num.png\" />";
		

	#if not enough data in the vectors it is some case not considered in the program => fail
	}else{
		#print to csv file and HTML a note and return
		print OFILE "Data can't be plotted!";
		print HTML_FILE "<br></br><br></br> <h2 align=\"center\">Data can't be plotted!</h2>";

	}

	close (OFILE); 
	close (HTML_FILE);

}

