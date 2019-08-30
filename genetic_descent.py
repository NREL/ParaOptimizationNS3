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
import getopt
import multiprocessing as mp
import numbers
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
	cost=avAvLatency+avPackLossRate+(60-avAvThroughput)
	if avAvLatency>300:
		cost+=(avAvLatency-300)
	if avAvLatency==0:						# Give large cost to error cases
		cost+=20000
	if maxAvLatency>300:					# Give large cost to cases that peform below minimum requirements
		cost+=(maxAvLatency-300)/100
	if avAvThroughput<9.6:					# Give large cost to cases that peform below minimum requirements
		cost+=(9.6-avAvThroughput)*100
	if avAvThroughput==0:					# Give large cost to error cases
		cost+=10000
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
	DataRates=[16000,24000,48000,56000]
	#PacketSizes=[64,128,256,512,1024,2048]
	#PacketSizes=[512]
	PacketSizes=[64,256,1024,2048]
	SimTimes=[120]
	#SimTimes=[1]
	TransferProtocols=["UDP","TCP"]
	
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
	Params=["DataRate","PacketSize"]
	vals=[[],[]]
	for DR in DataRates:
		for PS in PacketSizes:
			vals[0].append(DR)
			vals[1].append(PS)
						
	return (Params, vals)


#----------------------------------------------------------------------------------------------------------------------------------------------------------
#			GENETIC OPTIMIZER (Uses Weighted Global Criterion for evaluation)
#----------------------------------------------------------------------------------------------------------------------------------------------------------	
def genetic_optimizer(scriptName,Parameters,values,Runs,maxGen,maxElites,maxGenPop,mutationChance,mutationRate,stepSize):
	"This function accepts a list of parameters, a 2D list of initial values, and the maximum number of iterations to run to find the optimal solution using an evolutionary algorithm"
	values_nextGen=values
	values_GenPop={}
	cost_GenPop={}
	result_GenPop={}
	Lowest_cost=10000
	values_elites={}
	cost_elites={}
	result_elites={}
	i=0
	xmin=100000
	xmax=0
	minVals=[0]*len(Parameters)
	maxVals=[4000]*len(Parameters)
	for j in range(len(Parameters)):															# Identify minimum and maximum limits
		trait=values[j][0]
		if isinstance(trait, numbers.Number):
			minVals[j]=min(values[j])
			maxVals[j]=max(values[j])
	Optimum_Found=False
	bestHash="N/A"
	for gen in range(maxGen):
		if Lowest_cost > 0:
			q=[]
			runNo=0
			runRandomizer=random.randrange(1,1000)
			# Run generation and obtain results
			
			with open("Av_Results/Gen"+str(gen)+"_Averaged_Results_"+scriptName+".csv", 'w', newline='') as outputFile:		# Create Output CSV file in which to store raw results of all simulations for this script
				outputWriter = csv.writer(outputFile)
				outputWriter.writerow(['Test No', 'Script Name', 'Average Average Throughput (kbps)', 'Minimum Average Throughput (kbps)', 'Average Minimum Device Throughput (kbps)', 'Minimum Minimum Device Throughput (kbps)', 'Average Average Latency (ms)', 'Maximum Average Latency (ms)', 'Average Maximum Device Latency (ms)', 'Maximum Maximum Device Latency (ms)', 'Average Packet Loss Rate (%)', 'Maximum Device Packet Loss Rate (%)', 'Description'])
		
			with open("Raw_Results/Gen"+str(gen)+"_Raw_Results_"+scriptName+".csv", 'w', newline='') as outputFile:		# Create Output CSV file in which to store raw results of all simulations for this script
				outputWriter = csv.writer(outputFile)
				outputWriter.writerow(['Test No.', 'Script Name', 'Client Id','Average Throughput (kbps)', 'Min Device Throughput (kbps)', 'Average Latency (ms)', 'Max Device Latency (ms)', 'Packet Loss Rate (%)', 'Description', 'Generation Index'])
		
			print("Running Gen {} Parallely using {} threads".format(gen,mp.cpu_count()))	# Terminal Message for visibility of execution	
			with concurrent.futures.ThreadPoolExecutor(mp.cpu_count()) as executor:			# Parallel execution using as many threads as available cpu cores
				for i in range(len(values_nextGen[0])):
					options=""
					comment=""
					for j in range(len(Parameters)):							# Build options string from parameters
						options+="--{}={} ".format(Parameters[j],values_nextGen[j][i])
						if j==0:									# Build comments string from parameters
							comment+="Simulated with {} = {}".format(Parameters[j],values_nextGen[j][i])
						else:
							comment+=", {} = {}".format(Parameters[j],values_nextGen[j][i])
					for j in range(Runs):
						q.append(executor.submit(runScript,i+1,scriptName,options+"--RunNo={} ".format(runNo+runRandomizer+1),comment+", and RunNo = {}".format(runNo+runRandomizer+1),i))
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
					for result in output:		# Read and process Results from output queue as long as results are available
						avCount+=1;
						if(avCount==1):
							testNo=result[0]
							#scriptName=str(result[1])
							with open("Raw_Results/Gen"+str(gen)+"_Raw_Results_"+scriptName+"_Test_"+str(testNo)+".csv", 'w', newline='') as outputFile:		# Create Output CSV file in which to store raw results of this simulation
								outputWriter = csv.writer(outputFile)
								outputWriter.writerow(['Test No.', 'Script Name', 'Client Id','Average Throughput (kbps)', 'Min Device Throughput (kbps)', 'Average Latency (ms)', 'Max Device Latency (ms)', 'Packet Loss Rate (%)', 'Description', 'Generation Index'])
								outputWriter.writerow(result)	
							with open("Raw_Results/Gen"+str(gen)+"_Raw_Results_"+scriptName+".csv", 'a', newline='') as outputFile:		# Write results to csv file
								outputWriter = csv.writer(outputFile)
								outputWriter.writerow(result)
						else:
							with open("Raw_Results/Gen"+str(gen)+"_Raw_Results_"+scriptName+"_Test_"+str(testNo)+".csv", 'a', newline='') as outputFile:
								outputWriter = csv.writer(outputFile)
								outputWriter.writerow(result)	
							with open("Raw_Results/Gen"+str(gen)+"_Raw_Results_"+scriptName+".csv", 'a', newline='') as outputFile:
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
						
						genIndex=result[9]
					with open("Av_Results/Gen"+str(gen)+"_Averaged_Results_"+scriptName+".csv", 'a', newline='') as outputFile:		# Create Output CSV file in which to store averaged results of the simulation for this script
						outputWriter = csv.writer(outputFile)
						outputWriter.writerow([testNo, scriptName, avAvThroughput, minAvThroughput, avMinThroughput, minMinThroughput, avAvLatency, maxAvLatency, avMaxLatency, maxMaxLatency, avPackLossRate, maxPackLossRate, desc_unedited])		
					#print("Result of testNo {} on script {} is {} {} {} {} {} {} {} {} {} {} {}".format(testNo, scriptName, avAvThroughput, minAvThroughput, avMinThroughput, minMinThroughput, avAvLatency, maxAvLatency, avMaxLatency, maxMaxLatency, avPackLossRate, maxPackLossRate, desc_unedited))
					cost=cost_func(avAvThroughput, minAvThroughput, avAvLatency, maxAvLatency, avPackLossRate)			# Obtain weighted cost from cost function
					hash=""																								# Add result to general population
					for j in range(len(Parameters)):																		# Get unique hash of this simulation
						hash+=str(values_nextGen[j][genIndex])
					if hash in values_GenPop.keys():																	# Check if a result already exists
						if cost < cost_GenPop[hash]:																	# If new result is better, replace old result
							cost_GenPop[hash]=cost
							result_GenPop[hash]=[testNo, scriptName, avAvThroughput, minAvThroughput, avMinThroughput, minMinThroughput, avAvLatency, maxAvLatency, avMaxLatency, maxMaxLatency, avPackLossRate, maxPackLossRate, desc_unedited]
					else:																								# Add result to list if it already exists
						result_GenPop[hash]=[testNo, scriptName, avAvThroughput, minAvThroughput, avMinThroughput, minMinThroughput, avAvLatency, maxAvLatency, avMaxLatency, maxMaxLatency, avPackLossRate, maxPackLossRate, desc_unedited]
						if maxGenPop > 0:																				# Check if General Population is limited
							if len(cost_GenPop) >= maxGenPop:
								maxHash=max(cost_GenPop, key=cost_GenPop.get)
								if cost < cost_GenPop[maxHash]:
									del cost_GenPop[maxHash]															# Delete highest cost Parent in General Population
									del values_GenPop[maxHash]
									values_GenPop[hash]=[values_nextGen[j][genIndex] for j in range(len(Parameters))]	# add to General Population
									cost_GenPop[hash]=cost
							else:
								values_GenPop[hash]=[values_nextGen[j][genIndex] for j in range(len(Parameters))]			# Unconditionally add to General Population
								cost_GenPop[hash]=cost
						else:
							values_GenPop[hash]=[values_nextGen[j][genIndex] for j in range(len(Parameters))]			# Unconditionally add to General Population
							cost_GenPop[hash]=cost
					
					#print("Best Result with HASH={} is : {}".format(hash, result_GenPop[hash]))
					
					if len(cost_elites) == 0 or cost < max(list(cost_elites.values())):									# Check if new Elites List is needed
						elite_hashes=sorted(cost_GenPop, key=cost_GenPop.get)
						if len(elite_hashes)>maxElites:																	# Slice list if number of elements greater than maxElites
							elite_hashes=elite_hashes[:maxElites]
						cost_elites={}
						result_elites={}
						values_elites={}
						#print("Elite Hashes:{}".format(elite_hashes))
						for eliteHash in elite_hashes:																	# Build new Elites List											
							values_elites[eliteHash]=values_GenPop[eliteHash]
							result_elites[eliteHash]=result_GenPop[eliteHash]
							cost_elites[eliteHash]=cost_GenPop[eliteHash]		
			
			
			# Perform Gradient Descent to find best solution
			minHash=min(cost_elites, key=cost_elites.get)
			position=values_GenPop[minHash]
			#print("Gen {} Best Result before Gradient Descent: {}".format(gen, result_elites[minHash]))
			if minHash != bestHash:
				improved=True
				positionResult=result_GenPop[minHash]
				#print("Starting position: {}".format(position))
				while improved == True:
					for j in range(len(Parameters)):														# Clear List of next generation values
						values_nextGen[j].clear()
					val_next=position
					for j in range(len(Parameters)):
						trait=val_next[j]
						if isinstance(trait, numbers.Number):
						
							val_next[j]=trait+stepSize														# Create Child with trait one step in positive direction
							if val_next[j]>maxVals[j]:
								val_next[j]=maxVals[j]
							for k in range(len(Parameters)):
								values_nextGen[k].append(val_next[k])										
								
							val_next[j]=trait-stepSize														# Create Child with trait one step in negative direction
							if val_next[j]<minVals[j]:
								val_next[j]=minVals[j]
							for k in range(len(Parameters)):
								values_nextGen[k].append(val_next[k])	
						else:
							randVal=val_next[j]																# Create Child with different trait
							timeout=0
							while randVal==val_next[j] and timeout<3:
								randVal=random.choice(values[j])
								timeout=timeout+1
							val_next[j]=randVal
							for k in range(len(Parameters)):
								values_nextGen[k].append(val_next[k])
					q2=[]
					runRandomizer=random.randrange(1,1000)
					improved=False
					print("Running Gradient Descent for Gen {} Parallely using {} threads".format(gen,mp.cpu_count()))	# Terminal Message for visibility of execution	
					with concurrent.futures.ThreadPoolExecutor(mp.cpu_count()) as executor:			# Parallel execution using as many threads as available cpu cores
						for i in range(len(values_nextGen[0])):
							options=""
							comment=""
							for j in range(len(Parameters)):							# Build options string from parameters
								options+="--{}={} ".format(Parameters[j],values_nextGen[j][i])
								if j==0:									# Build comments string from parameters
									comment+="Simulated with {} = {}".format(Parameters[j],values_nextGen[j][i])
								else:
									comment+=", {} = {}".format(Parameters[j],values_nextGen[j][i])
							q2.append(executor.submit(runScript,scriptName,i+1,options,comment,i))


						for future in concurrent.futures.as_completed(q2):	
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
								if(avCount==0):
									testNo=result[0]
									#scriptName=str(result[1])
									with open("Raw_Results/Gen"+str(gen)+"_Raw_Results_"+scriptName+"_Test_"+str(testNo)+".csv", 'w', newline='') as outputFile:		# Create Output CSV file in which to store raw results of this simulation
										outputWriter = csv.writer(outputFile)
										outputWriter.writerow(['Test No.', 'Script Name', 'Client Id','Average Throughput (kbps)', 'Min Device Throughput (kbps)', 'Average Latency (ms)', 'Max Device Latency (ms)', 'Packet Loss Rate (%)', 'Description', 'Generation Index'])
										outputWriter.writerow(result)	
									with open("Raw_Results/Gen"+str(gen)+"_Raw_Results_"+scriptName+".csv", 'a', newline='') as outputFile:		# Write results to csv file
										outputWriter = csv.writer(outputFile)
										outputWriter.writerow(result)
								else:
									with open("Raw_Results/Gen"+str(gen)+"_Raw_Results_"+scriptName+"_Test_"+str(testNo)+".csv", 'a', newline='') as outputFile:
										outputWriter = csv.writer(outputFile)
										outputWriter.writerow(result)	
									with open("Raw_Results/Gen"+str(gen)+"_Raw_Results_"+scriptName+".csv", 'a', newline='') as outputFile:
										outputWriter = csv.writer(outputFile)
										outputWriter.writerow(result)
								if(result[3]>0):
									avCount+=1;
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
								
								genIndex=result[9]
							with open("Av_Results/Gen"+str(gen)+"_Averaged_Results_"+scriptName+".csv", 'a', newline='') as outputFile:		# Create Output CSV file in which to store averaged results of the simulation for this script
								outputWriter = csv.writer(outputFile)
								outputWriter.writerow([testNo, scriptName, avAvThroughput, minAvThroughput, avMinThroughput, minMinThroughput, avAvLatency, maxAvLatency, avMaxLatency, maxMaxLatency, avPackLossRate, maxPackLossRate, "GD-"+desc_unedited])		
							
							cost=cost_func(avAvThroughput, minAvThroughput, avAvLatency, maxAvLatency, avPackLossRate)			# Obtain weighted cost from cost function
							
							if cost<positionResult[2]:
								position=[values_nextGen[j][genIndex] for j in range(len(Parameters))]
								positionResult=[testNo, scriptName, cost, desc, genIndex]
								improved=True
								
					minHash=min(cost_elites, key=cost_elites.get)		
					#print("Gen {} Descent Best Result: {} \n Lowest Cost: {}".format(gen, position, positionResult[2]))
				hash=""																									# Add result to general population
				for j in range(len(Parameters)):																		# Get unique hash of this simulation
					hash+=str(position[j])
				if hash in list(values_GenPop.keys()):
					print("Result already exists, no descent necessary")
				if hash not in list(values_GenPop.keys()):	
					result_GenPop[hash]=positionResult
					values_GenPop[hash]=position																		# add to General Population
					cost_GenPop[hash]=positionResult[2]
					result_elites[hash]=positionResult
					values_elites[hash]=position																		# add to Elite Population
					cost_elites[hash]=positionResult[2]
					#print("Gradient Descent produced better result hash:{}, result:{}!!!".format(hash,result_GenPop[hash]))
					#print("Position: {}, Position Result: {}".format(position,positionResult))
					minHash=min(cost_elites, key=cost_elites.get)	
				bestHash=minHash
			
			for j in range(len(Parameters)):																			# Clear List of next generation values
				values_nextGen[j].clear()
			#print("\nGen {} Elites Values: {}\n".format(gen, list(values_elites.values())))
			#print("\nGen {} Elites Cost: {}\n".format(gen, list(cost_elites.values())))
			#print("\nGen {} Elites Results: {}\n".format(gen, list(result_elites.values())))
			
			if random.randint(0,100)<=(100*gen/(maxGen-5)):								# Simulated Annealing.
				PopList=values_elites
			else:
				PopList=values_GenPop
			if len(PopList)>4*maxElites:
				for element in range(4*maxElites):									# Limit size of next generation to 4*maxElites
					parentA=random.choice(list(PopList.keys()))
					parentB=random.choice(list(PopList.keys()))
					while parentA == parentB:										# Ensure parent B is different from A 
						parentB=random.choice(list(PopList.keys()))
					for j in range(len(Parameters)):
						parentTraitA=PopList[parentA][j]							
						parentTraitB=PopList[parentB][j]
						if isinstance(parentTraitA, numbers.Number):						# If numeric, obtain a mixed trait with other random parent
							childTrait=((parentTraitA+parentTraitB)/2)
							if random.choice(range(100)) <= mutationChance:					# mutation chance
								childTrait=childTrait+random.randint(int(-1*mutationRate*childTrait/100), int(mutationRate*childTrait/100))		# introduce mutation for numeric variables
								if childTrait>maxVals[j]:											# Enforce range limits
									childTrait=maxVals[j]
								if childTrait<minVals[j]:
									childTrait=minVals[j]
							if isinstance(parentTraitA, int):
								childTrait=int(childTrait)
							if isinstance(parentTraitA, float):
								childTrait=float(childTrait)
						else:																# If not numeric, randomly select one of the Parent traits for child
							childTrait=random.choice([parentTraitA, parentTraitB])	
						values_nextGen[j].append(childTrait)								# Add child trait to list of children to be simulated
			else:
				for parentA in list(PopList.keys()):												# Select as Parent A each element in Population list
					parentB=random.choice(list(PopList.keys()))
					while parentA == parentB:												# Ensure parent B is different from A
						parentB=random.choice(list(PopList.keys()))
					for j in range(len(Parameters)):
						parentTraitA=PopList[parentA][j]							
						parentTraitB=PopList[parentB][j]
						if isinstance(parentTraitA, numbers.Number):						# If numeric, obtain a mixed trait with other random parent
							childTrait=((parentTraitA+parentTraitB)/2)
							if random.choice(range(100)) <= mutationChance:					# mutation chance
								childTrait=childTrait+random.randint(int(-1*mutationRate*childTrait/100), int(mutationRate*childTrait/100))		# introduce mutation for numeric variables
								if childTrait>maxVals[j]:											# Enforce range limits
									childTrait=maxVals[j]
								if childTrait<minVals[j]:
									childTrait=minVals[j]
							if isinstance(parentTraitA, int):
								childTrait=int(childTrait)
							if isinstance(parentTraitA, float):
								childTrait=float(childTrait)
						else:														# If not numeric, randomly select one of the Parent traits for child
							childTrait=random.choice([parentTraitA, parentTraitB])	
						values_nextGen[j].append(childTrait)						# Add child trait to list of children to be simulated
			#print("Next Gen - Gen {} Values: {}".format(gen+1, values_nextGen))
		minHash=min(cost_elites, key=cost_elites.get)
		Lowest_cost=cost_elites[minHash]
		print("Gen {} Result: \n Best Result: {} \n Gen {} Lowest Cost: {}".format(gen, result_elites[minHash], gen, cost_elites[minHash]))
	with open("Optimal_Results/Optimal_Results_"+script+".csv", 'w', newline='') as outputFile:		# Create Output CSV file in which to store raw results of all simulations for this script
		outputWriter = csv.writer(outputFile)
		outputWriter.writerow(['Test No.', 'Script Name', 'Client Id','Average Throughput (kbps)', 'Min Device Throughput (kbps)', 'Average Latency (ms)', 'Max Device Latency (ms)', 'Packet Loss Rate (%)', 'Description', 'Generation Index'])
		for	hash in result_elites:
			outputWriter.writerow(result_elites[hash])
	minHash=min(cost_elites, key=cost_elites.get)
	#print("\nElite Results after output written: {} \n".format(result_elites))
	#print("\nElite Cost after output written: {} \n".format(cost_elites))
	#print("\nOptimal Result occurs at: {} \nWith cost:{}".format(result_elites[minHash], cost_elites[minHash]))
	return (result_elites[minHash], cost_elites[minHash])
		
#----------------------------------------------------------------------------------------------------------------------------------------------------------
#			SCRIPT EXECUTION FUNCTION
#----------------------------------------------------------------------------------------------------------------------------------------------------------	
def runScript(rowNo, scriptName, options, comment, genIndex):
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
		result.append([rowNo, scriptName, 60000, 0, 60000, 0, 0, 0, desc, genIndex]) # To observe error message in output, a dummy client 60000 is used
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
			result.append([rowNo, scriptName, int(dict_key), float(avThroughput[dict_key]), float(minThroughput[dict_key]), float(avLatency[dict_key]), float(maxLatency[dict_key]), packLossRate, desc, genIndex])			#write output to queue
	if(len(result)==0):
		result.append([rowNo, scriptName, 60000, 0, 60000, 0, 0, 0, "FAILED COMMAND: ./waf --run \"{} {}\"".format("scratch/"+scriptName,options), genIndex])
	return result
#----------------------------------------------------------------------------------------------------------------------------------------------------------
#			MAIN CODE EXECUTION (with performance measurement)
#----------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
	argv=sys.argv[1:]
	MC=20
	MR=20
	ME=30
	MG=25
	MP=60
	SS=3
	try:
		opts, args = getopt.getopt(argv,"hMC:MR:ME:MP:MG:SS:",["MutationChance=","MutationRate=","MaxElite=","MaxPopulation=","MaxGeneration=","StepSize="])
	except getopt.GetoptError:
		print ('genetic_optimizer_test.py -MC <MutationChance> -MR <MutationRate> -ME <MaxElite> -MP <MaxPopulation> -MG <MaxGeneration> -SS <StepSize>')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print ('genetic_optimizer_test.py -MC <MutationChance> -MR <MutationRate> -ME <MaxElite> -MP <MaxPopulation> -MG <MaxGeneration> -SS <StepSize>')
			sys.exit()
		elif opt in ("-MC", "--MutationChance"):
			MC = int(arg)
		elif opt in ("-MR", "--MutationRate"):
			MR = int(arg)
		elif opt in ("-ME", "--MaxElite"):
			ME = int(arg)
		elif opt in ("-MP", "--MaxPopulation"):
			MP = int(arg)
		elif opt in ("-MG", "--MaxGeneration"):
			MG = int(arg)
		elif opt in ("-SS", "--StepSize"):
			SS = int(arg)
	
	if not os.path.exists('Av_Results'):
		os.makedirs('Av_Results')
	if not os.path.exists('Raw_Results'):
		os.makedirs('Raw_Results')
	if not os.path.exists('Optimal_Results'):
		os.makedirs('Optimal_Results')

	if platform.system() == "Linux":
		os.system("taskset -c -p 0-{} {}".format(mp.cpu_count(),os.getpid()))			# Change task affinity so all cores are used [LINUX specific]
	print("Checking waf build.....")
	cmd=subprocess.check_output(['./waf build'], shell=True, stderr=subprocess.STDOUT)	# Build waf first
	print("waf built!")
	print("Test automation script by Adarsh Hasandka (NREL)\n")
	starttime=time.time()
	mode="Brute_Force"
	variable="Cost"
	optimum_results=[]
	# If script needs to iterate through many parameter values for a specific script the brute force optimizer may be used
	print("Using a hybrid evolutionary descent algorithm to optimize the simulation result")
	#cmd=subprocess.check_output(['./waf build'], shell=True, stderr=subprocess.STDOUT)	# Build waf first
	#scripts=["testbed-Lowpan-CSMA-v1","testbed-Lowpan-WiFi-v1","testbed-Lowpan-Wimax-v1","testbed-PLC-CSMA-v1","testbed-PLC-WiFi-v1","testbed-PLC-Wimax-v1"]
	scripts=["testbed-BPLC-CSMA-v1","testbed-BPLC-WiFi-v1","testbed-BPLC-Wimax-v1","testbed-NPLC-Wimax-v1"]
	for script in scripts:
		with open("Av_Results/Averaged_Results_"+script+".csv", 'w', newline='') as outputFile:		# Create Output CSV file in which to store raw results of all simulations for this script
			outputWriter = csv.writer(outputFile)
			outputWriter.writerow(['Test No', 'Script Name', 'Average Average Throughput (kbps)', 'Minimum Average Throughput (kbps)', 'Average Minimum Device Throughput (kbps)', 'Minimum Minimum Device Throughput (kbps)', 'Average Average Latency (ms)', 'Maximum Average Latency (ms)', 'Average Maximum Device Latency (ms)', 'Maximum Maximum Device Latency (ms)', 'Average Packet Loss Rate (%)', 'Maximum Device Packet Loss Rate (%)', 'Description'])
		(Parameters, values)=Get_Params_Vals(script)	
		(optimalResult, cost)=genetic_optimizer(script,Parameters,values,4,MG,ME,MP,MC,MR,SS)
		optimum_results.append(optimalResult) 
	with open('Optimal_Simulation_Results.csv', 'w', newline='') as outputFile:		# Create Output CSV file in which to store overall results of simulation
		outputWriter = csv.writer(outputFile)
		outputWriter.writerow(['Test No', 'Script Name', 'Average Average Throughput (kbps)', 'Minimum Average Throughput (kbps)', 'Average Minimum Device Throughput (kbps)', 'Minimum Minimum Device Throughput (kbps)', 'Average Average Latency (ms)', 'Maximum Average Latency (ms)', 'Average Maximum Device Latency (ms)', 'Maximum Maximum Device Latency (ms)', 'Average Packet Loss Rate (%)', 'Maximum Device Packet Loss Rate (%)', 'Description'])
	for optResult in optimum_results:
		with open('Optimal_Simulation_Results.csv', 'a', newline='') as outputFile:		# Create Output CSV file in which to store overall results of simulations
			outputWriter = csv.writer(outputFile)
			outputWriter.writerow(optResult)
	endtime=time.time()
	print("\ntotal execution time: {} seconds\n".format(float(endtime)-float(starttime)))
