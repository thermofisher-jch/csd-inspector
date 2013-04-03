OT_plots<-function(work_dir,file_name,machine,target,version) {
    
    

    # type_of_data<-strsplit(file_name,"_")
    
    # machine<-type_of_data[[1]][1]
    #machine= "machine"
    # target<-type_of_data[[1]][2]
    #target="target"
    dataSet <- read.csv(paste(work_dir,file_name,sep=""),header=TRUE)

    #check the file is healthy; 
    #vector "header" contains the expected header of the file

    header=c("Step","Thermistor.0.Temperature","Thermistor.1.Temperature","Thermistor.2.Temperature",
        "Thermistor.3.Temperature","Thermistor.4.Temperature","P_Sensor..Cur..Pressure","Raw.A2D",
        "TEC.0.Current.Temp","Set.Temp","PWM.duty.Cycle","On.Time","Tec.Dir","Adjusted.Set.Temp",
        "Heater.0.Current.Temp","Set.Temp.1","PWM.duty.Cycle.1","Heater.1.Current.Temp","Set.Temp.2",
        "PWM.duty.Cycle.2","Motor.Power..Oscillation","Raw","Solenoid.Pump..Total.Volume",
        "Dispensed.Volume","Oil.Pump.Status","Sample.Pump.Status","Pin.0.Pin","Pin.1.Pin",
        "Pin.2.Pin","Pin.3.Pin","Pin.4.Pin","Pin.5.Pin","Flowmeter0","Timestamp")

    #stop if the header of the file is not as expected
    if(! all(names(dataSet)==header)) {
        cat("Warning\n");
        cat("30\n");
        cat("Stopping: the file header is different from what is expected\n")
        cat("Verify that the header and structure of your file is exactly as follows:\n\n")
        cat(paste("Step,Thermistor-0 Temperature,Thermistor-1 Temperature,Thermistor-2 Temperature,",
            "Thermistor-3 Temperature,Thermistor-4 Temperature,P_Sensor- Cur. Pressure, ",
            "Raw A2D,TEC-0 Current Temp, Set Temp, PWM duty Cycle, On Time, Tec Dir, ",
            "Adjusted Set Temp,Heater-0 Current Temp, Set Temp, PWM duty Cycle,Heater-1 Current Temp, ",
            "Set Temp, PWM duty Cycle,Motor Power- Oscillation, Raw,Solenoid Pump- Total Volume, ",
            "Dispensed Volume, Oil Pump Status, Sample Pump Status,Pin-0 Pin,Pin-1 Pin,Pin-2 Pin,",
            "Pin-3 Pin,Pin-4 Pin,Pin-5 Pin,Flowmeter0,Timestamp",sep=""))
        cat("The file's header is different from what was expected\n");
        stop()
    }
    
    #The name of the resulting report
    mainHTML<-"report.html"
    
    f=paste(work_dir,"results.html",sep="")
    
    #make it nicer by adding a css file
    cat("<html><link rel=stylesheet href=some.css type=text/css>\n</head><body>\n",file=f,append=FALSE)
    cat(paste("<h1 align=\"center\">Plots for",machine,target,version,"</h1>\n",sep=" "),file=f,append=TRUE)

    #get the number of rows to be plotted
    l=nrow(dataSet)
    
    #This is plot 1
    #verify that the data can be plotted
    if(!(is.numeric(dataSet$Thermistor.0.Temperature) & is.numeric(dataSet$Thermistor.1.Temperature) & is.numeric(dataSet$Thermistor.2.Temperature) & is.numeric(dataSet$Thermistor.3.Temperature))) {
        cat("<h3 align=\"center\">The data temperatures cannot be plotted: verify all the data are numeric</h3>\n",sep=" ",file=f,append=TRUE)  
        cat("The data temperatures cannot be plotted: verify all the data are numeric")
    }else{
        graph <- paste(work_dir,"p1.png",sep="")
        png(graph)

        plot(seq(1,l)/60,ylim=(c(0,100)),dataSet$Thermistor.0.Temperature,las=1, yaxp= c(0,100,10), type="l",col="dark green",xlab="Time (minutes)",ylab="Temperature (Celsius)",main="Thermistor Temperature")

        lines(seq(1,l)/60,dataSet$Thermistor.1.Temperature,type="l",col="dark blue")
        lines(seq(1,l)/60,dataSet$Thermistor.2.Temperature,type="l",col="red")
        lines(seq(1,l)/60,dataSet$Thermistor.3.Temperature,type="l",col="orange")
        legend("bottomright",cex=0.8,c("T0-Ambient","T1-Heated Lid","T2-Thermal Cycling","T3-Internal Case"),col=c("dark green","dark blue","red","orange"),lty=1)
        dev.off()

        cat("<img src=\"p1.png\" />", file=f, append=TRUE)
    }

    #This is plot 2
    #verify the data can be ploted
    if(!(is.numeric(dataSet$P_Sensor..Cur..Pressure))) {
        cat("<h3 align=\"center\">The sensor pressure data cannot be plotted: the data is not numeric</h3>\n",sep=" ",file=f,append=TRUE)
        cat("The sensor pressure data cannot be plotted: the data is not numeric")
    }else{
        graph <- paste(work_dir,"p2.png",sep="")
        png(graph)
        plot(seq(1,l)/60,las=1,dataSet$P_Sensor..Cur..Pressure,type="l",col="dark blue",xlab="Time (minutes)",ylab="Pressure (PSI)",main="Sensor Presure")
        dev.off()

        cat("<img src=\"p2.png\" /><br />", file=f, append=TRUE)
    }

    #Check if there is an error (a value is 5) in the pump status
    if(!(is.numeric(dataSet$P_Sensor..Cur..Pressure))) {
        cat("<h3 align=\"center\">Unable to test Sample pump status: the data is not numeric</h3>\n",sep=" ",file=f,append=TRUE)
        cat("Unable to test Sample pump status: the data is not numeric")
    }else{
        
        if(5 %in% dataSet$Sample.Pump.Status){
            cat("<h2 align=\"center\" style=\"color: red\">Sample pump status test: ERROR detected value of 5</h3>\n",sep=" ",file=f,append=TRUE)
        }else{
            cat("<h2 align=\"center\" style=\"color: lime\">Sample pump status test: OK</h3>\n",sep=" ",file=f,append=TRUE)
        }
    }
            
    #finish report
    cat("\n<hr size=1>\n</body></html>",file=f,append=TRUE)
    cat("Info\n");
    cat("20\n");
    

}

cmd.args <- commandArgs(trailingOnly = TRUE);
OT_plots(cmd.args[1], cmd.args[2], cmd.args[3], cmd.args[4], cmd.args[5]);


