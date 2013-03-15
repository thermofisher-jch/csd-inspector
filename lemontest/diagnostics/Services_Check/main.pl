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
my $startpattern  = "Required processes";
my $endpattern    = "===";
my $searchpattern = "";
my $priority      = 0;

my $verbose       = 0;
my $help          = 0;
my $man           = 0;


my $options = GetOptions ("a|archive=s"         => \$archivep,          # path to archive
			  "o|output=s"          => \$outputp,           # path to test
			  "r|rank=i"            => \$priority,          # priority for this test 
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

my $fh = FileHandle->new($file, "r") or  die "$file is unreadable:$!\n";
my $fo = FileHandle->new($results, "w") or  die "$results is unwritable:$!\n";

my $s = 0;
my $table = ();
my $row = 0;

my $warn = 0;
my @services = qw(apache2 tomcat6 postgresql sge_execd sge_qmaster);
my %services2check = ();
@services2check{@services} = 1;

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
  foreach my $service(keys %services2check){
    delete $services2check{$service} if $line =~ /$service/; 
  }
  if ($line =~/No pid file: \/var\/run\/ionCrawler.pid/) { $services2check{'ionCrawler'} = 1 }
  if ($line =~/No pid file: \/var\/run\/ionJobServer.pid/) { $services2check{'ionJobServer'} = 1 }
  if ($line =~/No pid file: \/var\/run\/ionArchive.pid/) { $services2check{'ionArchive'} = 1 }
  if ($line =~/No pid file: \/var\/run\/ionPlugin.pid/) { $services2check{'ionPlugin'} = 1 }
}

my @failedservices = keys %services2check;

if(scalar @failedservices){
  $warn = 2;
  $priority = 90;
}

writeSTDOUT($priority,$warn);
writeHTML($fo,$warn,\@failedservices);


sub writeSTDOUT{
  my $priority  = shift || 0;
  my $warn      = shift || 0;
  print "OK\n$priority\nAll Services are Running.\n" if $warn == 0; 
  print "Alert\n$priority\nThe following services are not running: @failedservices\n" if $warn == 2; 
}

sub writeHTML{
  my $fo        = shift;
  my $warn      = shift || 0;
  my $err       = shift;
  my $bgcolor   = ''; 

  print $fo "<html>\n<head>\n <title>Check System Services</title>\n</head><body>";  
  print $fo "<h2>Error!!</h2><p>The following Services have failed: <b>@failedservices</b></p>" if $warn == 2;
  print $fo "<h2>Solutions</h2>If one of the services is down log into the server by ssh as ionadmin and run
  <dl>
  <dt>ionCrawler</dt>
    <dd>sudo /etc/init.d/ionCrawler start</dd>
  <dt>ionJobServer</dt>
    <dd>sudo /etc/init.d/ionJobServer start</dd> 
  <dt>ionArchive</dt>
    <dd>sudo /etc/init.d/ionArchive start</dd> 
  <dt>ionPlugin</dt>
    <dd>sudo /etc/init.d/ionPlugin start</dd> 
  <dt>apache2</dt>
    <dd>sudo /etc/init.d/apache2 start</dd>  
  <dt>postgresql</dt>
    <dd>sudo /etc/init.d/postgresql-8.4 start</dd> 
  <dt>sge_execd or sge_execd</dt>
    <dd>On a 2.0 TS: <br>
	sudo /etc/init.d/gridengine-exec start</br>
    sudo /etc/init.d/gridengine-master start<br>
	On a 1.5 or older TS: <br>
	sudo /etc/init.d/sgeexecd start</br>
    sudo /etc/init.d/sgemaster start
	</dd>
 </dl>";  
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

  
