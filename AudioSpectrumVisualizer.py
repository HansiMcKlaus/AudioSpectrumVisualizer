# -*- coding: utf-8 -*-
"""
@author: Maik Simke
Co-authors: Jannick Kremer, Jonas Bögle

Creates a customizable image sequence for the spectrum of an audio file.
"""

from arguments import args, initArgs, processArgs	# Handles arguments
from styles import renderFrame						# Handles styles

from audio2numpy import open_audio					# Works with several audio formats, including .mp3 (Uses ffmpeg as subroutine)
from time import time
import numpy as np
import cv2
import matplotlib.pyplot as plt
from os import mkdir, path, remove, rmdir
from sys import exit, stdout, stderr
from joblib import Parallel, delayed
from multiprocessing import Manager
import subprocess

VID_CODEC = "mp4v"
VID_EXT = ".mp4"


"""
Loads audio file.
"""
def loadAudio():
	if args.test:
		fileData = np.load("testData.npy")
		samplerate = 44100
		return fileData, samplerate
	else:
		if not path.isfile(args.filename):
			exit("Path to file does not exist.")
		else:
			fileData, samplerate = open_audio(args.filename)
			return fileData, samplerate


"""
Processes data from <FILENAME> and assigns data to its respective channels frame.
"""
def calculateFrameData(fileData, samplerate):
	# Chooses what channels to be calculated
	channels = []

	if len(fileData.shape) > 1:						# Converts multiple channels to single channel
		if args.channel == "average":
			channels.append(np.mean(fileData, axis=1))
		elif args.channel == "left":
			channels.append(fileData[:,0])
		elif args.channel == "right":
			channels.append(fileData[:,1])
		else:											# Adds all channels (Stereo, Surround)
			for i in range(fileData.shape[1]):
				channels.append(fileData[:,i])
	else:												# Adds mono channel
		channels.append(fileData)

	frameData = []
	for channel in channels:

		# Slices channelData to start and end point
		channelData = channel[int(args.start*samplerate):int(args.end*samplerate)]

		# Splits data into frames
		channelFrameData = []
		stepSize = samplerate/args.framerate
		for i in range(int(np.ceil(len(channelData)/stepSize))):
			frameDataMidpoint = stepSize * i + (stepSize/2)
			frameDataStart = int(frameDataMidpoint - (args.duration/1000/2)*samplerate)
			frameDataEnd = int(frameDataMidpoint + (args.duration/1000/2)*samplerate)

			if frameDataStart < 0:						# Leftbound data
				emptyFrame = np.zeros(int(args.duration/1000 * samplerate))
				currentFrameData = channelData[0:frameDataEnd]
				emptyFrame[0:len(currentFrameData)] = currentFrameData
				currentFrameData = emptyFrame
			elif frameDataEnd > len(channelData):		# Rightbound data
				emptyFrame = np.zeros(int(args.duration/1000 * samplerate))
				currentFrameData = channelData[frameDataStart:]
				emptyFrame[0:len(currentFrameData)] = currentFrameData
				currentFrameData = emptyFrame
			else:										# Inbound data
				currentFrameData = channelData[int(frameDataStart):int(frameDataEnd)]

			# Fourier Transformation (Amplitudes)
			frameDataAmplitudes = abs(np.fft.rfft(currentFrameData))

			# Slices frameDataAmplitudes to only contain the amplitudes between startFrequency and endFrequency
			frameDataAmplitudes = frameDataAmplitudes[int(args.frequencyStart/(samplerate/2)*len(frameDataAmplitudes)):int(args.frequencyEnd/(samplerate/2)*len(frameDataAmplitudes))]

			channelFrameData.append(frameDataAmplitudes)

		#frameData.append(channelFrameData)
		frameData.append(channelFrameData)

	return frameData


"""
Creates the bins for every channels frame. A bin contains an amplitude that will later be represented as the height of a bar, point, line, etc. on the frame.
"""
def createBins(frameData):
	bins = []
	for channel in frameData:
		channelBins = []
		for data in channel:
			frameBins = []
			for i in range(args.bins):
				if args.xlog == 0:
					dataStart = int(i*len(data)/args.bins)
					dataEnd = int((i+1)*len(data)/args.bins)
				else:
					dataStart = int((i/args.bins)**args.xlog * len(data))
					dataEnd = int(((i+1)/args.bins)**args.xlog * len(data))
				if dataEnd == dataStart:
					dataEnd += 1						# Ensures [dataStart:dataEnd] does not result NaN
				frameBins.append(np.mean(data[dataStart:dataEnd]))
			channelBins.append(frameBins)

		bins.append(channelBins)
	
	return bins


"""
Smoothes the bins in a frame (Over the past/next n frames).
"""
def smoothBinData(bins):
	binsSmoothed = []
	for channel in bins:
		channelBinsSmoothed = []
		for frameBinData in channel:
			smoothedBinData = []
			for i in range(len(frameBinData)):
				if i < args.smoothY:						# First n bins
					smoothedBinData.append(np.mean(frameBinData[:i+args.smoothY+1]))
				elif i >= len(frameBinData)-args.smoothY:	# Last n bins
					smoothedBinData.append(np.mean(frameBinData[i-args.smoothY:]))
				else:										# Normal Case
					smoothedBinData.append(np.mean(frameBinData[i-args.smoothY:i+args.smoothY+1]))
			channelBinsSmoothed.append(smoothedBinData)

		binsSmoothed.append(channelBinsSmoothed)

	return binsSmoothed


"""
Creates directory named <args.destination>
Renders frames from bin data and exports them directly to <args.processes> partial videos
If args.imageSequence is set, instead exports frames as images into the directory
Starts at "0.png" for first frame.
"""
def renderSaveFrames(bins):
	bins = bins/np.max(bins)							# Normalize vector length to [0,1]

	if args.ylog != 0:
		div = np.log2(args.ylog + 1)						# Constant for y-scaling
		bins = np.log2(args.ylog * np.array(bins) + 1)/div	# Y-scaling

	numChunks = int(np.ceil(bins.shape[1]/(args.processes * args.chunkSize))) * args.processes		# Total number of chunks (expanded to be a multiple of args.processes)

	shMem = Manager().dict()
	shMem['framecount'] = 0
	Parallel(n_jobs=args.processes)(delayed(renderSavePartial)(j, numChunks, bins, shMem) for j in range(args.processes))

	printProgressBar(bins.shape[1], bins.shape[1])
	print()												# New line after progress bar

"""
Renders and saves one process' share of frames in chunks
"""
def renderSavePartial(partialCounter, numChunks, bins, shMem):
	if args.imageSequence:
		vid = None
	else:
		fourcc = cv2.VideoWriter_fourcc(*VID_CODEC)
		dest = args.destination+"/part"+str(partialCounter)+VID_EXT
		vid = cv2.VideoWriter(dest, fourcc, args.framerate, (args.width, args.height))

	chunksPerProcess = int(numChunks/args.processes)
	for i in range(chunksPerProcess):
		chunkCounter = partialCounter*chunksPerProcess + i
		renderSaveChunk(chunkCounter, numChunks, bins, vid, shMem)

	if not args.imageSequence:
		vid.release()

"""
Renders and exports one chunk worth of frames
"""
def renderSaveChunk(chunkCounter, numChunks, bins, vid, shMem):
	chunksPerProcess = int(numChunks/args.processes)
	finishedChunkSets = int(chunkCounter/chunksPerProcess)
	framesPerProcess = int(bins.shape[1]/args.processes)
	currentChunkNumInNewSet = chunkCounter - finishedChunkSets * chunksPerProcess
	start = finishedChunkSets * framesPerProcess + currentChunkNumInNewSet * args.chunkSize
	end = start + args.chunkSize

	if chunkCounter % chunksPerProcess == chunksPerProcess - 1:
		completeChunkSets = int(numChunks/args.processes) - 1
		fullSetChunks = completeChunkSets * args.processes
		fullSetFrames = fullSetChunks * args.chunkSize
		remainingFrames = bins.shape[1] - fullSetFrames
		remainderChunkSize = int(remainingFrames/args.processes)
		end = start + remainderChunkSize

	frames = renderChunkFrames(bins, start, end)
	if args.test:
		plt.imsave("testFrame.png", frames[0], vmin=0, vmax=255, cmap='gray')
	else:
		for i in range(len(frames)):
			if args.imageSequence:
				plt.imsave(str(args.destination) + "/" + str(start + i) + ".png", frames[i], vmin=0, vmax=255, cmap='gray')
			else:
				vid.write(frames[i])
			shMem['framecount'] += 1
			printProgressBar(shMem['framecount'], bins.shape[1])

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
Progress Bar (Modified from https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console)
"""
def printProgressBar (iteration, total, prefix = "Progress:", suffix = "Complete", decimals = 2, length = 50, fill = '█', printEnd = "\r"):
	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	filledLength = int(length * iteration // total)
	bar = fill * filledLength + '-' * (length - filledLength)
	print(f'\r{prefix} |{bar}| {percent}% ({iteration}/{total}) {suffix}', end = printEnd)


"""
Concatenates partial videos to full video and overlays audio.

Returns ffmpeg's exit status (0 on success).
"""
def createVideo():
	with open(args.destination+"/vidList", "x") as vidList:
		for i in range(args.processes):
			vidList.write("file 'part"+ str(i) + VID_EXT +"'\n")

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

	if args.start != 0:
		arguments += ['-ss', str(args.start)]
	arguments += ['-i', args.filename]
	if args.end != -1:
		arguments += ['-t', str(args.end - args.start)]

	arguments += [
		'-c:v', 'libx264',
		'-preset', 'ultrafast',
		'-crf', '16',
		'-pix_fmt', 'yuv420p',
		'-c', 'copy',
		'-y', args.destination+VID_EXT
	]

	proc = subprocess.Popen(
		arguments,
		stdout=stdout,
		stderr=stderr,
	)

	return proc.wait()

def cleanupFiles(directoryExisted):
	remove(args.destination+"/vidList")
	for i in range(args.processes):
		remove(args.destination+"/part"+str(i)+VID_EXT)

	if not directoryExisted:
		try:
			rmdir(args.destination)
		except OSError as error:
			print(error)
			print("Directory '{}' can not be removed".format(args.destination))


"""
Main method. Initializes the complete process from start to finish.
"""
if __name__ == '__main__':
	args = initArgs()									# Arguments as global variables

	startTime = time()

	maxSteps = 5
	if args.imageSequence:
		maxSteps = 4

	# Create destination folder
	directoryExisted = False
	if not path.exists(args.destination) and not args.test:
		mkdir(args.destination)
	else:
		directoryExisted = True


	print("Loading audio. (1/{})".format(maxSteps))
	fileData, samplerate = loadAudio()
	processArgs(args, fileData, samplerate)

	print("Creating frame data. (2/{})".format(maxSteps))
	frameData = calculateFrameData(fileData, samplerate)
	del fileData, samplerate

	print("Creating bins. (3/{})".format(maxSteps))
	bins = createBins(frameData)
	if args.smoothY > 0:
		bins = smoothBinData(bins)
	del frameData

	if args.imageSequence:
		print("Creating and saving image sequence. (4/{})".format(maxSteps))
	else:
		print("Creating and saving partial videos. (4/{})".format(maxSteps))
	renderSaveFrames(bins)
	del bins

	if not args.imageSequence:
		print("Concatenating to full video and overlaying audio. (5/{})".format(maxSteps))
		if createVideo() != 0:
			exit("ffmpeg exited with a failure.")


	processTime = time() - startTime
	print("Completed successfully in " + str(format(processTime, ".3f")) + " seconds.")

	if not args.imageSequence:
		print("Cleaning up files.")
		cleanupFiles(directoryExisted)

	print("Finished!")
