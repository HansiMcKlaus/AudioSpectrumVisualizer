# -*- coding: utf-8 -*-
"""
@author: Maik Simke
Co-authors: Jannick Kremer, Jonas Bögle

Creates a customizable image sequence for the spectrum of an audio file.
"""

import os
from arguments import args, initArgs, processArgs	# Handles arguments
from styles import renderFrame						# Handles styles

from audio2numpy import open_audio					# Works with several audio formats, including .mp3 (Uses ffmpeg as subroutine)
from time import time
import numpy as np
import cv2
import matplotlib.pyplot as plt
from os import mkdir, path
from sys import exit, stdout, stderr
from joblib import Parallel, delayed
from multiprocessing import Manager
import subprocess


"""
Loads audio file.
"""
def loadAudio():
	if(args.test):
		fileData = np.load("testData.npy")
		samplerate = 44100
		return fileData, samplerate
	else:
		if(path.isfile(args.filename) == False):
			exit("Path to file does not exist.")
		else:
			fileData, samplerate = open_audio(args.filename)
			return fileData, samplerate


"""
Processes data from <FILENAME> and assigns data to its respective frame.
"""
def calculateFrameData(fileData, samplerate):
	# Averages multiple channels into a mono channel
	if(len(fileData.shape) == 2):
		if(args.channel == "average"):
			fileData = np.mean(fileData, axis=1)
		elif(args.channel == "left"):
			fileData = fileData[:,0]
		elif(args.channel == "right"):
			fileData = fileData[:,1]

	# Slices fileData to start and end point
	fileData = fileData[int(args.start*samplerate):int(args.end*samplerate)]

	# Splits data into frames
	frameData = []
	stepSize = samplerate/args.framerate
	for i in range(int(np.ceil(len(fileData)/stepSize))):
		frameDataMidpoint = stepSize * i + (stepSize/2)
		frameDataStart = int(frameDataMidpoint - (args.duration/1000/2)*samplerate)
		frameDataEnd = int(frameDataMidpoint + (args.duration/1000/2)*samplerate)

		if(frameDataStart < 0):					# Leftbound data
			emptyFrame = np.zeros(int(args.duration/1000 * samplerate))
			currentFrameData = fileData[0:frameDataEnd]
			emptyFrame[0:len(currentFrameData)] = currentFrameData
			currentFrameData = emptyFrame
		elif(frameDataEnd > len(fileData)):		# Rightbound data
			emptyFrame = np.zeros(int(args.duration/1000 * samplerate))
			currentFrameData = fileData[frameDataStart:]
			emptyFrame[0:len(currentFrameData)] = currentFrameData
			currentFrameData = emptyFrame
		else:									# Inbound data
			currentFrameData = fileData[int(frameDataStart):int(frameDataEnd)]

	# Fourier Transformation (Amplitudes)
		frameDataAmplitudes = abs(np.fft.rfft(currentFrameData))

	# Slices frameDataAmplitudes to only contain the amplitudes between startFrequency and endFrequency
		frameDataAmplitudes = frameDataAmplitudes[int(args.frequencyStart/(samplerate/2)*len(frameDataAmplitudes)):int(args.frequencyEnd/(samplerate/2)*len(frameDataAmplitudes))]

		frameData.append(frameDataAmplitudes)

	return frameData


"""
Creates the bins for every frame. A bin contains an amplitude that will later be represented as the height of a bar, point, line, etc. on the frame.
"""
def createBins(frameData):
	bins = []
	for data in frameData:
		frameBins = []
		for i in range(args.bins):
			if(args.xlog == 0):
				dataStart = int(i*len(data)/args.bins)
				dataEnd = int((i+1)*len(data)/args.bins)
			else:
				dataStart = int((i/args.bins)**args.xlog * len(data))
				dataEnd = int(((i+1)/args.bins)**args.xlog * len(data))
			if(dataEnd == dataStart):
				dataEnd += 1							# Ensures [dataStart:dataEnd] does not result NaN
			frameBins.append(np.mean(data[dataStart:dataEnd]))
		bins.append(frameBins)

	return bins


"""
Smoothes the bins in a frame (Over the past/next n frames).
"""
def smoothBinData(bins):
	binsSmoothed = []
	for frameBinData in bins:
		smoothedBinData = []
		for i in range(len(frameBinData)):
			if(i < args.smoothY):						# First n bins
				smoothedBinData.append(np.mean(frameBinData[:i+args.smoothY+1]))
			elif(i >= len(frameBinData)-args.smoothY):	# Last n bins
				smoothedBinData.append(np.mean(frameBinData[i-args.smoothY:]))
			else:										# Normal Case
				smoothedBinData.append(np.mean(frameBinData[i-args.smoothY:i+args.smoothY+1]))
		binsSmoothed.append(smoothedBinData)

	return binsSmoothed


"""
Creates directory named <DESTINATION>, renders frames from bin data and exports them into it.
Starts at "0.png" for first frame.
"""
def renderSaveFrames(bins):
	bins = bins/np.max(bins)							# Normalize vector length to [0,1]

	if(args.ylog != 0):
		div = np.log2(args.ylog + 1)						# Constant for y-scaling
		bins = np.log2(args.ylog * np.array(bins) + 1)/div	# Y-scaling

	numChunks = int(np.ceil(len(bins)/(args.processes * args.chunkSize))) * args.processes		# Total number of chunks (expanded to be a multiple of args.processes)

	# Create destination folder
	if(path.exists(args.destination) == False and not args.test):
		mkdir(args.destination)

	shMem = Manager().dict()
	shMem['framecount'] = 0
	Parallel(n_jobs=args.processes)(delayed(renderSavePartial)(j, numChunks, bins, shMem) for j in range(args.processes))

	printProgressBar(len(bins), len(bins))
	print()												# New line after progress bar

"""
Renders and saves one process' share of frames in chunks
"""
def renderSavePartial(partialCounter, numChunks, bins, shMem):
	fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
	vid = cv2.VideoWriter(args.destination+"/vid"+str(partialCounter)+".avi", fourcc, args.framerate, (args.width, args.height))

	chunksPerProcess = int(numChunks/args.processes)
	for i in range(chunksPerProcess):
		chunkCounter = partialCounter*chunksPerProcess + i
		renderSaveChunk(chunkCounter, numChunks, bins, vid, shMem)

	vid.release()

"""
Renders and exports one chunk worth of frames
"""
def renderSaveChunk(chunkCounter, numChunks, bins, vid, shMem):
	chunksPerProcess = int(numChunks/args.processes)
	finishedChunkSets = int(chunkCounter/chunksPerProcess)
	framesPerProcess = int(len(bins)/args.processes)
	currentChunkNumInNewSet = chunkCounter - finishedChunkSets * chunksPerProcess
	start = finishedChunkSets * framesPerProcess + currentChunkNumInNewSet * args.chunkSize
	end = start + args.chunkSize

	if(chunkCounter % chunksPerProcess == chunksPerProcess - 1):
		completeChunkSets = int(numChunks/args.processes) - 1
		fullSetChunks = completeChunkSets * args.processes
		fullSetFrames = fullSetChunks * args.chunkSize
		remainingFrames = len(bins) - fullSetFrames
		remainderChunkSize = int(remainingFrames/args.processes)
		end = start + remainderChunkSize

	if(chunkCounter == numChunks - 1):			# Sets the last chunk to do all frames that might be left over, to fix possible rounding errors etc.
		end = len(bins)

	#print("numChunks: "+ str(numChunks) +" chunkCounter: " + str(chunkCounter) + " Start: "+ str(start) +" End: "+ str(end) + "\n")

	frames = renderChunkFrames(bins, start, end)
	for frame in frames:
		vid.write(frame)
		shMem['framecount'] += 1
		printProgressBar(shMem['framecount'], len(bins))

	#saveChunkImages(frames, start, len(bins), shMem)

"""
Renders one chunk of frames
"""
def renderChunkFrames(bins, start, end):
	frames = []
	for j in range(start, end):
		frame = renderFrame(args, bins, j)
		frames.append(frame)
	return frames

"""
Exports one chunk of frames as a .png image sequence into it.
"""
def saveChunkImages(frames, start, length, shMem):
	# Save image sequence
	if(args.test):
		for i in range(len(frames)):
			plt.imsave("testFrame.png", frames[i], vmin=0, vmax=255, cmap='gray')
			shMem['framecount'] += 1
			printProgressBar(shMem['framecount'], length)
	else:
		for i in range(len(frames)):
			plt.imsave(str(args.destination) + "/" + str(start + i) + ".png", frames[i], vmin=0, vmax=255, cmap='gray')
			shMem['framecount'] += 1
			printProgressBar(shMem['framecount'], length)

"""
Progress Bar (Modified from https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console)
"""
def printProgressBar (iteration, total, prefix = "Progress:", suffix = "Complete", decimals = 2, length = 50, fill = '█', printEnd = "\r"):
	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	filledLength = int(length * iteration // total)
	bar = fill * filledLength + '-' * (length - filledLength)
	print(f'\r{prefix} |{bar}| {percent}% ({iteration}/{total}) {suffix}', end = printEnd)


"""
Creates a video from an image sequence.

Returns ffmpeg's exit status (0 on success).
"""
def createVideo():
	vidList = open(args.destination+"/vidList", "x")
	for i in range(args.processes):
		vidList.write("file '{}'\n".format(args.destination+"/vid"+str(i)+".avi"))
	vidList.close()

	arguments = [
		'ffmpeg',
		'-hide_banner',
		'-loglevel', 'error',
		'-stats',
		'-f', 'concat',
		'-safe',
		'0',
		'-i',
		args.destination+"/vidList",
	]

	if(args.videoAudio):
		if(args.start != 0):
			arguments += ['-ss', str(args.start)]
		arguments += ['-i', args.filename]
		if(args.end != -1):
			arguments += ['-t', str(args.end - args.start)]

	arguments += [
		'-c:v', 'libx264',
		'-preset', 'ultrafast',
		'-crf', '16',
		'-pix_fmt', 'yuv420p',
		'-c', 'copy',
		'-y', args.destination+'/finishedVideo.mp4'
	]

	if(args.height % 2 == 1 or args.width % 2 == 1):
		print("Warning: Image height and or width is uneven. Applying padding.")
	print("Converting image sequence to video.")

	proc = subprocess.Popen(
		arguments,
		stdout=stdout,
		stderr=stderr,
	)

	return proc.wait()


"""
Main method. Initializes the complete process from start to finish.
"""
if __name__ == '__main__':
	args = initArgs()									# Arguments as global variables

	startTime = time()

	fileData, samplerate = loadAudio()
	processArgs(args, fileData, samplerate)
	print("Audio succesfully loaded. (1/4)")

	frameData = calculateFrameData(fileData, samplerate)
	del fileData, samplerate
	print("Frame data created. (2/4)")

	bins = createBins(frameData)
	if(args.smoothY > 0):
		bins = smoothBinData(bins)
	del frameData
	print("Bins created. (3/4)")

	print("Creating and saving image sequence. (4/4)")
	renderSaveFrames(bins)
	del bins

	processTime = time() - startTime
	print("Created and saved Image Sequence in " + str(format(processTime, ".3f")) + " seconds.")

	if(args.videoAudio or args.video):
		if createVideo() != 0:
			exit("ffmpeg exited with a failure.")
		os.remove(args.destination+"/vidList")
		for i in range(args.processes):
			os.remove(args.destination+"/vid"+str(i)+".avi")
		
		processTime = time() - startTime
		print("Succesfully converted image sequence to video in " + str(format(processTime, ".3f")) + " seconds.")

	print("Finished!")