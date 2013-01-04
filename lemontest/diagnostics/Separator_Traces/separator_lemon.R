##########################################################################################
#   Customer Support Archive plots
#   Adapted from cusSupRawPlots.R
#
#   @archivePath: unzipped customer archive path.
#   @plotDir : the directory containing the output plots
##########################################################################################

library(ggplot2)
library(Hmisc)

### Load separator trace

loadSepTrace2 = function(sepTraceFile,nFlows=7, nRegions=3, flowOrder) {
  dat = read.table(sepTraceFile); 
  rows = dat[,1];
  cols = dat[,2];          
  BF_NCOLS_CONST = 10*max(cols);
  idx = rows * BF_NCOLS_CONST + cols; #0-based index ???
  signals = list();       
  
  xRanges <- unique(rows);
  yRanges <- unique(cols);
  nPoints <- length(xRanges)/nRegions;
  
                                        # Set the regions
  regions = list();
  rNames <- c("Outlet","Middle","Inlet");
  for ( iRegion in (1:nRegions)){
    regions[[iRegion]] = list(minCol=yRanges[(iRegion-1)*nPoints+1],maxCol=yRanges[iRegion*nPoints],minRow=xRanges[(iRegion-1)*nPoints+1],maxRow=xRanges[iRegion*nPoints],name=rNames[iRegion]);
  }
  
  retSig = list();
  for( iFlow in (1:nFlows))
    {    
      signals = list();
      for (i in 1:length(regions)) 
        {                                                                                                        
          s = cols >= regions[[i]]$minCol & cols <= regions[[i]]$maxCol  & rows >= regions[[i]]$minRow & rows <= regions[[i]]$maxRow  & dat[,3] ==(iFlow-1);
          mIdx = cols[s] + rows[s] * BF_NCOLS_CONST ;
          name = rep(regions[[i]]$name, length(mIdx));
          nuc = rep(flowOrder[iFlow], length(mIdx));
          type = rep("Other", length(mIdx));                                                                       
          sig = list( Region=name,Type=(type), nuc=nuc, index=mIdx, signal=dat[s,4:dim(dat)[2]]);          
          signals[[i]] = sig;
        }                                                                                                                 
      
                                        #Concatenate signals into 1 list.
      retSig[[iFlow]] = signals[[1]];
      if (length(signals) > 1)
        {                                                                                                            
          for (ii in 2:length(signals)) 
            {         
              retSig[[iFlow]]$Type = c(as.character(retSig[[iFlow]]$Type), as.character(signals[[ii]]$Type));
              retSig[[iFlow]]$index = c(retSig[[iFlow]]$index, signals[[ii]]$index);
              retSig[[iFlow]]$Region = c(retSig[[iFlow]]$Region, signals[[ii]]$Region);
              retSig[[iFlow]]$signal = rbind(retSig[[iFlow]]$signal, signals[[ii]]$signal);
              retSig[[iFlow]]$nuc = c(retSig[[iFlow]]$nuc, signals[[ii]]$nuc);

            }                                                                                                                                   
        }     
      
    }      
  
  return(retSig);                                                                                                                       
}         

################################################

seqToFlow <- function(sequence,flowOrder,nFlow=NA,finishAtSeqEnd=FALSE) {
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
  hpIndex <- 1
  for(fIndex in 1:nFlow) {
    if(hpNuc[hpIndex] == f[fIndex]) {
      out[fIndex] <- hpLen[hpIndex]
      hpIndex <- hpIndex + 1
      if(hpIndex > hpN)
        break;
    } else {
      out[fIndex] <- 0
    }
  }
  if(finishAtSeqEnd) {
    out <- out[!is.na(out)]
  } else {
    out[is.na(out)] <- 0
  }

  return(out)
}

################################################

plotSigFlows = function(plotSig, title = "Plot") {

  sig = list();
  for (flow in 1:length(plotSig)){
    tpSig = plotSig[[flow]]  
    tp = data.frame(Type=as.factor(as.character(tpSig$Type)), Index=tpSig$index, Region=tpSig$Region, Nuc=tpSig$nuc, tpSig$signal) ;  
    sig1 = melt(tp, c("Type","Index","Region","Nuc"), c(5:ncol(tp)));
    colnames(sig1) = c("Type","Index","Region","Nuc","Frame","Counts");
    sig1$Type = as.factor(as.character(sig1$Type));
    sig1$Frame = as.numeric(sig1$Frame);
    sig1$Counts = as.numeric(sig1$Counts);
    
    sig = rbind(sig,sig1)
  }
 # ymax = max(apply(tpSig$signal,2,quantile, probs=.98));
 # ymin = min(apply(tpSig$signal,2,quantile, probs=.02));
 # ylim=c(ymin,ymax);
    
  g = ggplot(sig, aes(x=Frame,y=Counts,colour=Nuc));
  td = g + geom_point(aes(group=Index, colour=Nuc, fill=Nuc), data=sig, size=1, shape=1) +
    stat_summary(fun.data="median_hilow", geom="smooth", line=2, size=1.2, fill=I("black"), alpha=.4, conf.int=.5) +
      stat_summary(aes(y=Counts,x=Frame,group=Nuc,colour=Nuc),fun.y=median, geom="line", line=1, size=1.2, alpha=1 ) +
        scale_colour_brewer(pal="Set1") +
          opts(title=title)

  td = td + facet_grid(Type ~ Region);
  
  print(td);
}

getParam = function(params, key){
  line = params[charmatch(key, params)]
  value = unlist(strsplit(line,"="))[2]
  value = gsub(" ","",value)  
  return(value)
}

#######################################################
cusSupSepPlots = function(archivePath, plotDir)
  {
    flowOrder <- "TACGTACG"; 
    libkey <- "TCAG" ;
    numFlows <- 7 ;
    numRegions <- 3;
 #   onemerFlows <- c(1,3,6)
 #   zeromerFlows <- c(5,7,2,4)        
    sigproc_path = file.path(archivePath, "sigproc_results");
    temp = unlist(strsplit(archivePath,"/"));
    datName <- temp[length(temp)];
    if (file.exists(sigproc_path))  archivePath = sigproc_path;
    
    # get key and flowOrder from processParameters.txt
    raw_params <- readLines(file.path(archivePath,"processParameters.txt"))
    params <- raw_params[tail(grep("global", raw_params), n=1):length(raw_params)]
    temp = getParam(params,"flowOrder")
    if (!is.na(temp)) flowOrder = temp;
    temp = getParam(params,"libraryKey")
    if (!is.na(temp)) libkey = temp;
    temp = getParam(params,"minNumKeyFlows")
    if (!is.na(temp)) numFlows = temp;
    
    keyflows <- seqToFlow(libkey,flowOrder)[1:numFlows]
    flowOrder <- strsplit(flowOrder,"")[[1]][1:numFlows]
    libkey <- strsplit(libkey,"")[[1]]
        
    # get data
    unzippedFolder <- list.files(archivePath, full.names=TRUE);
    datFile <- c();
    datName <- c();
    for ( i in 1:length(unzippedFolder)){
      temp = unlist(strsplit(unzippedFolder[i],"/"));
      if(temp[length(temp)]=="separator.trace.txt") {
        datFile <- unzippedFolder[i];
      }
    }
    if(length(datFile) == 0){
      cat("N/A\n");
      cat("0\n");
      cat("Can not find the separator.trace.txt file\n");
      stop();
    }
    
    xl = c (17,45);
    retSig <- loadSepTrace2(datFile,numFlows,numRegions,flowOrder);
    
    # reorder by nuc and 1/0    
    plotSig <- list();
    for(ii in 1:sum(keyflows==1))
      plotSig[[ii]] = retSig[keyflows==1&flowOrder==libkey[ii]][[1]]
    for(ii in 1:sum(keyflows==0))
      plotSig[[sum(keyflows==1)+ii]] = retSig[keyflows==0&flowOrder==libkey[ii]][[1]]
    
    # start HTML
    fName <- sprintf("%s/results.html",plotDir,sep="");
    fHtml <- file(fName,open="w");
    title = "Separator Customer Support Archive Plots";
    header = datName;
    txtStream = "";
    txtStream = paste(txtStream,sprintf("<html>\n<head>\n<center>\n <h1>%s</h1>\n<head>\n<body>\n <h3>%s</h3>\n",title,header),sep="");

    # plot 1-mers
    png(sprintf("%s/onemer.png", plotDir), width=1150,  height=500);
    plotSigFlows(plotSig[1:sum(keyflows==1)], 'Key 1-mer Flows');
    dev.off();
    txtStream = paste(txtStream,sprintf("<img src = \" %s \" ><br>\n","./onemer.png"),sep="");
         
    # plot 0-mers
    png(sprintf("%s/zeromer.png", plotDir), width=1150,  height=500);
    plotSigFlows(plotSig[sum(keyflows==1)+1:sum(keyflows==0)], 'Key 0-mer Flows');
    dev.off();     
    txtStream = paste(txtStream,sprintf("<img src = \" %s \" ><br>\n","./zeromer.png"),sep="");
   
    # plot subtracted
    zmerSubSig = list();
    for(ii in 1:sum(keyflows==1))
    {
	    zmerSubSig[[ii]]= plotSig[[ii]];
	    zmerSubSig[[ii]]$signal=(plotSig[[ii]]$signal-plotSig[[ii+sum(keyflows==1)]]$signal);
    }
    png(sprintf("%s/subtracted.png", plotDir), width=1150,  height=500);
    plotSigFlows(zmerSubSig, 'Zeromer-subtracted');
    dev.off();     
    txtStream = paste(txtStream,sprintf("<img src = \" %s \" ><br>\n","./subtracted.png"),sep="");
    
    
    # end HTML
    txtStream = paste(txtStream,"</body>\n</html>",sep="");
    write(txtStream,fHtml,append=FALSE);
    close(fHtml);
    
    
    # output    
    cat("Info\n");
    cat("20\n");
    cat("Key flows raw plots from Separator.\n");
  }
#######################################################

cmd.args <- commandArgs(trailingOnly = TRUE);
cusSupSepPlots(cmd.args[1], cmd.args[2]);
