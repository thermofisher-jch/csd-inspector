OT_plots<-function(work_dir,file_name,machine,target,version) { 
    
	#One of these flags becomes true
    
    OT2=FALSE
    OT1=FALSE
	OTDL=FALSE

    dataSet <- read.csv(paste(work_dir,file_name,sep=""),header=TRUE)

    #check if the file is healthy; 
    header_len=length(names(dataSet))


    #There are 4 types of file:
    #OT2 has 36 columns for TS4
    if( header_len ==36){
        OT2=TRUE;
        machine="OT2"
        header=c("Step","Thermistor0Temperature","Thermistor1Temperature","Thermistor2Temperature","Thermistor3Temperature",
            "Thermistor4Temperature","P_SensorCur.Pressure","RawA2D","TEC0CurrentTemp","SetTemp","PWMdutyCycle","OnTime",
            "TecDir","AdjustedSetTemp","Heater0CurrentTemp","SetTemp.1","PWMdutyCycle.1","Heater1CurrentTemp","SetTemp.2",
            "PWMdutyCycle.2","MotorPowerOscillation","Raw","SolenoidPumpTotalVolume","DispensedVolume","OilPumpStatus",
            "SamplePumpStatus","Pin0Pin","Pin1Pin","Pin2Pin","Pin3Pin","Pin4Pin","Pin5Pin","Flowmeter0","OilPumpPosition",
            "SamplePumpPosition","Timestamp")
        #stop if the header names of the file are not as expected for OT2
        if( ! (all(names(dataSet)==header ))) {
            cat("Warning\n");
            cat("30\n");
            cat("The file's header is different from what is expected\n");
            return();
        }
    }else if( header_len ==34){
        OT2=TRUE;
        machine="OT2"
        header=c("Step","Thermistor0Temperature","Thermistor1Temperature","Thermistor2Temperature","Thermistor3Temperature",
            "Thermistor4Temperature","P_SensorCur.Pressure","RawA2D","TEC0CurrentTemp","SetTemp","PWMdutyCycle","OnTime",
            "TecDir","AdjustedSetTemp","Heater0CurrentTemp","SetTemp.1","PWMdutyCycle.1","Heater1CurrentTemp","SetTemp.2",
            "PWMdutyCycle.2","MotorPowerOscillation","Raw","SolenoidPumpTotalVolume","DispensedVolume","OilPumpStatus",
            "SamplePumpStatus","Pin0Pin","Pin1Pin","Pin2Pin","Pin3Pin","Pin4Pin","Pin5Pin","Flowmeter0","Timestamp")
        #stop if the header names of the file are not as expected for OT2
        if( ! (all(names(dataSet)==header ))) {
            cat("Warning\n");
            cat("30\n");
            cat("The file's header is different from what is expected\n");
            return();
        }
    }else if(header_len ==32) {
        OT1=TRUE;
        machine="OT1"
        target=""
        version=""
        #OT1 has 32 columns and does not have pump data
        header=c("Thermistor0Temperature","Thermistor1Temperature","Thermistor2Temperature","Thermistor3Temperature",
            "Thermistor4Temperature","Heater0CurrentTemp","SetTemp","PWMdutyCycle","Heater1CurrentTemp","SetTemp.1",
            "PWMdutyCycle.1","Heater2CurrentTemp","SetTemp.2","PWMdutyCycle.2","Heater3CurrentTemp","SetTemp.3",
            "PWMdutyCycle.3","PressureAdj.SetPt","SetPt","P_SensorCur.Pressure","RawA2D","MotorPowerOscillation",
            "Valve0","Valve1","Valve2","Valve3","Valve4","Valve5","Valve6","Fan0","Fan1","Timestamp")

        #stop if the header names of the file are not as expected for OT1
        if( ! (all(names(dataSet)==header))) {
            cat("Warning\n");
            cat("30\n");
            cat("The file's header is different from what is expected\n");
            return();
            
        }
	}else if(header_len ==33) {
        OTDL=TRUE;
        machine="OTDL"
        target=""
        version=""
        #OTDL has 33 columns and does not have pump data either
        header=c("Thermistor0Temperature","Thermistor1Temperature","Thermistor2Temperature","Thermistor3Temperature",
            "Thermistor4Temperature","Heater0CurrentTemp","SetTemp","PWMdutyCycle","Heater1CurrentTemp","SetTemp.1",
            "PWMdutyCycle.1","Heater2CurrentTemp","SetTemp.2","PWMdutyCycle.2","Heater3CurrentTemp","SetTemp.3",
            "PWMdutyCycle.3","PressureAdj.SetPt","SetPt","P_SensorCur.Pressure","RawA2D","MotorPowerOscillation",
            "Valve0","Valve1","Valve2","Valve3","Valve4","Valve5","Valve6","Valve7","Fan0","Fan1","Timestamp")

        # #stop if the header names of the file are not as expected for OTDL
        if( ! (all(names(dataSet)==header))) {
            cat("Warning\n");
            cat("30\n");
            cat("Stopping: the file header is different from what is expected\n");
            return();
        }
    }else{
        cat("Warning\n");
        cat("30\n");
        cat("The file's header length is different from what is expected\n");
        return();
        
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
    if(!(is.numeric(dataSet$Thermistor0Temperature) & is.numeric(dataSet$Thermistor1Temperature) & is.numeric(dataSet$Thermistor2Temperature) & is.numeric(dataSet$Thermistor3Temperature))) {
        cat("<h3 align=\"center\">The data temperatures cannot be plotted: verify all the data are numeric</h3>\n",sep=" ",file=f,append=TRUE)  
        cat("The data temperatures cannot be plotted: verify all the data are numeric")
    }else{
        graph <- paste(work_dir,"p1.png",sep="")
        png(graph)

        plot(seq(1,l)/60,ylim=(c(0,100)),dataSet$Thermistor0Temperature,las=1, yaxp= c(0,100,10), type="l",col="dark green",xlab="Time (minutes)",ylab="Temperature (Celsius)",main="Thermistor Temperature")

        lines(seq(1,l)/60,dataSet$Thermistor1Temperature,type="l",col="dark blue")
        lines(seq(1,l)/60,dataSet$Thermistor2Temperature,type="l",col="red")
        lines(seq(1,l)/60,dataSet$Thermistor3Temperature,type="l",col="orange")
        legend("bottomright",cex=0.8,c("T0-Ambient","T1-Heated Lid","T2-Thermal Cycling","T3-Internal Case"),col=c("dark green","dark blue","red","orange"),lty=1)
        dev.off()
        cat("<img src=\"p1.png\" />", file=f, append=TRUE)
    }

    #This is plot 2 Sensor pressure
    #verify the data can be plotted
    if(!(is.numeric(dataSet$P_SensorCur.Pressure))) {
        cat("<h3 align=\"center\">The sensor pressure data cannot be plotted: the data is not numeric</h3>\n",sep=" ",file=f,append=TRUE)
        cat("The sensor pressure data cannot be plotted: the data is not numeric\n")
    }else{
        graph <- paste(work_dir,"p2.png",sep="")
        png(graph)
        plot(seq(1,l)/60,las=1,dataSet$P_SensorCur.Pressure,type="l",col="dark blue",xlab="Time (minutes)",ylab="Pressure (PSI)",main="Sensor Presure")

        dev.off()

        cat("<img src=\"p2.png\" /><br />", file=f, append=TRUE)
    }



    #For OT1 Motor Oscillation data comes in a list of values separated by ":", we need to extract the first value to be plotted
    #
    if(OT1==TRUE|OTDL==TRUE){
        MPO=(as.integer(sapply(strsplit(as.character(dataSet$MotorPowerOscillation),":"),"[[",1)))
    }else{
        MPO=dataSet$MotorPowerOscillation
    }

    #plot 3 Motor oscillation
    #verify the data can be plotted
    if(!(is.numeric(MPO))) {
        cat("<h3 align=\"center\">The Motor Power Oscillation data cannot be plotted: the data is not numeric</h3>\n",sep=" ",file=f,append=TRUE)
        cat("The Motor Power Oscillation data cannot be plotted: the data is not numeric")
    }else{
        graph <- paste(work_dir,"p3.png",sep="")
        png(graph)
        plot(seq(1,l)/60,las=1,MPO,type="l",col="dark blue",xlab="Time (minutes)",ylab="Signal",main="Motor Power Oscillation")

        dev.off()

        cat("<img src=\"p3.png\" />", file=f, append=TRUE)
    }

	if(OT2==TRUE){
        #flowmeter test only for OT2
        if(!(is.numeric(dataSet$Flowmeter0))) {
            cat("<h3 align=\"center\">Unable to test Flowmeter: the data is not numeric</h3>\n",sep=" ",file=f,append=TRUE)
            cat("Unable to test SFlowmeter: the data is not numeric")
        }else{
             graph <- paste(work_dir,"p4.png",sep="")
            png(graph)
            plot(seq(1,l)/60,las=1,dataSet$Flowmeter0,type="l",col="dark blue",xlab="Time (minutes)",ylab="Liters per minute",main="Flowmeter")

            dev.off()

            cat("<img src=\"p4.png\" /><br />", file=f, append=TRUE)           
        }    
	}
    #finish report
    cat("\n<hr size=1>\n</body></html>",file=f,append=TRUE)
    cat("Info\n");
    cat("20\n");
}

cmd.args <- commandArgs(trailingOnly = TRUE);

OT_plots(cmd.args[1], cmd.args[2], cmd.args[3], cmd.args[4], cmd.args[5]);

