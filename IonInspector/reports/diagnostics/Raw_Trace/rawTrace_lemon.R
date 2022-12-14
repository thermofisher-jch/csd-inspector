
library(rjson)
set.seed(0)

seqToFlow <- function(sequence,flowOrder,nFlow=NA,finishAtSeqEnd=FALSE,flowOffset=0) {
  # Compute homopolymers
  sequence <- gsub("[^(ACGT)]","",sequence) # remove non-ACGT chars
  bases <- strsplit(sequence,"")[[1]]
  runEnds <- c(which(!bases[-length(bases)]==bases[-1]),length(bases))
  hpNuc <- bases[runEnds]
  hpLen <- diff(c(0,runEnds))
  hpN   <- length(hpNuc)

  # Compute flowOrder
  f <- strsplit(flowOrder,"")[[1]]
  if(is.na(nFlow))
    nFlow <- length(f)
  else
    f <- rep(f,ceiling(nFlow/length(f)))[1:nFlow]

  out <- rep(NA,nFlow)
  fIndex <- 0
  if(length(hpNuc)>0) {
    hpIndex <- 1
    for(fIndex in (1+flowOffset):nFlow) {
      if(hpNuc[hpIndex] == f[fIndex]) {
        out[fIndex] <- hpLen[hpIndex]
        hpIndex <- hpIndex + 1
        if(hpIndex > hpN)
          break;
      } else {
        out[fIndex] <- 0
      }
    }
  }
  if(fIndex < nFlow) {
    if(finishAtSeqEnd) {
      out <- out[-((fIndex+1):nFlow)]
    } else {
      out[(1+fIndex):nFlow] <- 0
    }
  }

  return(out)
}

readRegion <- function(nucStepDir,region) {
  wellTypes <- c("bead","empty")
  res <- list(count=list(),signal=list(),stepSize=list())
  first <- TRUE
  for(wellType in wellTypes) {
    inFile <- sprintf("%s/NucStep_%s_%s.txt",nucStepDir,region,wellType)
    # Handle a bug that was present in Analysis - can remove this in April 2012
    temp <- scan(inFile,nlines=1,what=character(),quiet=TRUE)
    if(!is.element(temp[2],c("A","C","G","T"))) {
      nCol <- 1+length(scan(inFile,nlines=1,what=character(),quiet=TRUE))
      x <- scan(inFile,what=rep(list(numeric()),nCol-1),quiet=TRUE)
      x <- c(x[1],list(rep("N",length(x[[1]]))),x[2:length(x)])
    } else {
      nCol <- length(scan(inFile,nlines=1,what=character(),quiet=TRUE))
      x <- scan(inFile,what=c(list(numeric()),list(character()),rep(list(numeric()),nCol-2)),quiet=TRUE)
    }
    # Make sure we are in flow order
    newOrder <- order(x[[1]])
    x <- lapply(x,function(z){z[newOrder]})
    if(first) {
      first <- FALSE
      res$flow <- x[[1]]
      res$nuc  <- x[[2]]
      res$xMin <- x[[3]][1]
      res$xMax <- x[[4]][1]
      res$yMin <- x[[5]][1]
      res$yMax <- x[[6]][1]
    }
    res$count[[wellType]] <- x[[7]][1]
    res$signal[[wellType]] <- matrix(unlist(x[8:nCol]),nrow=length(res$flow))
    res$stepSize[[wellType]] <- apply(res$signal[[wellType]],1,max)-apply(res$signal[[wellType]],1,min)
  }

  return(res)
}

flowPlot <- function(signal,nuc,flow,frameStart,ylim,legendPosition,ylab="",header="") {
    nbr <- split(signal,1:nrow(signal))
    nbrSplit <- split(nbr,nuc)
    flowSplit <- split(flow,nuc)
    par(mfrow=c(1,4),mai=c(0.2,0.2,0.15,0.05),omd=c(0.03,0.98,0.05,0.9))
    for(thisNuc in c("A","C","G","T")) {
      thisNbr <- nbrSplit[[thisNuc]]
      thisFlow <- flowSplit[[thisNuc]]
      if(is.element(thisNuc,c("A"))) {
        ylab=ylab
        yaxt="s"
      } else {
        ylab=""
        yaxt="n"
      }
      if(is.element(thisNuc,c("A","C","G","T"))) {
        xlab="Time (s)"
        xaxt="s"
      } else {
        xlab=""
        xaxt="n"
      }
      plot(range(frameStart),main=thisNuc,ylim,type="n",xlab=xlab,xaxt=xaxt,ylab=ylab,yaxt=yaxt)
      abline(v=frameStart,col="lightgrey")
      thisColor <- jet.colors(length(thisNbr))
      for(i in 1:length(thisNbr)) {
        lines(frameStart,thisNbr[[i]],col=thisColor[i])
      }
      legendFlowIndex <- unique(pmax(1,round(seq(0,1,length=9)*length(thisFlow))))
      legend(legendPosition,inset=0.01,paste("flow",thisFlow[legendFlowIndex]),fill=thisColor[legendFlowIndex])
    }
    mtext(header,outer=TRUE,side=3,line=0)
}

flowsSinceLastLegendTitle <- "nuc wait (flows)"
flowsSinceLastLegendText  <- c("2 or fewer","3","4 or 5","6","7 or more")
flowsSinceLastLegendPch   <- c(25,21:23,24)
flowsSinceLastPch <- 1:30
flowsSinceLastPch[1:3] <- 25
flowsSinceLastPch[4]   <- 21
flowsSinceLastPch[5:6] <- 22
flowsSinceLastPch[7]   <- 23
flowsSinceLastPch[8:length(flowsSinceLastPch)]   <- 24

jet.colors <- colorRampPalette(c("#00007F", "blue", "#007FFF", "cyan", "#7FFF7F", "yellow", "#FF7F00", "red", "#7F0000"))
nucColor <- c(
  "A" = "green",
  "C" = "blue",
  "G" = "black",
  "T" = "red"
)
pngWidth <- 400
pngHeight <- 400
system(sprintf("mkdir -p %s",plotDir))

frameStart <- scan(nucStepTime,quiet=TRUE)

#dcOffsetFile     <- "/home/scawley/tmp/B15-645/dcOffset/dcOffset.txt"
#readDcOffset <- function(dcOffsetFile) {
#  nCol <- length(scan(dcOffsetFile,nlines=1,what=character(),quiet=TRUE))
#  x <- scan(dcOffsetFile,what=c(list(numeric()),list(character()),rep(list(numeric()),nCol-2)),quiet=TRUE)
#  names(x) <- c("flow","nuc","min","max",paste("q",sprintf("%02d",1:99),sep=""))
#  return(x)
#}
#dcOffset <- readDcOffset(dcOffsetFile)

data <- lapply(as.list(nucStepRegions),function(r){readRegion(nucStepDir,r)})
names(data) <- nucStepRegions

legendPosition <- list(
  "bead"   = "topleft",
  "empty"  = "topleft",
  "nbrsub" = "bottomright"
)
# Individual nuc steps
for(iRegion in 1:length(data)) {
  ylim.nucStep <- list(
    "bead"   = range(unlist(data[[iRegion]]$signal)),
    "empty"  = range(unlist(data[[iRegion]]$signal)),
    "nbrsub" = range(data[[iRegion]]$signal$bead-data[[iRegion]]$signal$empty)
  )
  regionName <- names(data)[iRegion]
  data[[iRegion]]$signal$nbrsub <- data[[iRegion]]$signal$bead-data[[iRegion]]$signal$empty
  data[[iRegion]]$count$nbrsub  <- data[[iRegion]]$count$bead
  data[[iRegion]]$smoothed <- data[[iRegion]]$signal
  for(thisNuc in c("A","C","G","T")) {
    flowIndex <- which(data[[iRegion]]$nuc==thisNuc)
    if(length(flowIndex)>0) {
      data[[iRegion]]$smoothed$bead[flowIndex,]   <- apply(data[[iRegion]]$signal$bead[flowIndex,] ,2,function(z){lowess(z)$y})
      data[[iRegion]]$smoothed$empty[flowIndex,]  <- apply(data[[iRegion]]$signal$empty[flowIndex,],2,function(z){lowess(z)$y})
    }
  }
  data[[iRegion]]$smoothed$nbrsub <- data[[iRegion]]$smoothed$bead-data[[iRegion]]$smoothed$empty
  x <- data[[iRegion]]
  for(wellType in c("bead","empty","nbrsub")) {
    # plot of nuc steps
    myTitle <- sprintf("Nuc Steps for %s\n%s wells in %dx%d %s region, lower-left corner at (c%d,r%d)\n%d empties and %d ISPs",
      analysisName,
      wellType,x$xMax-x$xMin,x$yMax-x$yMin,names(data)[iRegion],
      x$xMin,x$yMin,
      x$count$empty,
      x$count$bead
    )
    png(plotFile <- sprintf("%s/nucSteps.%s.%s.png",plotDir,regionName,wellType),height=pngHeight,width=2*pngWidth)
    flowPlot(x$signal[[wellType]],x$nuc,x$flow,frameStart,ylim.nucStep[[wellType]],legendPosition[[wellType]],header=myTitle)
    dev.off()
    #system(sprintf("eog %s",plotFile))

    # Smoothed plot of nuc steps
    myTitle <- sprintf("Smoothed %s",myTitle)
    png(plotFile <- sprintf("%s/nucSmooth.%s.%s.png",plotDir,regionName,wellType),height=pngHeight,width=2*pngWidth)
    flowPlot(x$smoothed[[wellType]],x$nuc,x$flow,frameStart,ylim.nucStep[[wellType]],legendPosition[[wellType]],header=myTitle)
    dev.off()
    #system(sprintf("eog %s",plotFile))

    flowSplit <- split(x$flow,x$nuc)
    flowIndexSplit <- split(1:length(x$flow),x$nuc)

    # Plot flow residuals
    flowResidual <- x$signal[[wellType]]-x$smoothed[[wellType]]
    flowResidual <- sqrt(apply(flowResidual*flowResidual,1,mean))
    png(plotFile <- sprintf("%s/flowResidual.%s.%s.png",plotDir,regionName,wellType),height=pngHeight,width=pngWidth)
    ylim <- range(c(0,flowResidual,15))
    plot(range(x$flow),ylim,type="n",xlab="Flow",ylab="RMS Flow Residual")
    for(thisNuc in c("A","C","G","T")) {
      flowsSinceLast <- c(0,diff(flowSplit[[thisNuc]]))
      lines(flowSplit[[thisNuc]],flowResidual[flowIndexSplit[[thisNuc]]],col=nucColor[thisNuc],bg=nucColor[thisNuc],type="b",pch=flowsSinceLastPch[1+flowsSinceLast])
    }
    title(sprintf("RMS flow residual\n%d %s wells, %s region",x$count[[wellType]],wellType,names(data)[iRegion]))
    legend(0.78*max(x$flow),max(ylim),flowsSinceLastLegendText,pch=flowsSinceLastLegendPch,title=flowsSinceLastLegendTitle,cex=0.8)
    legend(0.60*max(x$flow),max(ylim),c("A","C","G","T"),lwd=3,col=nucColor,cex=0.8)
    dev.off()
    #system(sprintf("eog %s",plotFile))

    # Plot nuc step sizes
    if(!is.null(x$stepSize[[wellType]])) {
      stepSize <- x$stepSize[[wellType]]
      png(plotFile <- sprintf("%s/stepSize.%s.%s.png",plotDir,regionName,wellType),height=pngHeight,width=pngWidth)
      plot(range(x$flow),range(c(0,stepSize)),type="n",xlab="Flow",ylab="Nuc step size")
      for(thisNuc in c("A","C","G","T")) {
        flowsSinceLast <- c(0,diff(flowSplit[[thisNuc]]))
        lines(flowSplit[[thisNuc]],stepSize[flowIndexSplit[[thisNuc]]],bg=nucColor[thisNuc],col=nucColor[thisNuc],type="b",pch=flowsSinceLastPch[1+flowsSinceLast])
      }
      title(sprintf("Nuc step size (max-min)\n%d %s wells, %s region",x$count[[wellType]],wellType,names(data)[iRegion]))
      legend(0.78*max(x$flow),0.3*max(stepSize),flowsSinceLastLegendText,pch=flowsSinceLastLegendPch,title=flowsSinceLastLegendTitle,cex=0.8)
      legend(0.60*max(x$flow),0.3*max(stepSize),c("A","C","G","T"),lwd=3,col=nucColor,cex=0.8)
      dev.off()
      #system(sprintf("eog %s",plotFile))
    }
  }
}

# Key traces
if(nchar(libKey) > 1 && nchar(floworder) > 1) {
  idealKey <- seqToFlow(libKey,floworder,finishAtSeqEnd=TRUE)
  keyNucs <- unlist(strsplit(floworder,""))[1:length(idealKey)]
  posMerNucs  <- keyNucs[which(idealKey>0)]
  zeroMerNucs <- keyNucs[which(idealKey==1)]
  allNucs <- c(unique(posMerNucs),unique(zeroMerNucs))

  # Background-subtracted traces
  zeroMer <- as.list(names(data))
  names(zeroMer) <- names(data)
  for(iRegion in 1:length(data)) {
    if(length(zeroMerNucs)>0) {
      zeroMer[[iRegion]] <- as.list(zeroMerNucs)
      names(zeroMer[[iRegion]]) <- zeroMerNucs
      for(iNuc in 1:length(zeroMerNucs)) {
        thisNuc <- zeroMerNucs[iNuc]
        nucFlows <- which(idealKey==0 & keyNucs==thisNuc)
        zeroMer[[iRegion]][[iNuc]] <- apply(matrix(data[[iRegion]]$signal$nbrsub[nucFlows,],ncol=length(nucFlows)),1,mean)
      }
    }
  }

  # Background-subtracted traces
  bkgSub <- as.list(names(data))
  names(bkgSub) <- names(data)
  duplicatedNucs <- allNucs[duplicated(allNucs)]
  if(length(duplicatedNucs)>0) {
    for(iRegion in 1:length(data)) {
      bkgSub[[iRegion]] <- list()
      for(iNuc in 1:length(duplicatedNucs)) {
        thisNuc <- duplicatedNucs[iNuc]
        nucFlows <- which(idealKey>0 & keyNucs==thisNuc)
        for(nucFlow in nucFlows) {
          bkgSub[[iRegion]] <- c(bkgSub[[iRegion]], list(data[[iRegion]]$signal$nbrsub[nucFlow,]-zeroMer[[iRegion]][[thisNuc]]))
        }
      }
    }
  }

  if(length(duplicatedNucs)>0) {
    for(iRegion in 1:length(data)) {
      regionName <- names(data)[iRegion]
      outFileBase <- sprintf("%s/keyBkgSub.%s",plotDir,regionName)
      plotFile <- sprintf("%s.png",outFileBase)
      jsonBkgSubFile <- sprintf("%s.json",outFileBase)
      png(plotFile,height=pngHeight,width=pngWidth)
      ylim <- range(unlist(bkgSub))
      plot(range(frameStart),ylim,type="n",xlab="Time (s)",ylab="Background-Subtracted Signal",las=2)
      for(i in 1:length(bkgSub[[iRegion]])) {
        lines(frameStart,bkgSub[[iRegion]][[i]],col=nucColor[duplicatedNucs[i]],lwd=2)
      }
      title(sprintf("Background-subtracted key traces\n%d ISPs and %d empty wells\n%dx%d %s region, lower-left at (c%d,r%d)",
        data[[iRegion]]$count$bead,data[[iRegion]]$count$empty,
        data[[iRegion]]$xMax-data[[iRegion]]$xMin,data[[iRegion]]$yMax-data[[iRegion]]$yMin,
        regionName,
        data[[iRegion]]$xMin,data[[iRegion]]$yMin)
      )
      legend("topright",inset=0.01,c("A","C","G","T"),fill=nucColor,bty="n")
      dev.off()
      #system(sprintf("eog %s",plotFile))
      write(toJSON(
        list(
          "frameStart"    = c(frameStart),
          "nuc"           = duplicatedNucs,
          "incorporation" = bkgSub
        )
      ),file=jsonBkgSubFile)
    }
  }
  

  for(iRegion in 1:length(data)) {
    regionName <- names(data)[iRegion]
    png(plotFile <- sprintf("%s/keyFlows.%s.png",plotDir,regionName),height=pngHeight,width=pngWidth)
    ylim <- range(unlist(lapply(data,function(z){z$signal$nbrsub[1:length(idealKey),]})))
    plot(range(frameStart),ylim,type="n",xlab="Time (s)",ylab="Neighbor-Subtracted Signal",las=2)
    for(iFlow in 1:length(idealKey)) {
      lines(frameStart,data[[iRegion]]$signal$nbrsub[iFlow,],col=nucColor[data[[iRegion]]$nuc[iFlow]],lwd=2,lty=2-idealKey[iFlow])
    }
    title(sprintf("Neighbor-subtracted key traces\n%d ISPs and %d empty wells\n%dx%d region, lower-left at (c%d,r%d)",
      data[[iRegion]]$count$bead,data[[iRegion]]$count$empty,
      data[[iRegion]]$xMax-data[[iRegion]]$xMin,data[[iRegion]]$yMax-data[[iRegion]]$yMin,
      data[[iRegion]]$xMin,data[[iRegion]]$yMin)
    )
    dev.off()
    #system(sprintf("eog %s",plotFile))
  }
}
