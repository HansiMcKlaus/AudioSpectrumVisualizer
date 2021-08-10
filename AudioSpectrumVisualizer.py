# -*- coding: utf-8 -*-
"""
@author: Maik Simke
Co-authors: Jannick Kremer, Jonas Bögle

Creates a customizable image sequence for the spectrum of an audio file.

Dependencies: numpy, audio2numpy, matplotlib, ffmpeg
"""

"""
TODO: Fix last frame
TODO: Implement different styles
		Styles:
			Bar: Filled, Blocks, Centered on y-axis
			Points: Shapes
			Line: Thicknes
			Filled
"""

import argparse
from audio2numpy import open_audio					# Works with several audio formats, including .mp3 (Uses ffmpeg as subroutine)
from time import time
import numpy as np
import matplotlib.pyplot as plt
from os import mkdir, path, system
from sys import exit
from joblib import Parallel, delayed, cpu_count
from multiprocessing import Manager

DEFAULT_CHUNKSIZE = 128


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
					help="Height of the image in px. Default: 540")

parser.add_argument("-w", "--width", type=int, default=1920,
					help="Width of the image in px. Will be overwritten if both bin_width AND bin_spacing is given! Default: 1920")

parser.add_argument("-bw", "--bin_width", type=str, default="auto",
					help="Width of the bins in px. Default: auto (5/6 * width/bins)")

parser.add_argument("-bs", "--bin_spacing", type=str, default="auto",
					help="Spacing between bins in px. Default: auto (1/6 * width/bins)")

parser.add_argument("-c", "--color", type=str, default="ffffff",
					help="Color of bins (bars, points, etc). Ex: ff0000 or red. Default: ffffff (white)")

parser.add_argument("-bgc", "--backgroundColor", type=str, default="000000",
					help="Color of the background. Ex: ff0000 or red. Default: 000000 (black)")

parser.add_argument("-fr", "--framerate", type=float, default=30,
					help="Framerate of the image sequence (Frames per second). Default: 30")

parser.add_argument("-ch", "--channel", type=str, default="average",
					help="Which channel to use (left, right, average). Default: average")

parser.add_argument("-xlog", type=float, default=0,
					help="Scales the X-axis logarithmically to a given base. Default: 0 (linear)")

parser.add_argument("-ylog", type=float, default=0,
					help="Scales the Y-axis logarithmically to a given base. Default: 0 (linear)")

parser.add_argument("-st", "--smoothT", type=str, default="0",
					help="Smoothing over past/next <smoothT> frames (Smoothes bin over time). If smoothT=auto: Automatic smoothing is applied (framerate/15). Default: 0")

parser.add_argument("-sy", "--smoothY", type=str, default="0",
					help="Smoothing over past/next <smoothY> bins (Smoothes bin with adjacent bins). If smoothY=auto: Automatic smoothing is applied (bins/32). Default: 0")

parser.add_argument("-s", "--start", type=float, default=0,
					help="Begins render at <start> seconds. Default: 0")

parser.add_argument("-e", "--end", type=float, default=-1,
					help="Ends render at <end> seconds. If end=-1: Renders to the end of the sound file. Default: -1")

parser.add_argument("-fs", "--frequencyStart", type=float, default=0,
					help="Limits the range of frequencies to <frequencyStart>Hz and onward. Default: -1")

parser.add_argument("-fe", "--frequencyEnd", type=float, default=-1,
					help="Limits the range of frequencies to <frequencyEnd>Hz. If frequencyEnd=-1: Ends at highest frequency. Default: -1")

parser.add_argument("-cs", "--chunkSize", type=int, default=-1,
					help="Amount of frames cached before clearing (Higher chunk size lowers render time, but increases RAM usage). Default: 64")

parser.add_argument("-cr", "--cores", type=int, default=-1,
					help="Number of cores to use for rendering and export. Default: All cores")

parser.add_argument("-t", "--test", action='store_true', default=False,
					help="Renders only a single frame for style testing. Default: False")

parser.add_argument("-v", "--video", action='store_true', default=False,
					help="Additionally creates a video (.mp4) from image sequence. Default: False")

parser.add_argument("-va", "--videoAudio", action='store_true', default=False,
					help="Additionally creates a video (.mp4) from image sequence and audio. Default: False")

parser.add_argument("-ds", "--disableSmoothing", action='store_true', default=False,
					help="Disables all smoothing (smoothT and smoothY). Default: False")

args = parser.parse_args()


# Loads audio file.
def loadAudio():
	if(path.isfile(args.filename) == False):
		exit("Path to file does not exist.")

	fileData, samplerate = open_audio(args.filename)
	return fileData, samplerate


# Exit on invalid inputs and processes arguments that can not be calculated independently.
def processArgs(fileData, samplerate):
	channels = len(fileData.shape)

	# Exit on invalid input
	if(args.bins <= 0):
		exit("Must have at least one bin.")

	if(args.height <= 0):
		exit("Height must be at least 1px.")

	if(args.width <= 0):
		exit("Width must be at least 1px.")

	if(args.framerate <= 0):
		exit("Framerate must be at least 1.")

	if(args.channel != "left" and args.channel != "right" and args.channel != "average"):
		exit("Invalid channel. Valid channels: left, right, average.")

	if(args.xlog < 0):
		exit("Scalar for xlog must not be smaller than 0.")

	if(args.ylog < 0):
		exit("Scalar for ylog must not be smaller than 0.")

	if(args.bin_width != "auto"):
		if(float(args.bin_width) < 1):
			exit("Bin width must be at least 1px.")

	if(args.bin_spacing != "auto"):
		if(float(args.bin_spacing) < 0):
			exit("Bin spacing must be 0px or higher")

	if(args.smoothT != "auto"):
		if(int(args.smoothT) < 0):
			exit("Smoothing scalar for smoothing between frames must be 0 or higher.")

	if(args.smoothY != "auto"):
		if(int(args.smoothY) < 0):
			exit("Smoothing scalar for smoothing in frame must be 0 or higher.")

	if(args.start != 0):
		if(float(args.start) < 0):
			exit("Start time must be 0 or later.")

	if(args.end != -1):
		if(float(args.end) <= 0):
			exit("End time must be later than 0.")

	if(args.start != 0):
		if(float(args.start) >= len(fileData)/samplerate):
			exit("Start time exceeds audio length of " + str(format(len(fileData)/samplerate, ".3f")) + "s.")

	if(args.end != -1):
		if(float(args.end) > len(fileData)/samplerate):
			exit("End time exceeds audio length of " + str(format(len(fileData)/samplerate, ".3f")) + "s.")

	if(args.start != 0 and args.end != -1):
		if(float(args.start) >= float(args.end)):
			exit("Start time must predate end time.")

	if(args.frequencyStart != 0):
		if(float(args.frequencyStart) < 0):
			exit("Frequency start must be 0 or higher.")

	if(args.frequencyEnd != -1):
		if(float(args.frequencyEnd) <= 0):
			exit("Frequency end must be higher than 0.")

	if(args.frequencyStart != 0):
		if(float(args.frequencyStart) >= samplerate/2):
			exit("Frequency start exceeds max frequency of " + str(int(samplerate/2)) + "Hz.")

	if(args.frequencyEnd != -1):
		if(float(args.frequencyEnd) > samplerate/2):
			exit("Frequency end exceeds max frequency of " + str(int(samplerate/2)) + "Hz.")

	if(args.frequencyStart != 0 and args.frequencyEnd != -1):
		if(float(args.frequencyStart) >= float(args.frequencyEnd)):
			exit("Frequency start must be lower than frequency end.")

	if(args.chunkSize == 0 or args.chunkSize < -1):
		exit("Chunk size must be at least 1.")

	if(args.cores == 0 or args.cores < -1):
		exit("Number of cores must be at least 1")

	# Process optional arguments:
	if(args.disableSmoothing):
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

	if(args.color == "black"):
		args.color = [0, 0, 0]
	elif(args.color == "white"):
		args.color = [255, 255, 255]
	elif(args.color == "red"):
		args.color = [255, 0, 0]
	elif(args.color == "green"):
		args.color = [0, 255, 0]
	elif(args.color == "blue"):
		args.color = [0, 0, 255]
	elif(args.color == "yellow"):
		args.color = [255, 255, 0]
	elif(args.color == "cyan"):
		args.color = [0, 255, 255]
	elif(args.color == "magenta"):
		args.color = [255, 0, 255]
	else:																# Converts HEX to RGB
		color = []
		for i in (0, 2, 4):
			color.append(int(args.color[i:i+2], 16))
		args.color = color

	if(args.backgroundColor == "black"):
		args.backgroundColor = [0, 0, 0]
	elif(args.backgroundColor == "white"):
		args.backgroundColor = [255, 255, 255]
	elif(args.backgroundColor == "red"):
		args.backgroundColor = [255, 0, 0]
	elif(args.backgroundColor == "green"):
		args.backgroundColor = [0, 255, 0]
	elif(args.backgroundColor == "blue"):
		args.backgroundColor = [0, 0, 255]
	elif(args.backgroundColor == "yellow"):
		args.backgroundColor = [255, 255, 0]
	elif(args.backgroundColor == "cyan"):
		args.backgroundColor = [0, 255, 255]
	elif(args.backgroundColor == "magenta"):
		args.backgroundColor = [255, 0, 255]
	else:																# Converts HEX to RGB
		backgroundColor = []
		for i in (0, 2, 4):
			backgroundColor.append(int(args.backgroundColor[i:i+2], 16))
		args.backgroundColor = backgroundColor

	if(args.smoothT == "auto"):						# Smoothing over past/next <smoothT> frames (Smoothes bin over time). If smoothT=auto: Automatic smoothing is applied (framerate/15). Default: 0
		args.smoothT = int(args.framerate/15)
	else:
		args.smoothT = int(args.smoothT)

	if(args.smoothY == "auto"):						# Smoothing over past/next <smoothY> bins (Smoothes bin with adjacent bins). If smoothY=auto: Automatic smoothing is applied (bins/32). Default: 0
		args.smoothY = int(args.bins/32)
	else:
		args.smoothY = int(args.smoothY)

	if(args.start == 0 or args.test == 1):			# Begins render at <start> seconds. If start=-1: Renders from the start of the sound file. Default: -1
		args.start = 0
	else:
		args.start = float(args.start)

	if(args.end == -1 or args.test == 1):			# Ends render at <end> seconds. If end=-1: Renders to the end of the sound file. Default: -1
		args.end = len(fileData)/samplerate
	else:
		args.end = float(args.end)

	if(args.frequencyStart == 0):					# Limits the range of frequencies to <frequencyStart>Hz and onward. If frequencyStart=-1: Starts at 0Hz. Default: -1
		args.frequencyStart = 0
	else:
		args.frequencyStart = float(args.frequencyStart)

	if(args.frequencyEnd == -1):					# Limits the range of frequencies to <frequencyEnd>Hz. If frequencyEnd=-1: Ends at highest frequency. Default: -1
		args.frequencyEnd = samplerate/2
	else:
		args.frequencyEnd = float(args.frequencyEnd)

	if(args.chunkSize == -1):
		args.chunkSize = int(DEFAULT_CHUNKSIZE/cpu_count())


"""
Processes data from <FILENAME> and assigns data to its respective frame.
"""
def calculateFrameData(fileData, samplerate):
	frameData = []
	frameCounter = 0

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
	stepSize = samplerate/args.framerate
	while (stepSize * frameCounter < len(fileData)):
		frameDataStart = int(stepSize * frameCounter)
		frameDataEnd = int(stepSize * (frameCounter + 1))

	# Fourier Transformation (Amplitudes)
		currentFrameData = fileData[int(frameDataStart):int(frameDataEnd)]
		frameDataAmplitudes = abs(np.fft.rfft(currentFrameData))

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
	div = np.log2(args.ylog + 1)						# Constant for y-scaling
	numChunks = int(np.ceil(len(bins)/args.chunkSize))	# Total number of chunks

	# Create destination folder
	if(path.exists(args.destination) == False):
		mkdir(args.destination)

	frameCounter = Manager().dict()
	frameCounter['c'] = 0
	Parallel(n_jobs=args.cores)(delayed(renderSaveChunk)(bins, j, frameCounter, div) for j in range(numChunks))

	printProgressBar(len(bins), len(bins))
	print()												# New line after progress bar

"""
Renders and exports one chunk worth of frames
"""
def renderSaveChunk(bins, chunkCounter, frameCounter, div):
	start = chunkCounter*args.chunkSize
	end = (chunkCounter+1)*args.chunkSize
	if(end > len(bins)):
		end = len(bins)

	frames = renderChunkFrames(bins, start, end, div)
	saveChunkImages(frames, start, len(bins), frameCounter)

"""
Renders one chunk of frames
"""
def renderChunkFrames(bins, start, end, div):
	frames = []
	for j in range(start, end):
		frame = np.full((args.height, int(args.bins*(args.bin_width+args.bin_spacing)), 3), args.backgroundColor)
		frame = frame.astype(np.uint8)					# Set datatype to uint8 to reduce RAM usage
		for k in range(args.bins):
			if(args.ylog == 0):
				binHeight = np.ceil(bins[j, k] * frame.shape[0])
			else:
				binHeight = np.ceil(np.log2(args.ylog * bins[j, k] + 1)/div * frame.shape[0])
			frame[int(0):int(binHeight),
				int(k*args.bin_width + k*args.bin_spacing):int((k+1)*args.bin_width + k*args.bin_spacing)] = args.color
		frame = np.flipud(frame)
		frames.append(frame)
	return frames

"""
Exports one chunk of frames as a .png image sequence into it.
"""
def saveChunkImages(frames, start, length, frameCounter):
	# Save image sequence
	for i in range(len(frames)):
		plt.imsave(str(args.destination) + "/" + str(start + i) + ".png", frames[i], vmin=0, vmax=255, cmap='gray')
		frameCounter['c'] += 1
		printProgressBar(frameCounter['c'], length)

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
	fileData, samplerate = loadAudio()
	processArgs(fileData, samplerate)

	testData = np.load("testData.npy")
	args.start = 0
	args.end = 1/args.framerate

	frameData = calculateFrameData(testData, 44100)
	bins = createBins(frameData)
	testFrame = renderSaveFrames(bins)
	plt.imsave("testFrame.png", testFrame, vmin=0, vmax=255, cmap='gray')
	print("Created Frame for Style Testing in current directory.")


"""
Creates a video from an image sequence.
"""
def createVideo():
	flags = '-hide_banner -loglevel error '
	flags += '-r {} '.format(str(args.framerate))
	flags += '-i "{}/%0d.png" '.format(str(args.destination))
	if(args.videoAudio):
		print("Converting image sequence to video (with audio).")
		if(args.start != 0):
			flags += '-ss {} '.format(str(args.start))
		flags += '-i "{}" '.format(str(args.filename))
		if(args.end != -1):
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
	processArgs(fileData, samplerate)
	print("Audio succesfully loaded. (1/4)")

	frameData = calculateFrameData(fileData, samplerate)
	if(args.smoothT > 0):
		frameData = smoothFrameData(frameData)
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
		createVideo()
		processTime = time() - startTime
		print("Succesfully converted image sequence to video in " + str(format(processTime, ".3f")) + " seconds.")

	print("Finished!")

if __name__ == '__main__':
	if(args.test):
		testRender()
	else:
		full()
