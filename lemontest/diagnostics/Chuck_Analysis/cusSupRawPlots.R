##########################################################################################
#   Customer Support Archive plots
#   last change: Aug 18 -- get the expName from the cusZipSupFile
#   Aug 17 --- takes in zipfile instead of analysis dir.
#   Thang Vu - August 16
#
#   @zipCusSupFile: customer archive zip file with full path.
#   @plotDir : the directory containing the output plots
##########################################################################################

library(ggplot2)
library(Hmisc)

### Load separator trace

loadSepTrace2 = function(sepTraceFile,nFlows=7, nRegions=3, smooth=0) {
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
          type = rep("Other", length(mIdx));                                                                       
          sig = list( Region=name,Type=(type), index=mIdx, signal=dat[s,4:dim(dat)[2]]);
          if (smooth > 0)
            {
              sig$signal = t(apply(sig$signal, 1, medSmooth, window=smooth))
            }
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
            }                                                                                                                                   
        }     
      
    }      
  
  return(retSig);                                                                                                                       
}         

################################################

plotSig2 = function(tpSig, title = "Plot", toPlot = c(), ylim = c(), xlim = c(), doRegionFacet = F) {
  tpSig$Type[tpSig$Type != "Empty"] = "Other";
  if (length(xlim)==2)
    {
      ymax = max(apply(tpSig$signal[,xlim[1]:xlim[2]],2,quantile, probs=.98));
      ymin = min(apply(tpSig$signal[,xlim[1]:xlim[2]],2,quantile, probs=.02));
    } else {
      ymax = max(apply(tpSig$signal,2,quantile, probs=.98));
      ymin = min(apply(tpSig$signal,2,quantile, probs=.02));
    }
  ylim=c(ymin,ymax);
  tp = data.frame(Type=as.factor(as.character(tpSig$Type)), Index=tpSig$index, Region=tpSig$Region, tpSig$signal) ;
  colnames(tp) = sub("X","", colnames(tp));
  sig.mx = melt(tp, c("Type","Index","Region"), c(4:ncol(tp)));
  colnames(sig.mx) = c("Type","Index","Region","Frame","Counts");
  sig.mx$Type = as.factor(as.character(sig.mx$Type));
  sig.mx$Frame = as.numeric(sig.mx$Frame);
  sig.mx$Counts = as.numeric(sig.mx$Counts);
  g = ggplot(sig.mx, aes(x=Frame,y=Counts,colour=Region),ylim=ylim);
  td = g + geom_line(aes(group=Index, colour=Region, fill=Region), data=sig.mx, alpha=.3) +
    stat_summary(fun.data="median_hilow", geom="smooth", line=2, size=1.2, fill=I("black"), alpha=.4, conf.int=.5) +
      stat_summary(aes(y=Counts,x=Frame,group=Region,colour=Region),fun.y=median, geom="line", line=2, size=1.2, alpha=1 ) +
        scale_colour_brewer(pal="Set1") +
          opts(title=title)
  if (doRegionFacet) {
    td = td + facet_grid(Type ~ Region);
  } else {
    td = td + facet_grid(Type ~ .);
  }
  if (length(ylim) > 0) {
    td = td + ylim(ylim);
  }
  if (length(xlim) > 0) {
    td = td + xlim(xlim);
  }
  print(td);
}

#######################################################
writeHtml <- function(plotDir,expName,nFlows,flows,changedFlows,nucs,xl){
  
  fName <- sprintf("%s/results.html",plotDir,sep="");
  fHtml <- file(fName,open="w");
  title = "Customer Support Archive Plots";
  header = expName;
  txtStream = "";
                                        # Beginning of the html file
  txtStream = paste(txtStream,sprintf("<html>\n<head>\n <title>%s</title>\n<head>\n<body>\n <h3>%s</h3>\nT",title,header),sep="");
                                        #Body part
  for(i in 1:nFlows)
    {
      flow = changedFlows[i];
      nuc = nucs[flow%%4+1];
      figName = sprintf("./raw-flow-%s-%d %s.png",nuc, flow, expName);
      txtStream = paste(txtStream,sprintf("<img src = \" %s \" >\n",figName),sep="");
    }
                                        #0mer-plots
  for(i in 1:3){
    flow = flows[i];
    nuc = nucs[flow%%4+1];
    figName = sprintf("./zeromer-subtracted raw-flow-%s-%s.png",nuc, expName);
    txtStream = paste(txtStream,sprintf("<img src = \" %s \" >\n",figName),sep="");
  } 
                                        # Zoomed-in plots
  for(i in 1:nFlows)
    {
      flow = changedFlows[i];
      nuc = nucs[flow%%4+1];
      figName = sprintf("./raw-flow-%d-%d-%s-%d %s.png", xl[1],xl[2],nuc, flow, expName);
      txtStream = paste(txtStream,sprintf("<img src = \" %s \" >\n",figName),sep="");
    }
                                        # End of the html file
  txtStream = paste(txtStream,"</body>\n</html>",sep="");
  write(txtStream,fHtml,append=FALSE);
  close(fHtml);
}

#######################################################
cusSupRawPlots = function(archivePath, plotDir)
  {
    flows <- c(0, 1, 2, 3, 4, 5, 6, 7);
    changedFlows <- c(0, 4, 1, 5, 2, 6, 3, 7);
    nucs <- c("T","A","C","G");
    expName <- "archive";
    unzippedFolder <- list.files(archivePath, full.names=TRUE);
    datFile <- c();
    for ( i in 1:length(unzippedFolder)){
      temp = unlist(strsplit(unzippedFolder[i],"/"));
      if(temp[length(temp)]=="separator.trace.txt") datFile <- unzippedFolder[i];
    }
    if(length(datFile) == 0){
      cat("Fail\n");
      cat("100\n");
      cat("Can not find the separator.trace.txt file\n");
      stop();
    }
    
    xl = c (17,45);
    retSig <- loadSepTrace2(datFile);
    for(i in 1:length(retSig)){
      flow = flows[i];
      nuc = nucs[flow%%4+1]
                                        # Raw plot
      png(sprintf("%s/raw-flow-%s-%d %s.png", plotDir, nuc, flow, expName), width=850,  height=600);
      plotSig2(retSig[[i]], sprintf( 'Raw Flow %d (Nuc %s) \n%s', flow, nuc, expName));
      dev.off();
                                        # Zoomed-in raw plot
      png(sprintf("%s/raw-flow-%d-%d-%s-%d %s.png", plotDir, xl[1],xl[2],nuc, flow, expName), width=850,  height=600);
      plotSig2(retSig[[i]], sprintf( 'Raw Flow %d (Nuc %s)\n%s', flow, nuc, expName),xlim=xl,doRegionFacet=TRUE);
      dev.off();
    }
                                        #0mer-subtracted plots.
    zmerSubSig = list();
    factor <- c(1,-1,1);
    for(ii in c(1,2,3))
      {
	zmerSubSig[[ii]]= retSig[[ii]];
	zmerSubSig[[ii]]$signal=factor[ii]*(retSig[[ii]]$signal-retSig[[ii+4]]$signal);
      }
    
    flow1 <- c(0,5,2);
    flow2 <- c(4,1,6);
    
    for(i in 1:3){
      flow = flows[i];
      nuc = nucs[flow%%4+1];
      png(sprintf("%s/zeromer-subtracted raw-flow-%s-%s.png", plotDir, nuc, expName), width=850, height=600);
      plotSig2(zmerSubSig[[i]], sprintf( 'Raw Flow %d - %d (Nuc %s) \n%s', flow1[i],flow2[i] ,nuc, expName));
      dev.off();
    }
                                        #$ Output to html file
    writeHtml(plotDir,expName,length(retSig),flows,changedFlows,nucs,xl);
    cat("Info\n");
    cat("25\n");
    cat("View various plots for more information.\n");
  }
#######################################################

cmd.args <- commandArgs(trailingOnly = TRUE);
cusSupRawPlots(cmd.args[1], cmd.args[2]);
