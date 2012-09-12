
pngWidth <- 500
pngHeight <- 400
myColor <- rev(rainbow(10))

myBarplot <- function(y,...) {
  ylim <- c(0,max(y)*1.1)
  yrange <- ylim[2]-ylim[1]
  mids <- barplot(y,ylim=ylim,...)
  plotText <- paste(round(y),", ",round(100*y/sum(y)),"%",sep="")
  text(mids,y+0.02*yrange,plotText,adj=c(0.5,0),cex=1)
}

getParam = function(text, key, sep){
  line = text[grep(key, text)]
  value = unlist(strsplit(line,sep))[2]
  value = gsub(" ","",value)
  if (is.na(value)) value = ""
#  print(paste(line,value))
  return(as.numeric(value))
}

getBasecallerParam = function(text, key, adj=0){
  value = 0
  line = text[grep(key, text)]  
  for (n in 1:length(line)){      
      if(grepl("BkgModel:", line[n])) column = 5
      else column = 4
 #     print(strsplit(line[n], " +"))
      temp = unlist(strsplit(line[n], " +"))[column+adj]
      temp = gsub("([-,])","",temp)
      if (is.na(temp)) temp = 0
      temp = as.numeric(temp)    
      value = value + temp
   }
   return(value)
}

#######################################################
filterMetricsPlots = function(archivePath, plotDir)
  {
    file_path = file.path(archivePath,"ReportLog.html")
    if (!file.exists(file_path)) file_path = file.path(archivePath,"sigproc_results/sigproc.log")
    log <- readLines(file_path) 
    sep = "\t"  
 
    # Top-level breakdown
    breakdownWell <- c(
      "Beads"    = getParam(log, "Beads  :", sep),
      "Empty"   = getParam(log, "Empties:", sep),
      "Pinned"  = getParam(log, "Pinned :", sep),
      "Ignored"  = getParam(log, "Ignored:", sep)      
    )
    png(plotFile <- sprintf("%s/primary.png",plotDir),width=pngWidth,height=pngHeight)
    myBarplot(breakdownWell/1e3,beside=TRUE,las=2,ylab="Reads (1,000's)",main="Primary Well Categorization",col=myColor)
    dev.off()
    
    # Breakdown of bead wells
    breakdownBead <- c(
      "Library"  = getParam(log, "Library:", sep),      
      "TF"   = getParam(log, "TFBead :", sep),
      "Dud"  = getParam(log, "Duds   :", sep)      
    )    
    png(plotFile <- sprintf("%s/loaded.png",plotDir),width=pngWidth,height=pngHeight)
myBarplot(breakdownBead/1e3,beside=TRUE,las=2,ylab="Reads (1,000's)",main="Loaded Well Categorization",col=myColor)
dev.off()
    
    # Breakdown of Library wells            
    breakdownLib <- c(
      "Valid"  = getBasecallerParam(log, "Valid reads", 3),
      "Polyclonal" = getBasecallerParam(log, " Polyclonal ",-1),
      "Bad key"  = getBasecallerParam(log, "Bad key"),
      "HighPPF"  = getBasecallerParam(log, "High PPF"),            
      "High\nresidual"  = getBasecallerParam(log, "High residual"),
      "Zero\nbases" = getBasecallerParam(log, "Zero bases"),
      "Short,\nFiltered" = getBasecallerParam(log, "Short read") + getBasecallerParam(log, "Short after", 2) + getBasecallerParam(log, "Beverly filter ")
    )    
    png(plotFile <- sprintf("%s/library.png",plotDir),width=pngWidth,height=pngHeight)
myBarplot(breakdownLib/1e3,beside=TRUE,las=2,ylab="Reads (1,000's)",main="Library Well Categorization",col=myColor)
dev.off()
   
    # start HTML
    fName <- sprintf("%s/results.html",plotDir,sep="");
    fHtml <- file(fName,open="w");
    title = "Filter Metrics Plots";
    header = "";
    txtStream = "";
    txtStream = paste(txtStream,sprintf("<html>\n<head>\n<center>\n <h1>%s</h1>\n<head>\n<body>\n <h3>%s</h3>\n",title,header),sep="");
    
    # plots    
    txtStream = paste(txtStream,sprintf("<img src = \" %s \" ><br>\n","./library.png"),sep="");
    txtStream = paste(txtStream,sprintf("<img src = \" %s \" ><br>\n","./loaded.png"),sep="");
    txtStream = paste(txtStream,sprintf("<img src = \" %s \" ><br>\n","./primary.png"),sep="");
    
    # end HTML
    txtStream = paste(txtStream,"</body>\n</html>",sep="");
    write(txtStream,fHtml,append=FALSE);
    close(fHtml);
    
    # output    
    cat("Info\n");
    cat("25\n");
    cat("Filtering and categorization plots.\n");
  }
#######################################################

cmd.args <- commandArgs(trailingOnly = TRUE);
filterMetricsPlots(cmd.args[1], cmd.args[2]);
