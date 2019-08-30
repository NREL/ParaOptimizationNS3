#!/usr/bin/env python3
# Test automation script
# Runs the testbed specified in the cript and parses the output into a csv file which may be imported into the results analysis tool of the user's choice
#
# Copyright (c) 2017 Regents of the University of Colorado

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), 
# to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS 
# IN THE SOFTWARE.

# Author:  Adarsh Hasandka (adarsh.hasandka@colorado.edu)

#import
import argparse
import concurrent.futures
import csv
import heapq
import multiprocessing as mp
import os
import platform
import random
import re
import string
import subprocess
import sys
import time

#----------------------------------------------------------------------------------------------------------------------------------------------------------
#			Metric Cost Function 
#----------------------------------------------------------------------------------------------------------------------------------------------------------
def cost_func(avAvThroughput, minAvThroughput, avAvLatency, maxAvLatency, avPackLossRate):
	"This function accepts the output metrics of the simulation and returns a cost metric for performance comparison"
	cost=1
	if avAvLatency>300:
		cost+=(avAvLatency-300)
	if avAvLatency==0:						# Give large cost to error cases
		cost+=(10000)
	if maxAvLatency>300:
		cost+=(maxAvLatency-300)/100
	if avAvThroughput<9.6:
		cost+=(9.6-avAvThroughput)*10
	if minAvThroughput<9.6:
		cost+=9.6-minAvThroughput
	if avPackLossRate>1:
		cost+=(avPackLossRate-1)*10
	cost=round(cost,4)
	#print("avAvThroughput={} , maxAvLatency={} , avAvThroughput={} , minAvThroughput={} , avPackLossRate={}".format(avAvLatency,maxAvLatency,avAvThroughput,minAvThroughput,avPackLossRate))
	return cost;
	
#----------------------------------------------------------------------------------------------------------------------------------------------------------
#			Parameter and Values Generator 
#----------------------------------------------------------------------------------------------------------------------------------------------------------
def Get_Params_Vals(script):
	"This function accepts the script to be simulated and returns all the tunable parameter options for the script"
	#DataRates=[24000]
	#DataRates=[16*1024,24*1024,32*1024,40*1024,48*1024,56*1024]
	DataRates=[24000]
	PacketSizes=[256]
	#PacketSizes=[2048]
	SimTimes=[120]
	#SimTimes=[1]
	TransferProtocols=["UDP"]
	Topologies=['Topology_PV_penetration_40.csv']
	
	# CSMA Protocol-specific parameters
	ChannelDataRates=["100Mbps","1000Mbps"]
	ChannelMTUs=[1492,1500]
	EncapModes=["Dix","Llc"]
	#EncapModes=["Dix"]
	
	# Wimax Protocol-specific parameters
	ModulationTypes=["BPSK_12","QPSK_12","QPSK_34","QAM16_12","QAM16_34","QAM64_23","QAM64_34"]
	#ModulationTypes=["QAM16_34","QAM64_23","QAM64_34"]
	Schedulers=["Simple","RTPS","MBQOS"]
	#Schedulers=["Simple"]
	ServiceFlowTypes=["BE","NRTPS","RTPS","UGS"]
	#ServiceFlowTypes=["UGS"]
	
	# PLC Protocol-specific parameters
	PlcLowFreqs=[0,10,100]
	PlcHiFreqs=[10e6,50e6,10e7]
	PlcSubBands=[100,200,300]
	PlcHeaderMods=["BPSK_1_4","BPSK_1_2","QPSK_1_2","QAM16_1_2","QAM64_16_21","QAM16_RATELESS","QAM32_RATELESS","QAM64_RATELESS"]
	PlcPayloadMods=["BPSK_1_4","BPSK_1_2","QPSK_1_2","QAM16_1_2","QAM64_16_21","QAM16_RATELESS","QAM32_RATELESS","QAM64_RATELESS"]
	
	# if script=="testbed-Lowpan-CSMA-v1":
		# Params=["DataRate","PacketSize","SimTime","TransferProtocol","ChannelDataRate","EncapMode","ChannelMTU"]
		# vals=[[],[],[],[],[],[],[]]
		# for DR in DataRates:
			# for PS in PacketSizes:
				# for ST in SimTimes:
					# for TP in TransferProtocols:
						# for CDR in ChannelDataRates:
							# for EM in EncapModes:
								# if EM=="Dix":
									# CMTU=1500
								# else:
									# CMTU=1492
								# vals[0].append(DR)
								# vals[1].append(PS)
								# vals[2].append(ST)
								# vals[3].append(TP)
								# vals[4].append(CDR)
								# vals[5].append(EM)
								# vals[6].append(CMTU)
								
	# if script=="testbed-Lowpan-Wimax-v1":
		# Params=["DataRate","PacketSize","SimTime","TransferProtocol","ModulationType","Scheduler","ServiceFlowType"]
		# vals=[[],[],[],[],[],[],[]]
		# for DR in DataRates:
			# for PS in PacketSizes:
				# for ST in SimTimes:
					# for TP in TransferProtocols:
						# for MT in ModulationTypes:
							# for Sch in Schedulers:
								# for SFT in ServiceFlowTypes:
									# vals[0].append(DR)
									# vals[1].append(PS)
									# vals[2].append(ST)
									# vals[3].append(TP)
									# vals[4].append(MT)
									# vals[5].append(Sch)
									# vals[6].append(SFT)
	# if script=="testbed-Lowpan-WiFi-v1":
		# Params=["DataRate","PacketSize","SimTime","TransferProtocol"]
		# vals=[[],[],[],[]]
		# for DR in DataRates:
			# for PS in PacketSizes:
				# for ST in SimTimes:
					# for TP in TransferProtocols:
						# vals[0].append(DR)
						# vals[1].append(PS)
						# vals[2].append(ST)
						# vals[3].append(TP)
	# if script=="testbed-PLC-CSMA-v1":
		# Params=["DataRate","PacketSize","SimTime","TransferProtocol","ChannelDataRate","EncapMode","ChannelMTU","PlcLowFreq","PlcHiFreq","PlcSubBands","PlcHeaderMod","PlcPayloadMod"]
		# vals=[[],[],[],[],[],[],[],[],[],[],[],[]]
		# for DR in DataRates:
			# for PS in PacketSizes:
				# for ST in SimTimes:
					# for TP in TransferProtocols:
						# for CDR in ChannelDataRates:
							# for EM in EncapModes:
								# if EM=="Dix":
									# CMTU=1500
								# else:
									# CMTU=1492
								# for PLF in PlcLowFreqs:
									# for PHF in PlcHiFreqs:
										# for PSB in PlcSubBands:
											# for PHM in PlcHeaderMods:
												# for PPM in PlcPayloadMods:
													# vals[0].append(DR)
													# vals[1].append(PS)
													# vals[2].append(ST)
													# vals[3].append(TP)
													# vals[4].append(CDR)
													# vals[5].append(EM)
													# vals[6].append(CMTU)
													# vals[7].append(PLF)
													# vals[8].append(PHF)
													# vals[9].append(PSB)
													# vals[10].append(PHM)
													# vals[11].append(PPM)
	# if script=="testbed-PLC-Wimax-v1":
		# Params=["DataRate","PacketSize","SimTime","TransferProtocol","ModulationType","Scheduler","ServiceFlowType","PlcLowFreq","PlcHiFreq","PlcSubBands","PlcHeaderMod","PlcPayloadMod"]
		# vals=[[],[],[],[],[],[],[],[],[],[],[],[]]
		# for DR in DataRates:
			# for PS in PacketSizes:
				# for ST in SimTimes:
					# for TP in TransferProtocols:
						# for MT in ModulationTypes:
							# for Sch in Schedulers:
								# for SFT in ServiceFlowTypes:
									# for PLF in PlcLowFreqs:
										# for PHF in PlcHiFreqs:
											# for PSB in PlcSubBands:
												# for PHM in PlcHeaderMods:
													# for PPM in PlcPayloadMods:
														# vals[0].append(DR)
														# vals[1].append(PS)
														# vals[2].append(ST)
														# vals[3].append(TP)
														# vals[4].append(MT)
														# vals[5].append(Sch)
														# vals[6].append(SFT)
														# vals[7].append(PLF)
														# vals[8].append(PHF)
														# vals[9].append(PSB)
														# vals[10].append(PHM)
														# vals[11].append(PPM)
	# if script=="testbed-PLC-WiFi-v1":
		# Params=["DataRate","PacketSize","SimTime","TransferProtocol","ChannelDataRate","ChannelMTU","EncapMode","PlcLowFreq","PlcHiFreq","PlcSubBands","PlcHeaderMod","PlcPayloadMod"]
		# vals=[[],[],[],[],[],[],[],[],[]]
		# for DR in DataRates:
			# for PS in PacketSizes:
				# for ST in SimTimes:
					# for TP in TransferProtocols:	
						# for PLF in PlcLowFreqs:
							# for PHF in PlcHiFreqs:
								# for PSB in PlcSubBands:
									# for PHM in PlcHeaderMods:
										# for PPM in PlcPayloadMods:
											# vals[0].append(DR)
											# vals[1].append(PS)
											# vals[2].append(ST)
											# vals[3].append(TP)
											# vals[4].append(PLF)
											# vals[5].append(PHF)
											# vals[6].append(PSB)
											# vals[7].append(PHM)
											# vals[8].append(PPM)
	Params=["DataRate","PacketSize","Topology"]
	vals=[[],[],[]]
	for DR in DataRates:
		for PS in PacketSizes:
			for TOP in Topologies:
				vals[0].append(DR)
				vals[1].append(PS)
				vals[2].append(TOP)
						
	return (Params, vals)
#----------------------------------------------------------------------------------------------------------------------------------------------------------
#			BRUTE FORCE OPTIMIZER
#----------------------------------------------------------------------------------------------------------------------------------------------------------
def brute_optimizer(scriptName,Parameters,values,outParam,maxOrMin,Runs):
	"This function accepts a list of parameters, a 2D list of values, and a solution criteria to iterate through and find the optimal solution"
	q=[None]*(len(values[0])*Runs)
	p=[]
	i=0
	xmin=100000
	xmax=0	
	script=scriptName
	scriptName=scriptName
	runNo=0
	
	optimalResult=[0, "ERROR", 0, 60000, 0, 60000, 0, 0, 0, 0, 0, 0, "ERROR"]
	with open("Raw_Results/Raw_Results_"+scriptName+".csv", 'w', newline='') as outputFile:		# Create Output CSV file in which to store raw results of all simulations for this script
		outputWriter = csv.writer(outputFile)
		outputWriter.writerow(['Test No.', 'Script Name', 'Client Id','Average Throughput (kbps)', 'Min Device Throughput (kbps)', 'Average Latency (ms)', 'Max Device Latency (ms)', 'Packet Loss Rate (%)', 'Description'])
	
	print("Running {} Parallely using {} threads".format(scriptName,mp.cpu_count()))	# Terminal Message for visibility of execution	
	with concurrent.futures.ThreadPoolExecutor(mp.cpu_count()) as executor:			# Paralell execution using as many threads as available cpu cores
		for i in range(len(values[0])):
			options=""
			comment=""
			for j in range(len(Parameters)):							# Build options string from parameters
				options+="--{}={} ".format(Parameters[j],values[j][i])
				if j==0:									# Build comments string from parameters
					comment+="Simulated with {} = {}".format(Parameters[j],values[j][i])
				else:
					comment+=", {} = {}".format(Parameters[j],values[j][i])
			for j in range(Runs):
				q[runNo]=executor.submit(runScript,i+1,scriptName,options+"--RunNo={} ".format(runNo+1),comment+", and RunNo = {}".format(runNo+1))
				runNo+=1
		
		for future in concurrent.futures.as_completed(q):		
			output=future.result()
			avCount=0
			avAvThroughput=0
			minAvThroughput=60000
			avMinThroughput=0
			minMinThroughput=60000
			avAvLatency=0
			maxAvLatency=0
			avMaxLatency=0
			maxMaxLatency=0
			avPackLossRate=0
			maxPackLossRate=0
			if(len(output)==0):
				print("Bad Output!!!!!!! Due to either malformed/unexpected output or error in parsing. Output is:"+str(output))
			for result in output:		# Read and process Results from output queue as long as results are available
				avCount+=1;
				if(avCount==1):
					testNo=result[0]
					scriptName=result[1]
					with open("Raw_Results/Raw_Results_"+scriptName+"_Test_"+str(testNo)+".csv", 'w', newline='') as outputFile:		# Create Output CSV file in which to store raw results of this simulation
						outputWriter = csv.writer(outputFile)
						outputWriter.writerow(['Test No.', 'Script Name', 'Client Id','Average Throughput (kbps)', 'Min Device Throughput (kbps)', 'Average Latency (ms)', 'Max Device Latency (ms)', 'Packet Loss Rate (%)', 'Description'])
						outputWriter.writerow(result)	
					with open("Raw_Results/Raw_Results_"+scriptName+".csv", 'a', newline='') as outputFile:		# Write results to csv file
						outputWriter = csv.writer(outputFile)
						outputWriter.writerow(result)
				else:
					with open("Raw_Results/Raw_Results_"+scriptName+"_Test_"+str(testNo)+".csv", 'a', newline='') as outputFile:
						outputWriter = csv.writer(outputFile)
						outputWriter.writerow(result)	
					with open("Raw_Results/Raw_Results_"+scriptName+".csv", 'a', newline='') as outputFile:
						outputWriter = csv.writer(outputFile)
						outputWriter.writerow(result)
				if(result[3]>0):
					avAvThroughput=round((avAvThroughput*(avCount-1)+result[3])/avCount,3);
					if(result[3]<minAvThroughput):
						minAvThroughput=result[3]
					avMinThroughput=round((avMinThroughput*(avCount-1)+result[4])/avCount,3);
					if(result[4]<minMinThroughput):
						minMinThroughput=result[4]
					avAvLatency=round((avAvLatency*(avCount-1)+result[5])/avCount,3);
					if(result[5]>maxAvLatency):
						maxAvLatency=result[5]
					avMaxLatency=round((avMaxLatency*(avCount-1)+result[6])/avCount,3);
					if(result[6]>maxMaxLatency):
						maxMaxLatency=result[6]
					avPackLossRate=round((avPackLossRate*(avCount-1)+result[7])/avCount,3);
					if(result[7]>maxPackLossRate):
						maxPackLossRate=result[7]
					
				if ", and RunNo" in result[8]:
					desc=result[8].split(', and RunNo')[0]			# Delete RunNo trailer from successful result description string
					desc_unedited=result[8]
			
			with open("Av_Results/Averaged_Results_"+scriptName+".csv", 'a', newline='') as outputFile:		# Create Output CSV file in which to store averaged results of the simulation for this script
				outputWriter = csv.writer(outputFile)
				outputWriter.writerow([testNo, scriptName, avAvThroughput, minAvThroughput, avMinThroughput, minMinThroughput, avAvLatency, maxAvLatency, avMaxLatency, maxMaxLatency, avPackLossRate, maxPackLossRate, desc_unedited])		
			
			if outParam=="Average Throughput":
				x=avAvThroughput
			if outParam=="Min Throughput":
				x=avMinThroughput
			
			if outParam=="Average Latency":
				x=avAvLatency
			if outParam=="Max Latency":
				x=avMaxLatency
				
			if outParam=="Average Packet Loss Rate":
				x=avPackLossRate
			if outParam=="Max Packet Loss Rate":
				x=maxPackLossRate
			if outParam=="Cost":
				x=cost_func(avAvThroughput, minAvThroughput, avAvLatency, maxAvLatency, avPackLossRate)
				
			if maxOrMin=="Maximize":						# Determine optimal result
				if x>xmax:
					optimalResult=[testNo, scriptName, avAvThroughput, minAvThroughput, avMinThroughput, minMinThroughput, avAvLatency, maxAvLatency, avMaxLatency, maxMaxLatency, avPackLossRate, maxPackLossRate, desc]
					xmax=x				
			if maxOrMin=="Minimize":
				if x<xmin and x>0:
					optimalResult=[testNo, scriptName, avAvThroughput, minAvThroughput, avMinThroughput, minMinThroughput, avAvLatency, maxAvLatency, avMaxLatency, maxMaxLatency, avPackLossRate, maxPackLossRate, desc]
					xmin=x
		
	return (optimalResult, x);								# Return optimal result
#----------------------------------------------------------------------------------------------------------------------------------------------------------
#			SCRIPT EXECUTION FUNCTION
#----------------------------------------------------------------------------------------------------------------------------------------------------------	
def runScript(rowNo, scriptName, options, comment):
	"This function runs the input script file and stores it in the corresponding row of the csv"
	# initialize dictionaries
	totalBytes_Tx={}
	totalBytes_Rx={}
	avLatency={}
	maxLatency={}
	avThroughput={}
	minThroughput={}
	desc=""
	sys.stdout.write("\rRunning Case: row no {}\r".format(rowNo))
	sys.stdout.flush()	
	result=[]
	try:		#Run ./waf command to obtain output
		cmd=subprocess.check_output(['./waf --run \"{} {}\"'.format("scratch/"+scriptName,options)], shell=True, stderr=subprocess.STDOUT)
	except Exception as error:
		desc+="[ERROR] - "+str(error)+"\n[COMMENT] - "+comment 			# Concatenate Error message to comment
		result.append([rowNo, scriptName, 60000, 0, 60000, 0, 0, 0, desc]) # To observe error message in output, a dummy client 60000 is used
	else:
		output=cmd.decode("UTF-8").splitlines()						#parse output
		for line in output:
			match = re.search(r'\[DESC\] - (.*)', line)				# Capture script description string
			if match:
				desc=match.group(1)
			
			match = re.search(r'Client (\d*) Sent (\d*) Packets of total size (\d*) bytes', line)	# Capture reported Client Tx Information
			if match:
				if(float(match.group(1))>0):								# Ignore errored values
					totalBytes_Tx['{}'.format(match.group(1))]=match.group(3)
			
			match = re.search(r'Server received (\d*) bytes across \d* packets, from Client (\d*), Average Latency: (\d+\.?\d*)+ms, Average Throughput: (\d+\.?\d*)+kbps, Max Latency: (\d+\.?\d*)+ms, Min Throughput: (\d+\.?\d*)+kbps', line)		# Capture reported Server Rx information
			if match:
				if(float(match.group(2))>0):				
					totalBytes_Rx['{}'.format(match.group(2))]=match.group(1)
					avLatency['{}'.format(match.group(2))]=match.group(3)
					avThroughput['{}'.format(match.group(2))]=match.group(4)
					maxLatency['{}'.format(match.group(2))]=match.group(5)
					minThroughput['{}'.format(match.group(2))]=match.group(6)	

		# concatenate comment to description if present
		desc+=" - "+comment

		# calculate max packet loss
		for dict_key in totalBytes_Rx.keys():
			Tx_Bytes=int(totalBytes_Tx[dict_key])	
			Rx_Bytes=int(totalBytes_Rx[dict_key])
			packLossRate=round((1.0-(Rx_Bytes/Tx_Bytes))*100,3)
			if packLossRate<0:
				packLossRate=-1*packLossRate
			result.append([rowNo, scriptName, int(dict_key), float(avThroughput[dict_key]), float(minThroughput[dict_key]), float(avLatency[dict_key]), float(maxLatency[dict_key]), packLossRate, desc])			#write output to queue
	if(len(result)==0):
		result.append([rowNo, scriptName, 60000, 0, 60000, 0, 0, 0, "FAILED COMMAND: ./waf --run \"{} {}\"".format("scratch/"+scriptName,options)])
	return result
#----------------------------------------------------------------------------------------------------------------------------------------------------------
#			MAIN CODE EXECUTION (with performance measurement)
#----------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':

	if platform.system() == "Linux":
		os.system("taskset -c -p 0-{} {}".format(mp.cpu_count(),os.getpid()))			# Change task affinity so all cores are used [LINUX specific]

	print("Test automation script by Adarsh Hasandka (NREL)\n")
	starttime=time.time()
	mode="Brute_Force"
	variable="Cost"
	optimum_results=[]

	if not os.path.exists('Av_Results'):
		os.makedirs('Av_Results')
	if not os.path.exists('Raw_Results'):
		os.makedirs('Raw_Results')

	# If script needs to iterate through many parameter values for a specific script the brute force optimizer may be used
	print("Using a Brute Force approach to optimize the simulation result")
	cmd=subprocess.check_output(['./waf build'], shell=True, stderr=subprocess.STDOUT)	# Build waf first

	#scripts=["testbed-Lowpan-Wimax-v1","testbed-BPLC-Wimax-v1"]
	scripts=["testbed-Lowpan-CSMA-v1","testbed-BPLC-CSMA-v1","testbed-Lowpan-Wimax-v1","testbed-BPLC-Wimax-v1","testbed-NPLC-Wimax-v1","testbed-NPLC-CSMA-v1","testbed-BPLC-WiFi-v1","testbed-NPLC-WiFi-v1","testbed-Lowpan-WiFi-v1"]
	for script in scripts:
		with open("Av_Results/Averaged_Results_"+script+".csv", 'w', newline='') as outputFile:		# Create Output CSV file in which to store raw results of all simulations for this script
			outputWriter = csv.writer(outputFile)
			outputWriter.writerow(['Test No', 'Script Name', 'Average Average Throughput (kbps)', 'Minimum Average Throughput (kbps)', 'Average Minimum Device Throughput (kbps)', 'Minimum Minimum Device Throughput (kbps)', 'Average Average Latency (ms)', 'Maximum Average Latency (ms)', 'Average Maximum Device Latency (ms)', 'Maximum Maximum Device Latency (ms)', 'Average Packet Loss Rate (%)', 'Maximum Device Packet Loss Rate (%)', 'Description'])
		(Parameters, values)=Get_Params_Vals(script)		
		(optimalResult, cost)=brute_optimizer(script,Parameters,values,variable,"Minimize",1000)
		optimum_results.append(optimalResult) 
		print("\nOptimal Result occurs at: \nTest No.\t\t\t\t:\t{}\nScript Name\t\t\t\t:\t{}\nAverage Average Throughput (kbps)\t:\t{}\nMinimum Average Throughput (kbps)\t:\t{}\nAverage Minimum Device Throughput (kbps):\t{}\nMinimum Minimum Device Throughput (kbps):\t{}\nAverage Average Latency (ms)\t\t:\t{}\nMaximum Average Latency (ms)\t\t:\t{}\nAverage Maximum Device Latency (ms)\t:\t{}\nMaximum Maximum Device Latency (ms)\t:\t{}\nAverage Packet Loss Rate\t\t:\t{}\nMaximum Device Packet Loss Rate\t\t:\t{}\nDescription\t\t\t\t:\t{}\nPerformance Metric Cost\t\t\t:\t{}\n".format(optimalResult[0],optimalResult[1],optimalResult[2],optimalResult[3],optimalResult[4],optimalResult[5],optimalResult[6],optimalResult[7],optimalResult[8],optimalResult[9],optimalResult[10],optimalResult[11],optimalResult[12],cost))
	
	with open('Optimal_Simulation_Results.csv', 'w', newline='') as outputFile:		# Create Output CSV file in which to store overall results of simulation
		outputWriter = csv.writer(outputFile)
		outputWriter.writerow(['Test No', 'Script Name', 'Average Average Throughput (kbps)', 'Minimum Average Throughput (kbps)', 'Average Minimum Device Throughput (kbps)', 'Minimum Minimum Device Throughput (kbps)', 'Average Average Latency (ms)', 'Maximum Average Latency (ms)', 'Average Maximum Device Latency (ms)', 'Maximum Maximum Device Latency (ms)', 'Average Packet Loss Rate (%)', 'Maximum Device Packet Loss Rate (%)', 'Description'])

	for optResult in optimum_results:
		with open('Optimal_Simulation_Results.csv', 'a', newline='') as outputFile:		# Create Output CSV file in which to store overall results of simulations
			outputWriter = csv.writer(outputFile)
			outputWriter.writerow(optResult)
	endtime=time.time()
	print("\ntotal execution time: {} seconds\n".format(float(endtime)-float(starttime)))
