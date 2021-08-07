# -*- coding: utf-8 -*-
"""
@author: Maik Simke
Co-author: Jannick Kremer, Jonas Bögle

Creates a customizable image sequence for the spectrum of an audio file.

Dependencies: numpy, audio2numpy, matplotlib, ffmpeg
"""

"""
TODO: Chunking (methods renderFrames and saveImageSequence need to be merged)
TODO: Check if file exists
TODO: Optional linear interpolation for bin calculation if bin acces only one point in array
TODO: x-axis and y-axis log scaling
TODO: Implement different styles
		Styles:
			Bar: Filled, Blocks, Centered on y-axis
			Points: Shapes
			Line: Thicknes
			Filled
TODO: Implement color
TODO: Implement channel selection
"""

import argparse
from audio2numpy import open_audio					# Works with several audio formats, including .mp3 (Uses ffmpeg as subroutine)
from time import time
import numpy as np
import matplotlib.pyplot as plt
from os import mkdir, path, system
from joblib import Parallel, delayed


# Instantiate the parser
parser = argparse.ArgumentParser(description="Creates an image sequence for the audio spectrum of an audio file.")

# Required positional arguments
parser.add_argument("filename", type=str,
					help="Name or path of the audio file")
parser.add_argument("destination", type=str, nargs='?', default="imageSequence",
					help="Name or path of the created directory in which the image sequence is saved. Default: Image Sequence")

# Optional arguments
parser.add_argument("-b", "--bins", type=int, default=64,
					help="Amount of bins (bars, points, etc). Default: 64")

parser.add_argument("-ht", "--height", type=int, default=540,
					help="Max height of the bins (height of the images). Default: 540px")

parser.add_argument("-w", "--width", type=int, default=1920,
					help="Width of the image. Will be overwritten if both bin_width AND bin_spacing is given! Default: 1920px")

parser.add_argument("-bw", "--bin_width", type=str, default="auto",
					help="Width of the bins. Default: auto (5/6 * width/bins)")

parser.add_argument("-bs", "--bin_spacing", type=str, default="auto",
					help="Spacing between bins. Default: auto (1/6 * width/bins)")

parser.add_argument("-fr", "--framerate", type=float, default=30,
					help="Framerate of the image sequence (Frames per second). Default: 30fps")

parser.add_argument("-xlog", type=float, default=0,
					help="Scales the X-axis logarithmically to a given base. Default: 0 (Linear)")

parser.add_argument("-ylog", type=float, default=0,
					help="Scales the Y-axis logarithmically to a given base. Default: 0 (Linear)")

parser.add_argument("-st", "--smoothT", type=str, default="0",
					help="Smoothing over past/next <smoothT> frames (Smoothes bin over time). If smoothT=auto: Automatic smoothing is applied (framerate/15). Default: 0")

parser.add_argument("-sy", "--smoothY", type=str, default="0",
					help="Smoothing over past/next <smoothY> bins (Smoothes bin with adjacent bins). If smoothY=auto: Automatic smoothing is applied (bins/32). Default: 0")

parser.add_argument("-s", "--start", type=float, default=-1,
					help="Begins render at <start> seconds. If start=-1: Renders from the start of the sound file. Default: -1")

parser.add_argument("-e", "--end", type=float, default=-1,
					help="Ends render at <end> seconds. If end=-1: Renders to the end of the sound file. Default: -1")

parser.add_argument("-fs", "--frequencyStart", type=float, default=-1,
					help="Limits the range of frequencies to <frequencyStart>Hz and onward. If frequencyStart=-1: Starts at 0Hz. Default: -1")

parser.add_argument("-fe", "--frequencyEnd", type=float, default=-1,
					help="Limits the range of frequencies to <frequencyEnd>Hz. If frequencyEnd=-1: Ends at highest frequency. Default: -1")

parser.add_argument("-t", "--test", action='store_true', default=False,
					help="Renders only a single frame for style testing. Default: False")

parser.add_argument("-v", "--video", action='store_true', default=False,
					help="Additionally creates a video (.mp4) from image sequence. Default: False")

parser.add_argument("-va", "--videoAudio", action='store_true', default=False,
					help="Additionally creates a video (.mp4) from image sequence and audio. Default: False")

parser.add_argument("-ds", "--disableSmoothing", action='store_true', default=False,
					help="Disables all smoothing (smoothT and smoothY). Default: False")

args = parser.parse_args()


# Loads audio file
def loadAudio():
	fileData, samplerate = open_audio(args.filename)
	return fileData, samplerate


# Cleans up bad inputs and processes arguments that can not be calculated independently
def processArgs(fileData, samplerate):
	channels = len(fileData.shape)

	# Clean up bad input
	while(args.bins <= 0):
		args.bins = int(input("Must have at least one bin. New amount of bins: "))

	while(args.height <= 0):
		args.height = int(input("Height must be at least 1px. New height: "))

	while(args.width <= 0):
		args.width = int(input("Width must be at least 1px. New width: "))

	while(args.framerate <= 0):
		args.framerate = float(input("Framerate must be at least 1. New framerate: "))

	while(args.xlog < 0):
		args.xlog = float(input("Scalar must not be smaller than 0. New Scalar: "))

	while(args.ylog < 0):
		args.ylog = float(input("Scalar must not be smaller than 0. New Scalar: "))

	if(args.bin_width != "auto"):
		while(float(args.bin_width) < 1):
			args.bin_width = float(input("Bin width must be at least 1px. New bin width: "))

	if(args.bin_spacing != "auto"):
		while(float(args.bin_spacing) < 0):
			args.bin_spacing = float(input("Bin spacing must be 0px or higher. New bin width: "))

	if(args.smoothT != "auto"):
		while(int(args.smoothT) < 0):
			args.smoothT = int(input("Smoothing scalar for smoothing between frames must be 0 or bigger. New Smoothing scalar: "))

	if(args.smoothY != "auto"):
		while(int(args.smoothY) < 0):
			args.smoothY = int(input("Smoothing scalar for smoothing in frame must be 0 or bigger. New Smoothing scalar: "))

	if(args.start != -1):
		while(float(args.start) < 0):
			args.start = float(input("Start time must be 0 or later. New start time: "))

	if(args.end != -1):
		while(float(args.end) <= 0):
			args.end = float(input("End time must be later than 0. New end time: "))

	if(args.start != -1):
		while(float(args.start) >= len(fileData)/samplerate):
			args.start = float(input("Start time exceeds audio length of " + str(format(len(fileData)/samplerate, ".3f")) + "s. New start time (-1 to set start time at audio start): "))

	if(args.end != -1):
		while(float(args.end) > len(fileData)/samplerate):
			args.end = float(input("End time exceeds audio length of " + str(format(len(fileData)/samplerate, ".3f")) + "s. New end time (-1 to set end time at audio end): "))

	if(args.start != -1 and args.end != -1):
		while(float(args.start) >= float(args.end)):
			args.start = float(input("Start time must predate end time. New start time: "))
			args.end = float(input("End time must postdate start time. New end time: "))

	if(args.frequencyStart != -1):
		while(float(args.frequencyStart) < 0):
			args.frequencyStart = float(input("Frequency start must be 0 or higher. New start frequency: "))

	if(args.frequencyEnd != -1):
		while(float(args.frequencyEnd) <= 0):
			args.frequencyEnd = float(input("Frequency end must be higher than 0. New end frequency: "))

	if(args.frequencyStart != -1):
		while(float(args.frequencyStart) >= samplerate/2):
			args.frequencyStart = float(input("Frequency start exceeds max frequency of " + str(int(samplerate/2)) + "Hz. New start frequency (-1 to set frequency start at lowest frequency): "))

	if(args.frequencyEnd != -1):
		while(float(args.frequencyEnd) > samplerate/2):
			args.frequencyEnd = float(input("Frequency end exceeds max frequency of " + str(int(samplerate/2)) + "Hz. New end frequency (-1 to set frequency end at highest frequency): "))

	if(args.frequencyStart != -1 and args.frequencyEnd != -1):
		while(float(args.frequencyStart) >= float(args.frequencyEnd)):
			args.frequencyStart = float(input("Frequency start must be lower than frequency end. New start frequency: "))
			args.frequencyEnd = float(input("Frequency end must be higher than frequency start. New end frequency: "))

	# Process optional arguments:
	if(args.disableSmoothing == True):
		args.smoothT = 0
		args.smoothY = 0

	if(args.bin_width == "auto" and args.bin_spacing != "auto"):		# Only bin_spacing is given
		args.bin_width = args.width/args.bins - float(args.bin_spacing)
		args.bin_spacing = float(args.bin_spacing)
	elif(args.bin_width != "auto" and args.bin_spacing == "auto"):		# Only bin_width is given
		args.bin_width = float(args.bin_width)
		args.bin_spacing = args.width/args.bins - float(args.bin_width)
	elif(args.bin_width == "auto" and args.bin_spacing == "auto"):		# Neither is given
		args.bin_width = args.width/args.bins * (5/6)
		args.bin_spacing = args.width/args.bins * (1/6)
	else:																# Both are given (Overwrites width)
		args.bin_width = float(args.bin_width)
		args.bin_spacing = float(args.bin_spacing)

	if(args.smoothT == "auto"):						# Smoothing over past/next <smoothT> frames (Smoothes bin over time). If smoothT=auto: Automatic smoothing is applied (framerate/15). Default: 0
		args.smoothT = int(args.framerate/15)
	else:
		args.smoothT = int(args.smoothT)

	if(args.smoothY == "auto"):						# Smoothing over past/next <smoothY> bins (Smoothes bin with adjacent bins). If smoothY=auto: Automatic smoothing is applied (bins/32). Default: 0
		args.smoothY = int(args.bins/32)
	else:
		args.smoothY = int(args.smoothY)

	if(args.start == -1 or args.test == 1):			# Begins render at <start> seconds. If start=-1: Renders from the start of the sound file. Default: -1
		args.start = 0
	else:
		args.start = float(args.start)

	if(args.end == -1 or args.test == 1):			# Ends render at <end> seconds. If end=-1: Renders to the end of the sound file. Default: -1
		args.end = len(fileData)/samplerate
	else:
		args.end = float(args.end)

	if(args.frequencyStart == -1):					# Limits the range of frequencies to <frequencyStart>Hz and onward. If frequencyStart=-1: Starts at 0Hz. Default: -1
		args.frequencyStart = 0
	else:
		args.frequencyStart = float(args.frequencyStart)

	if(args.frequencyEnd == -1):					# Limits the range of frequencies to <frequencyEnd>Hz. If frequencyEnd=-1: Ends at highest frequency. Default: -1
		args.frequencyEnd = samplerate/2
	else:
		args.frequencyEnd = float(args.frequencyEnd)


"""
Processes data from <FILENAME> and assigns data to its respective frame.
"""
def calculateFrameData(fileData, samplerate):
	frameData = []
	frameCounter = 0

	# Averages multiple channels into a mono channel
	if(len(fileData.shape) == 2):
		fileData = np.mean(fileData, axis=1)

	# Slices fileData to start and end point
	fileData = fileData[int(args.start*samplerate):int(args.end*samplerate)]

	# Splits data into frames
	stepSize = samplerate/args.framerate
	while (stepSize * frameCounter < len(fileData)):
		frameDataStart = int(stepSize * frameCounter)
		frameDataEnd = int(stepSize * (frameCounter + 1))

	# Fourier Transformation (Amplitudes)
		currentFrameData = fileData[int(frameDataStart):int(frameDataEnd)]
		frameDataAmplitudes = abs(np.fft.rfft(currentFrameData))

	# Fourier Transformation (Frequencies)
		#frameDataFrequencies = np.fft.rfftfreq(len(currentFrameData), 1/samplerate)
		#frameData.append([frameDataAmplitudes, frameDataFrequencies])

	# Slices frameDataAmplitudes to only contain the amplitudes between startFrequency and endFrequency
		frameDataAmplitudes = frameDataAmplitudes[int(args.frequencyStart/(samplerate/2)*len(frameDataAmplitudes)):int(args.frequencyEnd/(samplerate/2)*len(frameDataAmplitudes))]

		frameData.append(frameDataAmplitudes)
		frameCounter += 1

	# Scales last frameData to full length if it is not "full" (Less than a frame long, thus has less data than the rest)
	if(len(frameData[-1]) != len(frameData[0])):
		lastFrame = []
		for i in range(len(frameData[0])):
			lastFrame.append(int(i/stepSize*len(frameData[-1])))
		frameData[-1] = lastFrame

	return frameData


"""
Smoothes the bins in time (Over the past/next n frames).
Creates a kind of foresight/delay as it takes data from previous/next frames --> Factor should be kept small.
"""
def smoothFrameData(frameData):
	frameDataSmoothed = []
	for i in range(len(frameData)):
		if(i < args.smoothT):							# First n frame data
			frameDataSmoothed.append(np.mean(frameData[:i+args.smoothT+1], axis=0))
		elif(i >= len(frameData)-args.smoothT):			# Last n frame data
			frameDataSmoothed.append(np.mean(frameData[i-args.smoothT:], axis=0))
		else:											# Normal Case
			frameDataSmoothed.append(np.mean(frameData[i-args.smoothT:i+args.smoothT+1], axis=0))

	return frameDataSmoothed


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
				#dataStart = int((i/args.bins))
				#dataEnd = 
				dataStart = int(((i*len(data)/args.bins)/len(data))**args.xlog * len(data))
				dataEnd = int((((i+1)*len(data)/args.bins)/len(data))**args.xlog * len(data))
			if (dataEnd == dataStart):
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
Renders frames from bin data.
"""
def renderFrames(bins):
	bins = bins/np.max(bins)						# Normalize vector length to [0,1]
	frames = []
	for j in range(len(bins)):
		frame = np.zeros((args.height, int(args.bins*(args.bin_width+args.bin_spacing))))
		# frame = frame.astype(np.uint8)			# Set datatype to uint8 to reduce RAM usage (Doesn't work)
		for k in range(args.bins):
			if (args.ylog == 0):
				binHeight = np.ceil(bins[j, k] * frame.shape[0])
			else:
				binHeight = np.ceil(np.log2(args.ylog * bins[j, k] + 1)/np.log2(args.ylog + 1) * frame.shape[0])
			frame[int(0):int(binHeight),
				int(k*args.bin_width + k*args.bin_spacing):int((k+1)*args.bin_width + k*args.bin_spacing)] = 1
		frame = np.flipud(frame)
		frames.append(frame)

	return frames


"""
Creates directory named <DESTINATION> and exports the frames as a .png image sequence into it.
Starts at "0.png" for first frame.
"""
def saveImageSequence(frames):
	# Create destination folder
	if not path.exists(args.destination):
		mkdir(args.destination)
	
	# Save image sequence
	frameCounter = 0
	for frame in frames:
		plt.imsave(str(args.destination) + "/" + str(frameCounter) + ".png", frame, cmap='gray')
		frameCounter += 1
		printProgressBar(frameCounter, len(frames))
	print()											# New line


"""
Progress Bar (Modified from https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console)
"""
def printProgressBar (iteration, total, prefix = "Progress:", suffix = "Complete", decimals = 2, length = 50, fill = '█', printEnd = "\r"):
	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	filledLength = int(length * iteration // total)
	bar = fill * filledLength + '-' * (length - filledLength)
	print(f'\r{prefix} |{bar}| {percent}% ({iteration}/{total}) {suffix}', end = printEnd)


"""
Renders a single frame from testData (00:11:000 to 00:11:033 of "Bursty Greedy Spider" by Konomi Suzuki) for style testing.
"""
def testRender():
	testData = np.load("testData.npy")
	args.start = 0
	args.end = "False"

	frameData = calculateFrameData(44100, testData)
	bins = createBins(frameData)
	frames = renderFrames(bins)
	plt.imsave("testFrame.png", frames[0], cmap='gray')
	print("Created Frame for Style Testing in current directory.")


"""
Creates a video from an image sequence.
"""
def createVideo():
	flags = '-hide_banner -loglevel error '
	flags += '-r {} '.format(str(args.framerate))
	flags += '-i "{}/%0d.png" '.format(str(args.destination))
	if args.videoAudio:
		print("Converting image sequence to video (with audio).")
		if(args.start != 0):
			flags += '-ss {} '.format(str(args.start))
		flags += '-i "{}" '.format(str(args.filename))
		if(args.end != "False"):
			flags += '-t {} '.format(args.end - args.start)
	else:
		print("Converting image sequence to video.")

	flags += '-c:v libx264 -preset ultrafast -crf 16 -pix_fmt yuv420p -y "{}.mp4"'.format(str(args.destination))
	
	system('ffmpeg ' + flags)


"""
Main method. Initializes the complete process from start to finish.
"""
def full():
	startTime = time()

	fileData, samplerate = loadAudio()
	print("Audio succesfully loaded. (1/4)")

	processArgs(fileData, samplerate)

	frameData = calculateFrameData(fileData, samplerate)
	if(args.smoothT > 0):
		frameData = smoothFrameData(frameData)
	print("Frame data created. (2/4)")

	bins = createBins(frameData)
	if(args.smoothY > 0):
		bins = smoothBinData(bins)
	print("Bins created. (3/4)")

	frames = renderFrames(bins)
	print("Frames created. (4/4)")

	print("Saving Image Sequence to: " + args.destination)
	saveImageSequence(frames)

	processTime = time() - startTime
	print("Created and saved Image Sequence in " + str(format(processTime, ".3f")) + " seconds.")

	if(args.videoAudio or args.video):
		createVideo()
		processTime = time() - startTime
		print("Succesfully converted image sequence to video in " + str(format(processTime, ".3f")) + " seconds.")

	print("Finished!")

if (args.test == 1):
	testRender()
else:
	full()
