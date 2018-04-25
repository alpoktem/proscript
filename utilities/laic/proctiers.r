source("f0basics.r")

#get.info <- function(fstem){
#	return(fstem)
#}

get.tiers <- function(pdir, filenames=NULL, suffix=".PitchTier", xname="Time",yname="F0", short=F, skip=3, atype="icsi") {
	print("get.tiers")
	
        if (is.null(filenames)) {
                curr.files <- list.files(pdir)
        } else {
		print(pdir)
		print(curr.files)
                curr.files <- paste(filenames, suffix,sep="")
        }
        pitchtiers <- list()

	print("get.tiers loop")
#	print(curr.files)
        for (filename in curr.files) {
		#print(filename)
                if (file.exists(paste(pdir, filename, sep="/"))) {
			## Read file
                        curr0 <- try(read.table(paste(pdir, filename, sep="/"), header=F, 
					na.strings="--undefined--", skip=skip))
			if (is.data.frame(curr0)) {
				curr <- data.table(get.tier(curr0, short=short))
				setnames(curr, c(xname, yname))
				fstem <- paste(head(strsplit(filename, split="\\.")[[1]], -1), collapse=".")

				## Check if there's enough data
				if (nrow(curr) >= 3) {
					pitchtiers[[fstem]] <- data.table(fstem=fstem, curr)
				} else {
					print("less than 3 points")
					print(curr)
				}

			} else {
				print("No data!")
			}
	
                } else {
                        print(paste("No file", filename))
                }
        }

	print("got tier")
        return(pitchtiers)
}

get.tier <- function(curr0, short=F) { 
	if (short) {
		xcurr <- curr0[seq(1,nrow(curr0)-1, by=2),]
		ycurr <- curr0[seq(2,nrow(curr0), by=2),]
		curr <- data.frame(xcurr, ycurr)
	} else { 
		curr <- curr0
	}

	return(curr)
}


get.normdata.f0 <- function(xdt) {
	xdt[,list(mean=mean(F0), sd=sd(F0), median=median(F0)),by=list(participant)]
}

get.normdata.i0 <- function(xdt) {
	xdt[,list(mean=mean(I0), sd=sd(I0), median=median(I0)),by=list(participant)]
}


add.st <- function(xdata, xnorm=NULL, xname="Time", bw=T) {

	xdata[,{
		currspk <- unlevel(participant[1])
		print(fstem[1])
		if (is.null(xnorm)) {
			spkmed <- median(F0, na.rm=T)
		} else {
			spkmed <- xnorm[participant==currspk]$median
			print(currspk)
			print(spkmed)
		}	
		F0.st <- to.semitone(F0, spkmed)	
		if (bw) {
			curr <- data.frame(Time, F0.st)
 			xbw <- bw.smooth(curr, xname, "F0.st")
                        F0.st.bw <- xbw$F0.st
		} else {
			F0.st.bw <- F0.st
		}
		list(conv=unlevel(conv[1]), participant=currspk, starttime=starttime, endtime=endtime, 
			Time=Time+starttime, F0=F0, F0.st=F0.st, F0.st.bw=F0.st.bw)
	}, by=list(fstem)]
}

add.zscore.f0 <- function(xdata, xnorm=NULL, xname="Time", bw=T) {
	xdata[,{
		currspk <- unlevel(participant[1])
		print(fstem[1])
		if (is.null(xnorm)) {
			spkmean <- mean(F0, na.rm=T)
			spksd <- sd(F0, na.rm=T)
		} else {
			spkmean <- xnorm[participant==currspk]$mean
			spksd <- xnorm[participant==currspk]$sd
		}	
		F0.zs <- to.zscore(F0, spkmean, spksd)	
		if (bw) {
			curr <- data.frame(Time, F0.zs)
 			xbw <- bw.smooth(curr, xname, "F0.zs")
                        F0.zs.bw <- xbw$F0.zs
		} else {
			F0.zs.bw <- F0.zs
		}
		list(conv=unlevel(conv[1]), participant=currspk, starttime=starttime, endtime=endtime, 
			Time=Time+starttime, F0=F0, F0.zs=F0.zs, F0.zs.bw=F0.zs.bw)
	}, by=list(fstem)]
}

add.zscore.int <- function(xdata, xnorm=NULL, xname="Time", bw=T) {
	xdata[,{
		currspk <- unlevel(participant[1])
		print(fstem[1])
		if (is.null(xnorm)) {
			spkmean <- mean(I0, na.rm=T)
			spksd <- sd(I0, na.rm=T)
		} else {
			spkmean <- xnorm[participant==currspk]$mean
			spksd <- xnorm[participant==currspk]$sd
		}	
		I0.zs <- to.zscore(I0, spkmean, spksd)	
		if (bw) {
			curr <- data.frame(Time, I0.zs)
 			xbw <- bw.smooth(curr, xname, "I0.zs")
                        I0.zs.bw <- xbw$I0.zs
		} else {
			I0.zs.bw <- I0.zs
		}
		list(conv=unlevel(conv[1]), participant=currspk, starttime=starttime, endtime=endtime, 
			Time=Time+starttime, I0=I0, I0.zs=I0.zs, I0.zs.bw=I0.zs.bw)
	}, by=list(fstem)]
}

regroup <- function(fx, vs, vname) {
	xf0 <- list()
	for (v in vs) {
		xf0[[v]] <- list()
	}
	for (i in c(1:length(fx))){
		x <- fx[[i]]
		if (is.factor(x[[vname]])) {
			curr <- unlevel(x[[vname]][1])	
		} else {
			curr <- x[[vname]][1]	
		}
		print(curr)
		xf0[[curr]][[unlevel(x$fstem[1])]] <- x
		print(unlevel(x$fstem[1]))
	}

	return(xf0)
}


