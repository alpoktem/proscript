#!/usr/bin/Rscript --vanilla --slave

library(data.table)
library(plyr)
source("proc-prosody.r")

print("=== START get-pros-window ===")

args=(commandArgs(TRUE))
if(length(args)==0){
	stop("No arguments supplied. Exiting")

}

#----------------------------------------------------------
print(args)
currconv <- args[1]
featname <- args[2]  ## F0 or Intensity, or something else?
xdir <- args[3] 	## Data Directory, input/output to/from  xdir/F0 etc.
window.file  <- args[4]
#window.type <- args[5]
#----------------------------------------------------------
## get windows
#window.file <- paste(window.dir, "/", currconv, ".", window.type, ".txt" sep="")		

## Nowadays get window type from the file extension
#window.type <- strsplit(basename(window.file), "\\.")[[1]][2]
#print(window.type)

## Read the segment times
segs <- fread(window.file)

## Temporarily rename the id column name for generality. 
# if (grepl("sent", window.type)) {
# 	setnames(segs, "sent.id", "niteid")	
# } else if (grepl("word", window.type)){
# 	setnames(segs, "word.id", "niteid")	
# } else if (grepl("seg", window.type)){
# 	setnames(segs, "seg.id", "niteid")	
# } else {
# 	print("What windowtype?")
# }

setnames(segs, "word.id", "niteid")

## a data.table of segment times
segs <- segs[,list(conv, xid=paste(conv, spk, sep="-"), niteid, wstarts=starttime, wends=endtime)]
print(segs)

## put segments into list, one data.table per speaker
x.list <- dlply(segs, .(xid), function(x) {x})
print(paste("spk NAMES:", names(x.list)))
print(names(x.list[1]))

## get feature time series 
objfile <- paste(xdir, "/", featname, "/", currconv, sep="")		
xobj <- load(objfile)
x.feat <- get(xobj)

## Fix an ICSI error 
#if (currconv == "Bmr031") {
#	x.feat$participant[x.feat$xid == "Bmr031-H"] <- "me001"
#}

## Get segment based aggregates
x.aggs <- get.var.aggs.spk(x.feat, windows=x.list, wkey="xid", var.name=toupper(featname))

#if (featname == "i0") {
#	x.aggs <- get.i0.aggs.spk(x.feat, windows=x.list, wkey="xid")
#} else if (featname == "f0") {
#	x.aggs <- get.f0.aggs.spk(x.feat, windows=x.list, wkey="xid")
#}

## Output as a table 
outfile.txt <- paste(xdir, "/", featname, "/", currconv, ".aggs", ".txt", sep="")		
print(outfile.txt)	
write.table(x.aggs[order(wstart)], file=outfile.txt, row.names=F, quote=F)	
	
print("=== END get-pros-window ===")

