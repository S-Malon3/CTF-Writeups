#!/usr/bin/perl
use strict;
use warnings;
use Math::BigInt;
use List::Util qw(reduce);

my @tuples;


# --- INPUTS ----------------------------------------------------------------- #

# Parse (ni,wi), (nj, wj),... from commandline
foreach my $arg (@ARGV) {
# Match pattern like (w,n)
if ($arg =~ /^\((.+?),(.+?)\)$/) {
      push @tuples, [Math::BigInt->new($1), Math::BigInt->new($2)];
   } else {
      warn "Invalid tuple format: $arg\n";
   }
}

# Print all tuples
foreach my $tuple (@tuples) {
   print "id $tuple->[0]: $tuple->[1]\n";
}


# --- FIND p,s --- ----------------------------------------------------------- #

my @d; #list of all d_i,j pairs

# find d_i,j
sub d_ij {
   my ($i, $j) = @_;
   return ($j->[1] - $i->[1]) - (($i->[0] - $j->[0]) * $i->[1] * $j->[1]);
}

# modular inversion
sub modinv {
  my($x, $m) = @_;
  Math::BigInt->new($x)->bmodinv($m)
}

# Call d_ij for all unique pairs of tuples
for (my $i = 0; $i < @tuples; $i++) {
   for (my $j = $i + 1; $j < @tuples; $j++) {
      my $result = d_ij($tuples[$i], $tuples[$j]);
      push @d, $result;
   }
}

# Print all d values
print "\nd values:\n";

foreach my $d (@d) {
   print " - $d\n"
}

my $p;
# Calculate GCD of all d values as p
if (@d) {
   $p = reduce { Math::BigInt::bgcd($a, $b) } @d;
   #   print "\np: $gcd\n";
}

# calculate s given p using ni,wi
my $s = modinv($tuples[0][1], $p) - $tuples[0][0];


# --- VALIDATE p,s ------------------------------------------------------------#

my $validate = modinv($s+$tuples[1][0],$p);

unless($validate == $tuples[1][1]) {
   print("not enough id: token pairs to determine p");
   exit 0;
}

print "\n\n# --- p, s Validated " . ('-' x 58) . "#\n\n";

print "p: $p\n";
print "s: $s\n";


# --- SOLVE -------------------------------------------------------------------#

my $solve = modinv($s+0x1337,$p);
print "\n\n# --- 0x1337 " . ('-' x 66) . "#\n\n";
print "$solve\n";
