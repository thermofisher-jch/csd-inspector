#!/usr/bin/env python

import os.path
import numpy as np
import matplotlib.pyplot as plt
import cv2 #requires install of opencv-python==4.2.0.32
import scipy.signal
import logging
import json
from numpy import round, divide
from django.conf import settings

logger = logging.getLogger(__name__)
def FindPeaks(image):
    #try to look for a peak detection or sharp corner detection
    peaks = cv2.goodFeaturesToTrack(image,1000,0.5,2)
    peaks = np.int0(peaks)
    #for each peak detected determine if it is a real peak through algorithm
    # for each peak check if there is another non-zero point within +- 4-5 pixels. 
    counter = 0 #measures the point score for determining if true peak, good on score 3 or higher
    true_peaks=[]
    pixel_threshold=0
    for pixel_threshold in range(4,50):#grow the scan area for non-zero pixels, all successes are recorded
        for k in peaks:
            if ((k[0,0] +pixel_threshold+2) >= 172) or ((k[0,0] - pixel_threshold-2) < 0) or ((k[0,1] +pixel_threshold+2) >= 315) or ((k[0,1] -pixel_threshold-2) >= 315) :
                continue
            if  image[k[0,1]+ pixel_threshold ,k[0,0]] == 0 and image[k[0,1]+pixel_threshold+1,k[0,0]] == 0:
                counter +=1
            if  image[k[0,1]-pixel_threshold,k[0,0]] == 0 and image[k[0,1]-pixel_threshold-1,k[0,0]] == 0:
                counter +=1
            if  image[k[0,1],k[0,0]-pixel_threshold] == 0 and image[k[0,1],k[0,0]-pixel_threshold-1] == 0:
                counter +=1
            if  image[k[0,1],k[0,0]+pixel_threshold] == 0 and image[k[0,1],k[0,0]+pixel_threshold+1] == 0:
                counter +=1
            if  k[0,0] >=160:
                counter =0
            if counter > 3:
                true_peaks.append(k)
            counter=0
    #need to eliminate dulpicates from true_peaks and sort the list
    true_peaks_sorted = []
    for i in range(len(true_peaks)):
        true_peaks_sorted.append(tuple(true_peaks[i][0]))
    true_peaks_sorted.sort(key= lambda y:y[0])
    true_peaks_filtered=[]
    for i in true_peaks_sorted:
        if i not in true_peaks_filtered:
            true_peaks_filtered.append(i)
    #filter for multiple y for each x out
    true_peaks_filtered_vertically=[]
    for i in range(len(true_peaks_filtered)-1):
        if ( not true_peaks_filtered[i][0]== true_peaks_filtered[i+1][0]) and (not true_peaks_filtered[i][0]== true_peaks_filtered[i-1][0]):
            true_peaks_filtered_vertically.append(true_peaks_filtered[i])
    # filtering is deleting some important points need to refine (maybe run vertical test recording from top down and down top the first point encountered in each direction)
    peaks_fitted=[]
    if len(true_peaks_filtered_vertically)>4:
        x, y = np.array(true_peaks_filtered_vertically).T
        x_axis=np.linspace(0, max(x),max(x))
        poly_A=np.polyfit(x,y,len(x))
        fit= np.polyval(poly_A,x_axis)
        peaks_max= list(scipy.signal.argrelextrema(np.array(fit,),np.greater))
        peaks_min=  list(scipy.signal.argrelextrema(np.array(fit),np.less))
        for i in range(len(peaks_max[0])):
            peaks_fitted.append(peaks_max[0][i])
        for i in range(len(peaks_min[0])):
            peaks_fitted.append(peaks_min[0][i])
        peaks_fitted.sort()
    return np.array(true_peaks_filtered) ,np.array(peaks_fitted)

def RawTrace_Analyze(path):
    #load image and remove everything but signal lines, then split into A,C,G,T
    image = cv2.imread(path)
    #delete the background and edges of the whole image
    i=0
    j=0
    rows, columns, channels = image.shape
    for i in range(0,rows):
        for j in range(0,columns):
            if image[i,j,0] == image[i,j,1] == image[i,j,2]:
                image[i,j]= [0,0,0]
            if (i >=60 and i <=142 ) and ((j >=46 and j <= 53) or (j >=236 and j <=243 ) or (j >=426 and j <= 453) or (j >=616 and j <= 623)):
                image[i,j]= [0,0,0]
    #split the images into A,C,G,T
    image_A = image[50:365,38:210]
    image_A_Gray = cv2.cvtColor(image_A,cv2.COLOR_BGR2GRAY)
    image_C = image[50:365,228:400]
    image_C_Gray = cv2.cvtColor(image_C,cv2.COLOR_BGR2GRAY)
    image_G = image[50:365,418:590]
    image_G_Gray = cv2.cvtColor(image_G,cv2.COLOR_BGR2GRAY)
    image_T = image[50:365,608:780]
    image_T_Gray = cv2.cvtColor(image_T,cv2.COLOR_BGR2GRAY)
    # Analyze image to find irregular patterns
    true_peaks_A,fitted_peaks_A = FindPeaks(image_A_Gray)
    true_peaks_C,fitted_peaks_C = FindPeaks(image_C_Gray)
    true_peaks_G,fitted_peaks_G = FindPeaks(image_G_Gray)
    true_peaks_T,fitted_peaks_T = FindPeaks(image_T_Gray)

    non_zeroes_A_top=[]
    non_zeroes_C_top=[]
    non_zeroes_G_top=[]
    non_zeroes_T_top=[]
    non_zeroes_A_bot=[]
    non_zeroes_C_bot=[]
    non_zeroes_G_bot=[]
    non_zeroes_T_bot=[]
    for i in range(0,315):
        if not image_A_Gray[i][160]==0:
            non_zeroes_A_top.append(i) 
        if not image_A_Gray[i][10]==0:
            non_zeroes_A_bot.append(i)
    for i in range(0,315):
        if not image_C_Gray[i][160]==0:
            non_zeroes_C_top.append(i) 
        if not image_C_Gray[i][10]==0:
            non_zeroes_C_bot.append(i)
    for i in range(0,315):
        if not image_G_Gray[i][160]==0:
            non_zeroes_G_top.append(i) 
        if not image_G_Gray[i][10]==0:
            non_zeroes_G_bot.append(i)
    for i in range(0,315):
        if not image_T_Gray[i][160]==0:
            non_zeroes_T_top.append(i) 
        if not image_T_Gray[i][10]==0:
            non_zeroes_T_bot.append(i)
    range_100_A =np.average(non_zeroes_A_bot)-np.average(non_zeroes_A_top)
    range_100_C =np.average(non_zeroes_C_bot)-np.average(non_zeroes_C_top)
    range_100_G =np.average(non_zeroes_G_bot)-np.average(non_zeroes_G_top)
    range_100_T =np.average(non_zeroes_T_bot)-np.average(non_zeroes_T_top)
    #report out the analysis report
    report_out=''
    if len(fitted_peaks_A) >1 or range_100_A <= 50:
            report_out+="RawTrace: Irregular artifacts found in Nuc: A"
    if len(fitted_peaks_C) >1 or range_100_C <= 50:
            report_out+="RawTrace: Irregular artifacts found in Nuc: C"
    if len(fitted_peaks_G) >1 or range_100_G <= 50:
            report_out+="RawTrace: Irregular artifacts found in Nuc: G"
    if len(fitted_peaks_T) >1 or range_100_T <= 50:
            report_out+="RawTrace: Irregular artifacts found in Nuc: T"  

    return report_out


def test_rawTrace(archive_path, output_path):
    """Executes the test"""

    raw_trace_path = os.path.join(archive_path, "rawTrace")
    if not os.path.exists(raw_trace_path):
        return print_failed("Could not find rawTrace!")

    message = ""

    for lane in range(1, 5):
        lane_file_path = os.path.join(
            raw_trace_path, "plots_lane_{}".format(lane)
        )
        if os.path.exists(lane_file_path):
            #get path_to_filethe paths to the nucStep image
            path_nucSteps_inlet=os.path.join(
                lane_file_path,"nucSteps.inlet.bead.png")
            path_nucSteps_middle=os.path.join(
                lane_file_path,"nucSteps.middle.bead.png")
            path_nucSteps_outlet=os.path.join(
                lane_file_path,"nucSteps.outlet.bead.png")
            logger.warn("RawTrace path to inlet:" + path_nucSteps_inlet)
            logger.warn("RawTrace path to middle:" + path_nucSteps_middle)
            logger.warn("RawTrace path to outlet:" + path_nucSteps_outlet)
            #run the defect detection function
            tmpmsg=''
            tmpmsg += RawTrace_Analyze(path_nucSteps_inlet)
            tmpmsg += RawTrace_Analyze(path_nucSteps_middle)
            tmpmsg += RawTrace_Analyze(path_nucSteps_outlet)
            if tmpmsg:
                message += "RawTrace: Lane {} Irregular artifacts found\n".format(lane)
            # If any of the reports is populated then change the status to alert and link to a report
            
            

    return message

def test_BKQ(path_to_file):
    lower_limit = -10
    NucArray = ["T","C","A","G"]
    inlet = []
    middle = []
    outlet = []
    
    # read file
    with open(path_to_file, 'r') as myfile:
        data = myfile.read()

    # parse file
    JsData = json.loads(data)

    #y-coordinates for each nuc in inlet, middle, and outlet
    ExtractINC = JsData["incorporation"]
        
    # for i in range(np.asarray(ExtractINC["inlet"]).shape[0]):
    #     for j in range(np.asarray(ExtractINC["inlet"]).shape[1]):
    #         if np.asarray(ExtractINC["inlet"])[i,j] < lower_limit:
    #             inlet.append(NucArray[i])
    #             break

    for k in range(np.asarray(ExtractINC["middle"]).shape[0]):
        #logger.warn(" middle array " + str(np.asarray(ExtractINC["middle"])[k]))
        for l in range(np.asarray(ExtractINC["middle"]).shape[1]):
            if np.asarray(ExtractINC["middle"])[k,l] < lower_limit:
                middle.append(NucArray[k])
                break
           
    # for m in range(np.asarray(ExtractINC["outlet"]).shape[0]):
    #     for n in range(np.asarray(ExtractINC["outlet"]).shape[1]):
    #         if np.asarray(ExtractINC["outlet"])[m,n] < lower_limit:
    #             outlet.append(NucArray[m])
    #             break
    #logger.warn("middle "+str(len(middle)))
    if len(inlet) > 0 or len(middle) > 0 or len(outlet) > 0:
        return "Background-subtracted key traces test failed"
    else:
        return ""

def NucStepSize_test(path_to_file, lane):
    NucArray = ["T","C","A","G"]
    NucAvg = {}
    with open(path_to_file, 'r') as myfile:
        data = myfile.read()

    # parse file
    JsData = json.loads(data)
    
    lane_data=JsData["lane_"+str(lane)]["nucs"]
    for nuc in NucArray:
        cnt=0
        avg=0
        for entry in lane_data:
            avg += lane_data[entry][nuc]["raw_bead_zero"]["height"]
            avg += lane_data[entry][nuc]["raw_bead_one"]["height"]
            cnt+=1
        NucAvg[nuc]=avg/cnt
        
    logger.warn("NucAvg: "+str(NucAvg))
    
    failed=False
    if NucAvg["C"] > 2.0*NucAvg["T"] or NucAvg["C"] < NucAvg["T"]/2.0:
        failed=True
    if NucAvg["G"] > 2.0*NucAvg["T"] or NucAvg["G"] < NucAvg["T"]/2.0:
        failed=True
    if NucAvg["A"] > 2.0*NucAvg["T"] or NucAvg["A"] < NucAvg["T"]/2.0:
        failed=True
    
    if failed:
        return "Nuc swap or missing detected"
    else:
        return ""
    
         
    
        
    
def NucStepSizeImage_test(path_to_image):
    #load image and remove everything but signal lines, then split into A,C,G,T arrays when color matches
    image = cv2.imread(path_to_image)
    A = []
    C = []
    G = []
    T = []
    #delete the background and edges of the whole image
    i=0
    j=0
    rows, columns, channels = image.shape
    for i in range(0,rows):
        for j in range(0,columns):
            if i<=60 or i>=325 or j<=60 or j>=368 : #delete the axis
                image[i,j]= [255,255,255]
                continue
            if i>=241 and i<=300 and j>=242 and j<=290: #delete the legend
                image[i,j] = [255,255,255]
                continue
            if i>=241 and i<=323 and j>=294 and j<=368: #delete the other legend
                image[i,j] = [255,255,255]
                continue
            if image[i,j,0]==0 and image[i,j,1]==255 and image[i,j,2]==0:
                A.append(i)
            if  image[i,j,0]==0 and image[i,j,1]==0 and image[i,j,2]==255:
                C.append(i)
            if  image[i,j,0]==0 and image[i,j,1]==0 and image[i,j,2]==0:
                G.append(i)
            if  image[i,j,0]==255 and image[i,j,1]==0 and image[i,j,2]==0:
                T.append(i)
    #convert to Averages of each lane and scale to the scale in the picture
    A=400#int((400-(sum(A)/len(A))-84)*1.25)
    C=int((400-(sum(C)/len(C))-84)*1.25)
    G=int((400-(sum(G)/len(G))-84)*1.25)
    T=int((400-(sum(T)/len(T))-84)*1.25)
    #Run through decision tree
    AVG = (A+C+G+T)/4
    cols = ["A", "C", "G", "T"]
    problem_array = []
    matrix = abs(np.multiply(((np.array([[A,C,G,T],[A,C,G,T],[A,C,G,T],[A,C,G,T]]) + np.array([[A,A,A,A],[C,C,C,C],[G,G,G,G],[T,T,T,T]]))/2) - np.array([[A,C,G,T],[A,C,G,T],[A,C,G,T],[A,C,G,T]]),np.array([[1,1/AVG,1/AVG,1/AVG],[1/AVG,1,1/AVG,1/AVG],[1/AVG,1/AVG,1,1/AVG],[1/AVG,1/AVG,1/AVG,1]]))) #matrix of averages of all pair combinations
    
    for i in range(0,4):
        for j in range(0,4):
            if matrix[i][j] >= 0.10:
                problem_array.append(cols[i]+cols[j])
    print(problem_array)
    print(matrix)
    report = [0,0,0,0] # ACGT counts of occurence in matrix
    if len(problem_array) == 0:
        print("All good")
    for i in problem_array:
        if "A" in i:
            report[0]+=1
        if "C" in i:
            report[1]+=1
        if "G" in i:
            report[2]+=1
        if "T" in i:
            report[3]+=1
    print(report)
    return ""

def sample_plate_position(deck_image_path):###for some god dam reason the Diff variable is getting populated wrong
    image = cv2.imread(deck_image_path)
    image = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    top_sum=0
    bot_sum=0
    height, width = image.shape
    #populates top sum
    for i in range(150,351):
        for j in range(150,551):
            top_sum += image[j][i]
    #populates bot sum
    for i in range(150,351):
        for j in range(950,1351):
            bot_sum += image[j][i]      
    Diff = (top_sum-bot_sum)/top_sum
    report =""
    if (bot_sum >= 8000000) and (Diff<=0.50):
        report = "Position of Sample and MagSep plates were swapped"
    return report 
