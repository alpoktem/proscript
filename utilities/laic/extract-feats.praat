## Extract F0 and intensity time series from a .wav file.

form getfilename
text wavfile	wavfile	
text outfile	outfile		 
real ustart	0.0
real uend	0.0		
text outdir 	outdir	
endform

print 'ustart'-'uend''newline$'

currfile$ = wavfile$
print 'outdir$''newline$''currfile$''newline$'
Read from file... 'currfile$'

## Note this keeps doesn't keep times
Extract part... ustart uend Rectangular 1 no 
shname$ = selected$ ("Sound")

#print "Part name: "'shname$''newline$'

################################################
# F0 extraction: set params 
################################################
tstep = 0.0
defmin = 70
defmax = 300
lq = 0.35
rq = 0.65


select Sound 'shname$'
To Pitch (ac)... 'tstep' 'defmin' 15 no 0.03 0.45 0.01 2 0.14 'defmax'
minf0 = Get quantile... 0.0 0.0 'lq' Hertz
maxf0 = Get quantile... 0.0 0.0 'rq' Hertz
minf0 = round(minf0 * 0.72) - 10
maxf0 = round(maxf0 * 1.90) + 10
print 'shname$''tab$''minf0''tab$''maxf0''newline$'

#################################################
## Intensity extraction 
#################################################

select Sound 'shname$'
To Intensity... 'minf0' 'tstep' no
Down to IntensityTier
Write to short text file... 'outdir$'/raw-i0/'outfile$'.IntensityTier
print 'outdir$'/raw-i0/'outfile$'.IntensityTier'newline$'

################################################
# F0 extraction 
################################################

select Sound 'shname$'
To Pitch (ac)... 'tstep' 'minf0' 15 no 0.03 0.45 0.01 2 0.14 'maxf0'

Kill octave jumps
Interpolate
Down to PitchTier
npoints = Get number of points

print 'outdir$'/raw-f0/'outfile$'.PitchTier'newline$'
if npoints > 3 
        Write to PitchTier spreadsheet file... 'outdir$'/raw-f0/'outfile$'.PitchTier
endif


select Sound 'shname$'
Remove





