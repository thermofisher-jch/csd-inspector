#!/usr/bin/perl

use strict;
use warnings;
use FileHandle;
use Getopt::Long;
use Pod::Usage;

use Path::Class;

my $archivep      = shift || "";
my $outputp       = shift || "";

my $filename      = "ReportLog.html";
my $resultsname   = "results.html";
my $startpattern  = "BASECALLING";
my $endpattern    = "TF_D";
my $searchpattern = "lib";
my $endpattern2   = "Valid reads saved";

my $verbose       = 0;
my $help          = 0;
my $man           = 0;


my $options = GetOptions ("a|archive=s"         => \$archivep,          # path to archive
			  "o|output=s"          => \$outputp,           # path to test
			  "f|file=s"            => \$filename,          # base input filename of file to be parsed 
			  "r|results=s"         => \$resultsname,       # base filename for results
			  "s|startpattern=s"    => \$startpattern,      # start pattern to look for the table
			  "e|endpattern=s"      => \$endpattern,        # end pattern to look for the table
			  "p|searchpattern=s"   => \$searchpattern,     # search pattern to look for the table
			  "v|verbose"           => \$verbose,
			  "h|help"              => \$help,
			  "m|man"               => \$man
			 );

## Parse options NEED TO FINISH THIS ALSO POD
#GetOptions("help", "man", "flag1")  ||  pod2usage(2);
#pod2usage(1)  if ($opt_help);
#pod2usage(-verbose => 2)  if ($opt_man);
##

my $archive = dir($archivep);
my $output = dir($outputp);

my $file = file($archive,$filename);
my $results = file($output,$resultsname);

my $fh = FileHandle->new($file, "r") || die "$file is unreadable:$!\n";
my $fo = FileHandle->new($results, "w") || die "$results is unwritable:$!\n";

my $s = 0;
my $table = ();
my $row = 0;
my $warn = 0;

my $skipline = "Generated";
my $oldLog = 0;
my $table2 = ();

foreach my $line ($fh->getlines){
  if ($line=~/$startpattern/){
     $s++;
     next;
   }elsif ((! $s) ||  ($line=~/$skipline/) ){
     next;
   }elsif ($line=~/$endpattern/) {
     $s--;
     $oldLog = 1;
   }elsif ($line=~/$endpattern2/) {
     $s--;
   }
  
  $line=~s/^\s+//g;
  $line=~s/\s+$//g;
  my @f = split(/\s+/,$line);
  $table->[$row] = \@f;
  @f = split(/\s\s\s\s\s+/,$line);
    
  if ($row == 1){ @f = ("",@f); }
  $table2->[$row] = \@f;
  $row++; 
}

if (not $oldLog){
  # results.html
  print $fo "<html>\n<head>\n <title>Filter Metrics CSA</title>\n</head><body>";  
  print $fo "<h4>Filter Metrics CSA</h4>";
  print $fo "<table border=1 cellpadding=3 cellspacing=0>\n";  
  foreach my $row(1..$#{$table}){    
      print $fo "<tr>", (map {"<td>$_</td>"} @{$table->[$row]}), "</tr>\n";
  }
  print $fo "</table>\n";  
  print $fo "</body>\n</html>";     
  # stdout
  print "Info\n";
  print "25\n";
  print "Filter metrics output by BaseCaller\n";  
}    
elsif (defined $table){
  # old log file  
  my $err = -1;
  
  foreach $row (0..$#{$table}){
    foreach (@{$table->[$row]}) {
      $err = $row if $_ eq $searchpattern; 
    }
  }

  die "no row with $searchpattern\n" if $err < 0;
  
  my $total = 0;
  map {$total += $_ if $_=~/\d+/} @{$table->[$err]};
  
  my $errvalue = 0;
  if ($table->[$err]->[2] == 0) {
	$warn = 1;
  }
  # foreach (0..$#{$table->[$err]}){
	
    # if($table->[$err]->[$_]=~/\d+/){
	  # print $_, $table->[$err]->[$_], "\n";
      # if (($table->[$err]->[$_]/$total) > 0.4 && $warn < 1){
	# $warn = 1; 
      # $errvalue = $table->[$err]->[$_];      
      # }elsif( ($table->[$err]->[$_]/$total) > 0.7 ){
	# $warn=2;
      # $errvalue = $table->[$err]->[$_];  
      # }
    # }
  # }
  
  writeSTDOUT($warn,$err,$errvalue);
  writeHTMLTab($table,$fo,$warn,$err,$errvalue);
}  

sub writeSTDOUT{
    my $warn      = shift || 0;
    my $err       = shift || -1;
    my $errvalue  = shift || -1;
    print "OK\n0\nfilter metrics all look good.\n" if $warn == 0; 
    print "Warning\n0\nPolyclonal filter has likely failed. http://lifetech-it.hosted.jivesoftware.com/message/4453#4453\n" if $warn == 1; 
    print "Fail\n0\nfilter metrics have a major problem. . Please see results for details.\n" if $warn == 2; 
}


sub writeHTMLTab{
  my $table     = shift;
  my $fo        = shift;
  my $warn      = shift || 0;
  my $err       = shift || -1;
  my $errvalue  = shift || -1;
  my $bgcolor   = ''; 

  $bgcolor = "orange" if $warn ==1;  
  $bgcolor = "red" if $warn ==12;
  print $fo "<html>\n<head>\n <title>Filter Metrics CSA</title>\n</head><body>";  
  
  print $fo "<table border=1 cellpadding=3 cellspacing=0>\n";
  print $fo "<caption>Filter Metrics CSA</caption>\n";
  print $fo "<tr>", (map {"<th>$_</th>"} @{$table->[0]}), "</tr>\n" ;
  foreach my $row(1..$#{$table}){
    if($row == $err){
      print $fo "<tr>";
      foreach (@{$table->[$err]}){
	if ($_=~/\d+/ && $_ == $errvalue){
	  print $fo "<td bgcolor=$bgcolor>$_</td>";
	}else{
	  print $fo "<td>$_</td>";
	}
      }
      print $fo "</tr>";
      
    }else{
      print $fo "<tr>", (map {"<td>$_</td>"} @{$table->[$row]}), "</tr>\n";
    }
    
  }
  
  print $fo "</table>\n";
  print $fo '<p>The general phenotype we are seeing is 0 polyclonal filtered and very high low quality filtered. </p>
<p>I looked at one such customer run and suspect very high polyclonality. In extreme cases of very high or very low&nbsp; polyclonality we have a known bug that will result in 0 polyclonal filtered (more info here: http://lifetech-it.hosted.jivesoftware.com/thread/1899)</p><p> </p>
<p>Because of this bug, all the reads were passed through and caught by the low quality filter. This filter is improved in 2.0.</p><p>You\'ll see high filtering in badKey (key pass filter) or&nbsp; highRes (poor signal profile filter). Both of these filters are catching the polyclonal reads.</p>
<p>A very high consensus 1-key signal peak also indicate high polyclonality. </p>
<p> </p>
<p>You can rerun the analysis with:&nbsp; </p>
<p>&lsquo;Analysis --cr-filter=off --keypass-filter=off --clonal-filter-solve=off&rsquo;</p>
<p> </p>
<p>in the advanced args textbox. This will turn off all the filters. The mapping will be very poor, because the reads are junk. </p>' if $warn == 1; 
 
  print $fo "</body>\n</html>";  
}
 
sub getTotalfromTab{
  my $table = shift;
  my $total = 0;
  foreach my $row (0..$#{$table}){
   foreach my $cellvalue (@{$table->[$row]}){
     $total += $cellvalue if $cellvalue=~/\d+/;
   } 
  }
  return $total;
}

  
