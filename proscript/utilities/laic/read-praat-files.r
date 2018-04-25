## read-praat-files.r: some functions for reading praat files!
source("proctiers.r")
source("proc-prosody.r")
##-----------------------------------------------------------------
## wrappers
get.f0.tiers.conv <- function(currconv, pdir) {
	y <- currconv
	xtier.list <- get.tiers(pdir=pdir,suffix=".PitchTier", yname="F0", short=F, skip=3)  
	return(xtier.list)
}

get.i0.tiers.conv <- function(currconv, pdir) {
	y <- currconv
	xtier.list <- get.tiers(pdir,suffix="IntensityTier",yname="I0",skip=6,short=T)
	return(xtier.list)
}


#add.times.all <- function(x.all, x.spurts.channel) {
#        lapply(x.all, add.times, x.spurts.channel=x.spurts.channel)
#}


## Add offset times based on spurt listing, return a data.table that includes
## spurt info.
add.times <- function(x.list, x.spurts.channel) {
        xdf <- data.table(unlist.df(x.list))
	#print("xdf")
	#print(xdf)
        setkey(xdf, fstem)
	#write.table(xdf, file="xdf.txt")
        setkey(x.spurts.channel, wid)
	#print("x.spurts.channel")
	#print(x.spurts.channel)
	#write.table(x.spurts.channel, file="x.spurts.channel.txt")
        y <- x.spurts.channel[xdf]
	#print(y)
	#write.table(y, file="y.txt")
        y$Time <- y$Time + y$starttime
        return(y)
}

##-----------------------------------------------------------------

normalize.conv <- function(x, x.aggs, var.name="F0", st=c("mean.val", "q5.val", "none"), zscore=F, center=c("mean","min","none"), 
			remove.outliers=c("q1.val","q5.val","none"), remove.spurt.slope=F) {
        u <- copy(x)
        setnames(u, c(var.name), c("val"))
        participants <- unique(u$participant)
        currconv <- unique(u$conv)
        print(currconv)

        norm.conv <- NULL
        for (currpart in participants) {
		print("-----------------------------------")
		print(currpart)
		if (nrow(u[participant==currpart]) > 3) { 
			curr.norm <- normalize.vals.spk(u[participant==currpart], x.aggs, var.name=var.name, 
				st=st, zscore=zscore, center=center, remove.outliers=remove.outliers, 
				remove.spurt.slope=remove.spurt.slope)	
			
			norm.conv <- rbindlist(list(norm.conv, curr.norm))
		} else {
			print("Less than 3 data points for speakers")
		}
		
        }

        return(norm.conv)

}

normalize.vals.spk <- function(u, x.aggs, var.name="F0", st=c("mean.val", "q5.val", "none"), zscore=F, center=c("mean","min","none"), 
				remove.outliers=c("q1.val","q5.val","none"), remove.spurt.slope=F) {
        currpart <- unique(u$participant)
        currconv <- unique(u$conv)
        curraggs <- x.aggs[conv==currconv][participant==currpart]

	if (remove.outliers != "none") {
		if (remove.outliers=="q1.val") {
			u <- u[val < curraggs$q99.val][val > curraggs$q1.val] 
		} else if (remove.outliers=="q5.val") {
			u <- u[val < curraggs$q95.val][val > curraggs$q5.val] 
		} else {
			print("Outlier threshold default to (1,99)")
			print(remove.outliers)
			u <- u[val < curraggs$q99.val][val > curraggs$q1.val] 
		}
	}

        normvals <- u$val

        if (st != "none") {
		f0ref <- curraggs[[st]]		## Reference value
		if (st != "mean.val") { 
			## Use the minimum as the reference
			f0ref <- max(f0ref, min(normvals, na.rm=T))	
		}
		cat("st norm val:", f0ref, "\n", sep=" ")
                normvals <- to.semitone(normvals, F0.ref=f0ref)
        }

        if (zscore) {
                normvals <- to.zscore(normvals)
        }

	if ((center != "none") & !zscore & (st == "none")) { 
		print("center")
		if (center == "min") {  
			normvals <- normvals - min(normvals, na.rm=T)
		} else {
			normvals <- normvals - mean(normvals, na.rm=T)
		}
	} 

        norm.u <- data.table(u, normval=normvals)
	if (remove.spurt.slope==T) {
		print("removing spurt slope")
		xslope <- data.table(ddply(norm.u, .(wid), get.slope.correction, xname="Time", yname="normval")) 
		setkey(xslope, wid, Time)   
		setkey(norm.u, wid, Time)	
		norm.u <- norm.u[xslope]
	}

        setnames(norm.u, names(norm.u), gsub("val",var.name, names(norm.u)))


	print(norm.u)
	print("***HERE")
        return(norm.u)


}

##-----------------------------------------------------------------
get.slope.correction <- function(x, xname="Time", yname="val") {
#	print("get.slope.correction")
	zy <- x[[yname]]
        zx <- x[[xname]]

	val.sloperm <- zy
        if(nrow(x) > 2) {
		curr.mod <- lm(zy ~ zx)
		if (curr.mod$coefficients[2] < 0) {
			val.sloperm <- zy-predict(curr.mod) 			
		} 
	} 

	return(data.table(x[,c("wid", xname)], slopeval=val.sloperm))
}


znorm.by.window <- function(u, var.name="F0", wpercent=0.5) {

        setnames(u, names(u), gsub(var.name, "val", names(norm.u)))

        currconv <- unique(u$conv)
	totaltime <- max(u$Time, na.rm=T) - min(u$Time, na.rm=T)  
	wsize <- totaltime * wpercent

	## z-score normalize by  
	norm.u <- data.table(ddply(u, c("wid"), 
	function(x, xdata, wsize) {
		curr <- xdata[Time > (min(x$Time)-wsize)][Time < (max(x$Time)+wsize), list(mean.val=mean(val, na.rm=T), sd.val(val, na.rm=T))]
		z <- (x$val - curr$mean.val) / (curr$sd.val)
		return(data.frame(Time=x$Time, wnorm.val=z))
	}, xdata=u, wsize=wsize))

	#write.table(norm.u, file="norm.u.txt")

	setkey(norm.u, wid, Time)
	setkey(u, wid, Time)
	norm.u <- u[norm.u]

        setnames(norm.u, names(norm.u), gsub("val",var.name, names(norm.u)))
	#write.table(norm.u, file="norm.u.joined.txt")

	return(norm.u)
}

##-----------------------------------------------------------------
## This might need to be put in its own file
#calc.spk.aggs <- function(x, var.name="F0", xconv="Xconv", xparticipant="Xpart", xspk="Xspk") {
#	#print("calc.spk.aggs")
#        if (nrow(x) > 0) {
#                u <- copy(x)
#                setnames(u, c(var.name), c("val"))
#		if (("spk" %in% names(u)) & !("nxt_agent" %in% names(u))) {
#			setnames(u, c("spk"), c("nxt_agent"))	
#		}
#                y <- u[,{       
#			q <- quantile(val, probs=c(0.01, 0.025, 0.05, 0.25,0.5,0.75,0.95, 0.975,0.99))
#		        curr.slope <- slope.value(data.table(Time=Time, val=val), xname="Time", yname="val")
#		        curr.intercept <- intercept.value(data.table(Time=Time, val=val), xname="Time", yname="val")
#                        list(mean.val=mean(val, na.rm=T), sd.val=sd(val, na.rm=T), max.val=max(val,na.rm=T), min.val=min(val,na.rm=T),
#                        median.val=q[5],
#                        q1.val=q[1], q2.5.val=q[2], q5.val=q[3], q25.val=q[4],
#                        q75.val=q[6], q95.val=q[7], q97.5.val=q[8],q99.val=q[9], 
#			slope.val=curr.slope, intercept.val=curr.intercept
#			)
#                },by=list(conv, participant, nxt_agent)]
#
#
#        } else {
#                y <- data.table(conv=xconv, participant=xparticipant, nxt_agent=xspk,
#                        mean.val=NA, sd.val=NA, max.val=NA, min.val=NA,
#                        median.val=NA,
#			q1.val=NA, q2.5.val=NA,  q5.val=NA, q25.val=NA,
#                        q75.val=NA, q95.val=NA, q97.5.val=NA, q99.val=NA, 
#			slope.val=NA, intercept.val=NA
#		)
#        }
#        setnames(y, names(y), gsub("val", var.name, names(y)))
#        return(y)
#}


##-----------------------------------------------------------------

add.maxtime <- function(x, conv.maxtime) {
        currconv <- unique(x$conv)
        data.table(x, maxtime=conv.maxtime[conv==currconv]$maxtime)
}


add.df.conv <- function(x, var.name="F0") {
	print("add.df.conv") 
	setnames(x, names(x), gsub(var.name, "val", names(x))) 

        u <- x[,{    
		if (length(normval) >= 4) {
			dy <- get.spline.deriv(Time, normval)
			dys <- get.spline.deriv(Time, slopeval)

			xcurr <- data.table(
				nxt_agent=nxt_agent, conv=conv, participant=participant, channel=channel, conv_id=conv,
				starttime=starttime, endtime=endtime,
				Time=Time, val=val, normval=normval, normval.slope=slopeval, maxtime=maxtime,
				dval=dy$y, dval.slope=dys$y)
		} else {
			xcurr <- data.table(
				nxt_agent=nxt_agent, conv=conv, participant=participant, channel=channel, conv_id=conv,
				starttime=starttime, endtime=endtime,
				Time=Time, val=val, normval=normval, normval.slope=slopeval, maxtime=maxtime,
				dval=0, dval.slope=0)
		}
		xcurr
        },by=list(wid)]

	setnames(u, names(u), gsub("val", var.name, names(u))) 
	print(names(u))
	return(u)
}


get.spline.deriv <- function(x, y) {
        v <- smooth.spline(x,y)
        dy <- predict(v, deriv=1)
        return(dy)

}


#add.deriv.all.I0 <- function(xlist) {
#        return(lapply(xlist, add.dI0.conv))
#}

#add.deriv.all.F0 <- function(xlist) {
#        return(lapply(xlist, add.dF0.conv))
#}



#==========================================================
normalize.convs.all <- function(x, spk.aggs, var.name="F0", st=c("mean.val", "q5.val", "none"), center=c("mean","min","none"), zscore=F, 
				remove.outliers=c("q1.val","q5.val","none")) {
        x.aggs <- copy(spk.aggs)
        setnames(x.aggs, names(x.aggs), gsub(var.name, "val", names(x.aggs)))
        lapply(x, normalize.conv, x.aggs=x.aggs, var.name=var.name, st=st, zscore=zscore, center=center, remove.outliers= remove.outliers)
}

get.spk.aggs <- function(x, var.name="F0") {
        unlist.df(lapply(x, calc.spk.aggs, var.name=var.name))
}

add.maxtime.all <- function(xlist, conv.maxtime) {
        lapply(xlist, add.maxtime, conv.maxtime=conv.maxtime)
}

