## proc-prosody.r: functions to do with getting aggregates over prosody 
## time series.
## used by: get-pros-window.r
source("f0basics.r")
#source("read-praat-files.r")
#source("nxt-proc.r")

## get aggregates over the window specified in x, to the data in xprops,
## default window size is 15 seconds.

get.var.aggs.spk <- function(xdt, windows=NULL, wkey="xid", wsize=15, var.name="F0") {
	#print(xdt)
	var.aggs.spk <- ddply(xdt, c("conv","nxt_agent"), get.xint.windows,
			windows=windows, wkey=wkey, fx=get.var.aggs.window, wsize=wsize, var.name=var.name)
	return(data.table(var.aggs.spk))
}

get.f0.aggs.window <- 
get.var.aggs.window <- function(x,xprops, var.name="F0") {
	currstart <- unique(x$wstarts)
        currend <- unique(x$wends)
        if (length(currend) >1) {
                print(x)
                print("Non unique end")
        }
	currconv <- unique(xprops$conv)
	currpart <- unique(xprops$participant)
	currspk <- unique(xprops$nxt_agent)

	normvar <- paste("norm", var.name,sep="")
	dvar <- paste("d",var.name,sep="") 	

        currx <- xprops[Time < currend & Time >= currstart]
	curr.aggs <- calc.spk.aggs(currx, var.name=normvar, xconv=currconv, xparticipant=currpart, xspk=currspk)

	if (length(grep(dvar, names(xprops))) > 0) {
		curr.aggs.dF <- calc.spk.aggs(currx, var.name=dvar, xconv=currconv, xparticipant=currpart, xspk=currspk)
        	xstats <- data.table(wstart=currstart, wend=currend, curr.aggs, curr.aggs.dF)
	} else { 
        	xstats <- data.table(wstart=currstart, wend=currend, curr.aggs)
	}

	slopevar <- paste("norm", var.name,".slope", sep="") 	
	if (length(grep(slopevar, names(xprops))) > 0) {
		curr.aggs.slope <- calc.spk.aggs(currx, var.name=slopevar, xconv=currconv, xparticipant=currpart, xspk=currspk)
        	xstats <- data.table(wstart=currstart, wend=currend, curr.aggs, curr.aggs.slope)
	} else { 
        	xstats <- data.table(wstart=currstart, wend=currend, curr.aggs)
	}

	if ("niteid" %in% names(x)) {
                xstats <- data.table(niteid=unique(x$niteid), xstats)
        }
        return(xstats)


} 


#--------------------------------------------------------------------------
# A wrapper function for applying function fx to windows, or created moving
# windows if windows==NULL.
get.xint.windows <- function(x.list0, wsize=15, tstep=5, windows=NULL, fx=get.xint.window, wkey="xid", ...) {
        ## Make sure we're dealing with a data.table    
        if (!is.data.table(x.list0)) {
                x.list <- data.table(x.list0)
        } else {
                x.list <- x.list0
        }

        ## Get the current conversation
        currconv <- x.list$conv[1]
        if (is.factor(x.list$conv)) {
                currconv <- unlevel(currconv)
        }
        print("***")
        print(currconv)
        print(wkey)
        print("***")

        if (is.null(windows)) {
                ## Make some windows
                print("NO WINDOWS GIVEN")
                if ("maxtime" %in% names(x.list)) {
                        maxt <- max(x.list$maxtime)
                } else {
                        maxt <- max(x.list$endtime)
                }
                wstarts <- seq(0,maxt,by=tstep)
                wends <- wstarts + wsize
                wints <- data.table(wstarts=wstarts, wends=wends)
        } else {
                ## Use given windows, check that there's a match between the 
		## window list and the feature series.
                print("WKEY")
                print(unique(x.list[[wkey]]))
                currwkey <- unique(x.list[[wkey]])
                if (currwkey %in% names(windows)) {
                        wints <- windows[[currwkey]]
                } else {
                        return(NULL)
                }
        }
        if ("niteid" %in% names(wints)) {
                wx.dt <- data.table(ddply(wints, c("niteid"), fx, xprops=x.list, ...))
        } else {
                wx.dt <- data.table(ddply(wints, c("wstarts"), fx, xprops=x.list, ...))
        }

        #print(wx.dt)
        return(wx.dt)
}


calc.spk.aggs <- function(x, var.name="F0", xconv="Xconv", xparticipant="Xpart", xspk="Xspk") {
        #print("calc.spk.aggs")
        if (nrow(x) > 0) {
                u <- copy(x)
                setnames(u, c(var.name), c("val"))
                if (("spk" %in% names(u)) & !("nxt_agent" %in% names(u))) {
                        setnames(u, c("spk"), c("nxt_agent"))
                }
                y <- u[,{
                        q <- quantile(val, probs=c(0.01, 0.025, 0.05, 0.25,0.5,0.75,0.95, 0.975,0.99))
                        curr.slope <- slope.value(data.table(Time=Time, val=val), xname="Time", yname="val")
                        curr.intercept <- intercept.value(data.table(Time=Time, val=val), xname="Time", yname="val")
                        list(mean.val=mean(val, na.rm=T), sd.val=sd(val, na.rm=T), max.val=max(val,na.rm=T), min.val=min(val,na.rm=T),
                        median.val=q[5],
                        q1.val=q[1], q2.5.val=q[2], q5.val=q[3], q25.val=q[4],
                        q75.val=q[6], q95.val=q[7], q97.5.val=q[8],q99.val=q[9],
                        slope.val=curr.slope, intercept.val=curr.intercept
                        )
                },by=list(conv, participant, nxt_agent)]


        } else {
                y <- data.table(conv=xconv, participant=xparticipant, nxt_agent=xspk,
                        mean.val=NA, sd.val=NA, max.val=NA, min.val=NA,
                        median.val=NA,
                        q1.val=NA, q2.5.val=NA,  q5.val=NA, q25.val=NA,
                        q75.val=NA, q95.val=NA, q97.5.val=NA, q99.val=NA,
                        slope.val=NA, intercept.val=NA
                )
        }
        setnames(y, names(y), gsub("val", var.name, names(y)))
        return(y)
}

