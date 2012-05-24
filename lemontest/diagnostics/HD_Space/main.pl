#!/usr/bin/perl

use strict;
use warnings;
use FileHandle;
use Getopt::Long;
use Pod::Usage;

use Path::Class;

my $archivep      = shift || "";
my $outputp       = shift || "";

my $filename      = "stats_sys.txt";
my $resultsname   = "results.html";
my $startpattern  = "Disk Space";
my $endpattern    = "=";
my $searchpattern = "%";

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


foreach my $line ($fh->getlines){
  if ($line=~/$startpattern/){
     $s++;
     next;
   }elsif (! $s) {
     next;
   }elsif ($line=~/$endpattern/) {
     $s--;
   }
  $line=~s/^\s+//g;
  $line=~s/\s+$//g;
  my @f = split(/\s+/,$line);
  $table->[$row] = \@f;
  $row++;
}

if (defined $table){
  
  my $err = -1;
  
  foreach $row (0..$#{$table}){
    foreach my $col(0..$#{$table->[$row]}) {
      $err = $col if $table->[$row]->[$col]=~/$searchpattern/; 
    }
  }
  
  die "no row with $searchpattern\n" if $err < 0;
  
  my $errvalue = 0;
  foreach $row (0..$#{$table}){
    foreach my $col(0..$#{$table->[$row]}) {
      my $value = $table->[$row]->[$col];
      if (($col == $err) && ($value eq "100%")){
	$errvalue = $value; 
	$warn = 2;
      }
    }
  }

  
  writeSTDOUT($warn,$err,$errvalue);
  writeHTMLTab($table,$fo,$warn,$err,$errvalue);
 } 

sub writeSTDOUT{
    my $warn      = shift || 0;
    my $err       = shift || -1;
    my $errvalue  = shift || -1;
    print "OK\n0\nHard drive space is fine.\n" if $warn == 0; 
    print "Warning\n0\nHard drive space is an issue. Please see results for details.\n" if $warn == 1; 
    print "Fail\n100\nNo Hard drive space left! Please see results for details.\n" if $warn == 2; 
}

sub writeHTMLTab{
  my $table     = shift;
  my $fo        = shift;
  my $warn      = shift || 0;
  my $err       = shift || -1;
  my $errvalue  = shift || -1;
  my $bgcolor   = ''; 

  $bgcolor = "orange" if $warn == 1;  
  $bgcolor = "red" if $warn == 2;  
  print $fo "Warning!!" if $warn == 1;
  print $fo "Error!!" if $warn == 2;

  print $fo "<html>\n<head>\n <title>Filter Metrics CSA</title>\n</head><body>";  
  print $fo "<p>Warning!!</p>" if $warn == 1;
  print $fo "<p>Error!!</p>" if $warn == 2;
   
  print $fo "<table border=1 cellpadding=3 cellspacing=0>\n";

  print $fo "<tr>", (map {"<th>$_</th>"} @{$table->[0]}), "</tr>\n" ;
  foreach my $row(1..$#{$table}){
    if($row == $err){
      print $fo "<tr>";
      foreach my $col(0..$#{$table->[$row]}){
	if ($col == $err && $table->[$row]->[$col] eq $errvalue){
	  print $fo "<td bgcolor=$bgcolor>$table->[$row]->[$col]</td>";
	}else{
	  print $fo "<td>$table->[$row]->[$col]</td>";
	}
      }
      print $fo "</tr>";
      
    }else{
      print $fo "<tr>";
      foreach my $col(0..$#{$table->[$row]}){
	if ($col == $err && $table->[$row]->[$col] eq $errvalue){
	  print $fo "<td bgcolor=$bgcolor>$table->[$row]->[$col]</td>";
	}else{
	  print $fo "<td>$table->[$row]->[$col]</td>";
	}
      }
      print $fo "</tr>";
    }
    
  }
  
  
  print $fo "</table>\n";
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

  
