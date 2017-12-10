# f0basics.r: Catherine Lai
# Basic functions to do with processing F0. 
require(geometry)
require(mFilter)
source("legendre.r")

sigmoid <- function(x) {
	return(1/(1 + exp(-x)))
}

refactor <- function(vrmi) {
        for (fx in names(vrmi)) {
                if (is.factor(vrmi[[fx]])) {
                        vrmi[[fx]] <- factor(unlevel(vrmi[[fx]]))
                }
        }
        return(vrmi)
}



bw.smooth <- function(x, xname="Time", yname="F0", freq=NA) {
        #points(x, col="magenta")
	if (is.na(freq)) {
		 freq <- bwcuttoff(x, nv=0.1, xname) 
	}

        if (is.null(freq) | (nrow(x) < 4)){ p1 <- x }
        else {
		#print(tail(x))
                p1 <- data.frame(x[[xname]], 
			fitted(bwfilter(x[[yname]],freq=freq)))
		names(p1) <- c(xname, yname)	
                p1 <- bw.brute.ends(p1, xname, yname)

        }
        return(p1)
}

bw.brute.ends <- function(p1, xname="Time", yname="F0") {
        if(nrow(p1) == 0) {return(p1)}
        x <- head(tail(p1,min(5, nrow(p1))),4)
        xs <- x[[xname]]
        ys <- x[[yname]]
        pend <- predict(lm(ys ~ xs), data.frame(xs=tail(p1[[xname]],1)))
        p1[nrow(p1), yname] <- pend

        return(p1)
}



# calculate normalized cutoff for Butterworth filter. 
bwcuttoff <- function(x, xname="Time", nv=0.1) {
	if (nrow(x) > 1) {
		return((1/min(diff(x[[xname]]))/2) * nv)
	} else {
		return(NULL)
	}
}


from.semitone <- function(F0.st, F0.ref=min(F0.hz)) {
        F0.ref * (2^(F0.st/12))
}

to.semitone <- function(x, F0.ref=100) {
	if (length(names(x))==0) {
		F0.hz <- x 
		y <- 12* log2(F0.hz/F0.ref)
	} else {
		F0.hz <- x$F0
        	y <- data.frame(Time=x$Time, F0=12* log2(F0.hz/F0.ref))
	} 
	y
}


to.zscore <- function(x, x.mean=mean(x,na.rm=T), x.sd=sd(x,na.rm=T)) {
        (x - x.mean)/x.sd
}


unfactor <- function(x) {
        as.numeric(levels(x)[x])
}

unlevel <- function(x) {
        levels(x)[x]
}


remove.outliers <- function(x)  {
        y <- to.semitone(x$F0)
        i.new <- (y < mean(y, na.rm=T) + 3*sd(y, na.rm=T)) &  (y > mean(y, na.rm=T) - 3*sd(y, na.rm=T))
        data.frame(Time=x$Time[i.new], F0=x$F0[i.new])
}

#############################################################################################
irange <- function(x){ 
	if(nrow(x) > 0) { max(x$I0)-min(x$I0) }
	else {NA}
}

mean.i0 <- function(x) {
	if(nrow(x) > 0) { mean(x$I0, na.rm=T) }
	else {NA}
}

sd.i0 <- function(x) {
	if(nrow(x) > 0) { sd(x$I0, na.rm=T) }
	else {NA}
}

median.i0 <- function(x) {
	if(nrow(x) > 0) { median(x$I0, na.rm=T) }
	else {NA}
}
min.i0 <- function(x) {
	if(nrow(x) > 0) { min(x$I0, na.rm=T) }
	else {NA}
}

max.i0 <- function(x) {
	if(nrow(x) > 0) { max(x$I0, na.rm=T) }
	else {NA}
}

slope.i0 <- function(x0) {
	x <- x0[!is.na(x0$I0),]	
	if(nrow(x) > 1) {
		y <- lm(x$I0 ~ x$Time)$coefficients[2]
		names(y) <- NULL
		return(y) 
	} else {return(NA)}
}  

intercept.i0 <- function(x0) {
	x <- x0[!is.na(x0$I0),]	
	if(nrow(x) > 1) {
		y <- lm(x$I0 ~ x$Time)$coefficients[1]
		names(y) <- NULL
		return(y)
	} else {return(NA)}
}  

jitter.i0 <- function(x) {
	if(nrow(x) > 0) {
		y <- x$I0
        	(sum(abs(diff(y)),na.rm=T)/(length(y)-1))/(sum(abs(y))/length(y))
	} else {NA}
}

npoints.i0 <- function(x) {
	length(x$I0[!is.na(x$I0)])
}

##################################################################################
prange.value <- function(x0, xname="Time", yname="Value"){ 
	x <- x0[!is.na(x0[[yname]]),]	
	if(nrow(x) > 0) { max(x[[yname]],na.rm=T)-min(x[[yname]],na.rm=T) }
	else {NA}
}

mean.value <- function(x0, xname="Time",yname="Value") {
	x <- x0[!is.na(x0[[yname]]),]	
	if(nrow(x) > 0) { mean(x[[yname]], na.rm=T) }
	else {NA}
}

sd.value <- function(x0, xname="Time", yname="Value") {
	x <- x0[!is.na(x0[[yname]]),]	
	if(nrow(x) > 0) { sd(x[[yname]], na.rm=T) }
	else {NA}
}

median.value <- function(x0, xname="Time",yname="Value") {
	x <- x0[!is.na(x0[[yname]]),]	
	if(nrow(x) > 0) { median(x[[yname]], na.rm=T) }
	else {NA}
}
min.value <- function(x0, xname="Time",yname="Value") {
	x <- x0[!is.na(x0[[yname]]),]	
	if(nrow(x) > 0) { min(x[[yname]], na.rm=T) }
	else {NA}
}

max.value <- function(x0, xname="Time", yname="Value") {
	x <- x0[!is.na(x0[[yname]]),]	
	if(nrow(x) > 0) { max(x[[yname]], na.rm=T) }
	else {NA}
}

slope.value <- function(x0, xname="ActualTime", yname="Value", sampletime=F) {
	#print(c(xname, yname)) 
	#print(x0)
	x <- x0[!is.na(x0[[yname]]),]	
	zy <- x[[yname]]
	zx <- x[[xname]]

	if(nrow(x) > 1) {
		if (sampletime) {
			y <- lm(Value ~ SampleTime, data=x)$coefficients[2]
		}  else {
			y <- lm(zy ~ zx)$coefficients[2]
		}
		names(y) <- NULL
		return(y) 
	} else {return(NA)}
}  

intercept.value <- function(x0, xname="ActualTime", yname="Value", sampletime=F) {
	x <- x0[!is.na(x0[[yname]]),]	
	zy <- x[[yname]]
	zx <- x[[xname]]

	if(nrow(x) > 1) {
		if (sampletime) {
			y <- lm(Value ~ SampleTime, data=x)$coefficients[1]
		} else {
			y <- lm(zy ~ zx)$coefficients[1]
		}
		names(y) <- NULL
		return(y)
	} else {return(NA)}
}  

jitter.value <- function(x0, xname="Time", yname="Value") {
	x <- x0[!is.na(x0[[yname]]),]	
	if(nrow(x) > 0) {
		y <- x[[yname]]
        	(sum(abs(diff(y)),na.rm=T)/(length(y)-1))/(sum(abs(y),na.rm=T)/length(y))
	} else {NA}
}

npoints.value <- function(x, xname="Time", yname="Value") {
	length(x[[yname]][!is.na(x[[yname]])])
}

get.legendre.coeffs <- function(x, degree=5) {
	lp <- legendre.polynomials(degree, normalize=T)
	p <- legendre.coeff(x$ActualTime,x$Value,lp)
	p
} 


#############################################################################################
prange <- function(x){ 
	if(nrow(x) > 0) { max(x$F0)-min(x$F0) }
	else {NA}
}

mean.f0 <- function(x) {
	if(nrow(x) > 0) { mean(x$F0, na.rm=T) }
	else {NA}
}

sd.f0 <- function(x) {
	if(nrow(x) > 0) { sd(x$F0, na.rm=T) }
	else {NA}
}

median.f0 <- function(x) {
	if(nrow(x) > 0) { median(x$F0, na.rm=T) }
	else {NA}
}
min.f0 <- function(x) {
	if(nrow(x) > 0) { min(x$F0, na.rm=T) }
	else {NA}
}

max.f0 <- function(x) {
	if(nrow(x) > 0) { max(x$F0, na.rm=T) }
	else {NA}
}

slope.f0 <- function(x0) {
	x <- x0[!is.na(x0$F0),]	
	if(nrow(x) > 1) {
		y <- lm(x$F0 ~ x$Time)$coefficients[2]
		names(y) <- NULL
		return(y) 
	} else {return(NA)}
}  

intercept.f0 <- function(x0) {
	x <- x0[!is.na(x0$F0),]	
	if(nrow(x) > 1) {
		y <- lm(x$F0 ~ x$Time)$coefficients[1]
		names(y) <- NULL
		return(y)
	} else {return(NA)}
}  

jitter.f0 <- function(x) {
	if(nrow(x) > 0) {
		y <- x$F0
        	(sum(abs(diff(y)))/(length(y)-1))/(sum(abs(y))/length(y))
	} else {NA}
}

npoints.f0 <- function(x) {
	length(x$F0[!is.na(x$F0)])
}

get.legendre.coeffs.f0 <- function(x, degree=5) {
	lp <- legendre.polynomials(degree, normalize=T)
	p <- legendre.coeff(x$Time,x$F0,lp)
	p
} 


pred.point2 <- function(y1, y2, x) {
	a <- y1[2] - ((y2[2]-y1[2])/(y2[1]-y1[1])) * y1[1] 
	m = ((y2[2]-y1[2])/(y2[1]-y1[1]))
	m*x + a
}

sort.hull <- function(y) {
	ynew <- NULL
	for (i in 1:nrow(y)) {
		ynew <- rbind(ynew, sort(y[i,]))
	}  
	ynew
}

get.max <- function(x, y) {
	vs <- unique(c(y[,1], y[,2])) 	
	vs[which.max(x[vs,]$F0)]
}

get.prevs <- function(x, y, v) {
	curr <- y[y[,2] == v,]	
	if (length(curr) == 2) {
		return(c(v, get.prevs(x, y, curr[1])))
	} else if (length(curr) > 2) {
		cx <- find.highv(x,curr,forward=F)
		return(c(v, get.prevs(x, y, cx[1])))
	} else {
		return(v)
	}
}

# Find the highest vertex in the convex hull top.
find.highv <- function(x, curr, forward=T) {
	preds <- NULL 
	if (forward) {
		v1 <- unique(curr[,1])
		for (i in 1:nrow(curr)) {
			preds <- c(preds, 
				pred.point2(x[curr[i,1],], x[curr[i,2],], x[v1+1,1]))
		}
	} else {
		v1 <- unique(curr[,2])
		for (i in 1:nrow(curr)) {
			preds <- c(preds, 
				pred.point2(x[curr[i,1],], x[curr[i,2],], x[v1-1,1]))
		}
	}
	#print(which.max(preds))
	#print(curr[which.max(preds),])
	curr[which.max(preds),]
}

get.nxts <- function(x, y, v) {
	curr <- y[y[,1] == v,]	
	if (length(curr) == 2) {
		return(c(v, get.nxts(x, y, curr[2])))
	} else if (length(curr) > 2) {
		cx <- find.highv(x,curr,forward=T)
		return(c(v, get.nxts(x, y, cx[2])))
	} else {
		return(v)
	}
}


# get.hulltop: get the part of the convex hull above the contour.
get.hulltop <- function(x, y0, vmax) {
	#print("hulltop")	
	y <- sort.hull(y0)
	prev <- get.prevs(x, y, vmax) 
 	nxt <- get.nxts(x, y,vmax)
	top <- unique(sort(c(prev,nxt)))
	return(list(prev=prev, nxt=nxt, top=top))
}

# get.nxtdiff: find the point with maximum difference from 
# the hull top that exceeds the threshold. 
get.nxtdiff <- function(x, y, nxt, diffthresh=1) {
	maxdiff <- 0 
	idiff <- NA   	
	for (i in 1:(length(nxt)-1)) {
		vs <- c(nxt[i], nxt[i+1]) 
		#points(x[vs,], col="blue", pch=15)

		preds <- NULL
		curr <- vs[1]:vs[2]
		for (j in curr)  {
			preds <- c(preds,pred.point2(x[vs[1],], x[vs[2],], x[j,1]))
		}
		preds <- unlist(preds)
		#points(x[curr,1], preds, col="red", pch=13)
		diffs <- preds - x[curr,2]
		md <- which.max(diffs) 	
		#print(diffs[md])
		#points(x[curr[md],], col="green", pch=15)
		if (diffs[md] > diffthresh & diffs[md] > maxdiff) {
			idiff <- curr[md] 
			maxdiff <- diffs[md]	
		} 
	}	
	return(idiff)
} 


# get.maxdiffs: Recursively apply Mermelstein algorithm to 
# time series (x0) to find inflection points.  
# (This function is unfortunately named! It should get a wrapper!)

get.maxdiffs <- function(x0, vs=1:nrow(x0), diffthresh=2) {
	if (length(vs) == 0) {return(NULL)}

	if (length(vs) < 3 ) {
		return(c(which.max(px[[1]]$F0), 1, nrow(px[[1]])))
	}  

	x <- x0[vs,]

	y <- convhulln(as.matrix(x))
	y <- sort.hull(y)
	vmax <- get.max(x,y) 
	#points(x0[vs[vmax],], col="red", pch=15)
	print(vs[vmax])
	htop <- get.hulltop(x,y,vmax)
	itop <- get.nxtdiff(x,y,htop$top,diffthresh)
	if (!is.na(itop)) {
		#abline(v=x[itop,], col="green")
		prev <- head(vs,1):vs[itop]
		nxt <- vs[itop]:tail(vs,1)
		return(rbind(c(vs[vmax], head(vs,1), tail(vs,1)),   
			get.maxdiffs(x0, prev, diffthresh), 
			get.maxdiffs(x0, nxt, diffthresh)))	
	} else {
		return(c(vs[vmax], head(vs,1), tail(vs,1)))   
	}
} 

chunk.by.pause <- function (x, plen=0.1) {
        chunks <- list()
        lx <- 1
        pauses <- get.pause.indices(x, plen)

                if (length(pauses) > 0) {
                for (i in 1:length(pauses)) {
                        p <- pauses[i]
                        curr <- list()
                        curr$Time <- x$Time[lx:p]
                        curr$F0 <- x$F0[lx:p]

                        chunks[[i]] <- curr
                        lx <- p+1
                }
        }
        curr <- list()
        curr$Time <- x$Time[lx:length(x$Time)]
        curr$F0 <- x$F0[lx:length(x$Time)]
        chunks[[length(chunks)+1]] <- curr
        chunks
}

get.pause.indices <- function(x, plen=0.1) {
        tdiff <- diff(x$Time,1)
        which(tdiff > plen)
}


apply.by.pause <- function(x, f, plen=0.1) {
        xs <- chunk.by.pause(x, plen)
        ys  <- lapply(xs, f)

        x.new <- list(Time=NULL, F0=NULL)
        for (y in ys) {
                x.new$Time <- c(x.new$Time, y$Time)
                x.new$F0 <- c(x.new$F0, y$F0)
        }

        x.new

}

unlist.df <- function(x) {
	y <- NULL
	if (length(x) > 0) {
		for (i in 1:length(x)) {
			y <- rbind(y, x[[i]])
		}
	}
	y
}

unlist.vec <- function(x) {
	y <- NULL
	for (i in 1:length(x)) {
		y <- c(y, x[[i]])
	}
	y
}

get.pquantiles <- function(pitchtiers, probs=c(0,0.05,0.25,0.5,0.75,0.95,1)) {
	pquantile <- sapply(pitchtiers, function(x) {quantile(x$F0, probs=probs)})
	pquantile <- t(pquantile)
	data.frame(rownames(pquantile), pquantile, row.names=NULL)
}


