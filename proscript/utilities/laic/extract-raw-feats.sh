#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

get_abs_filename() {
  # $1 : relative filename
  spacefix=${1// /\\ }
  echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
}

## Get raw F0 and intensity features using praat.  
PRAAT=praat 		#link to praat binary
curr_dir=`pwd`
file_id=$1
wavfile=`get_abs_filename $2`
alignfile=`get_abs_filename $3`
outdir=`get_abs_filename $4`

wavbase=$(basename "$wavfile")
#file_id="${wavbase%.*}"

echo Processing $file_id

mkdir -p $outdir/
mkdir -p $outdir/raw-f0
mkdir -p $outdir/raw-i0

cd $SCRIPT_DIR

tail -n +2 $alignfile |
while read line
do
	#CAREFUL HERE. CHANGED ALIGNFILE STRUCTURE
	wordid=`echo $line | cut -d " " -f 8`
	start=`echo $line | cut -d " " -f 6`
	end=`echo $line | cut -d " " -f 7`

	outfilename=$wordid

    #FOR AUDIO SEGMENTATION
    #wavsegmentdir=$outdir/$conv-wav
    #mkdir -p $wavsegmentdir
	#echo  $wavfile $outfile $start $end $indir $outdir $conv 
	#echo `which praat`
	#duration=`echo - | awk -v end=$end -v start=$start '{print end - start}'`
	#echo avconv -i $wavfile -ss $start -t $duration -ac 1 -ar 16000 $wavsegmentdir/$wordid.wav
	
	#EXTRACT RAW FEATURES USING PRAAT
	praat extract-feats.praat $wavfile $outfilename $start $end $outdir
done  

cd $curr_dir
#exit 0
