# -*- coding: utf-8 -*-
"""
@author: HansiMcKlaus

Creates an Image Sequence for the Spectrum of an Audio File.

Dependencies: numpy, audio2numpy, matplotlib, ffmpeg
"""

"""
TODO: Implement mp4 export with audio (-va)
TODO: Implement different styles
		Styles:
			Bar: Filled, Blocks, Centered on y-axis
			Points: Shapes
			Line: Thicknes
			Filled
TODO: Implement color
TODO: Make the x-axis scaling actually logarithmic
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
parser.add_argument("destination", type=str, nargs='?', default="Image Sequence",
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

parser.add_argument("-xlog", type=float, default=1,
					help="Scales the X-axis logarithmically to a given base. Default: 1 (Linear Scaling)")

parser.add_argument("-st", "--smoothT", type=str, default="0",
					help="Smoothing over past/next <smoothT> frames (Smoothes bin over time). If smoothT=auto: Automatic smoothing is applied (framerate/15). Default: 0")

parser.add_argument("-sy", "--smoothY", type=str, default="0",
					help="Smoothing over past/next <smoothY> bins (Smoothes bin with adjacent bins). If smoothY=auto: Automatic smoothing is applied (bins/32). Default: 0")

parser.add_argument("-s", "--start", type=str, default="False",
					help="Begins render at <start> seconds. If start=False: Renders from the start of the sound file. Default: False")

parser.add_argument("-e", "--end", type=str, default="False",
					help="Ends render at <end> seconds. If end=False: Renders to the end of the sound file. Default: False")

parser.add_argument("-fs", "--frequencyStart", type=str, default="False",
					help="Limits the range of frequencies to <frequencyStart>Hz and onward. If frequencyStart=False: Starts at 0Hz. Default: False")

parser.add_argument("-fe", "--frequencyEnd", type=str, default="False",
					help="Limits the range of frequencies to <frequencyEnd>Hz. If frequencyEnd=False: Ends at highest frequency. Default: False")

parser.add_argument("-t", "--test", action='store_true', default=False,
					help="Renders only a single frame for style testing. Default: False")

parser.add_argument("-v", "--video", action='store_true', default=False,
					help="Additionaly creates a video (.mp4) from image sequence. Default: False")

parser.add_argument("-va", "--videoAudio", action='store_true', default=False,
					help="Additionaly creates a video (.mp4) from image sequence and audio. Default: False")

parser.add_argument("-ds", "--disableSmoothing", action='store_true', default=False,
					help="Disables all smoothing (smoothT and smoothY). Default: False")

args = parser.parse_args()


# Disable options
if(args.disableSmoothing == True):
	args.smoothT = 0
	args.smoothY = 0


# Clean up bad input
while(args.bins <= 0):
	args.bins = int(input("Must have at least one bin. New amount of bins: "))

while(args.height <= 0):
	args.height = int(input("Height must be at least 1px. New height: "))

while(args.width <= 0):
	args.width = int(input("Width must be at least 1px. New width: "))

while(args.framerate <= 0):
	args.framerate = float(input("Framerate must be at least 1. New framerate: "))

while(args.xlog <= 0):
	args.xlog = float(input("Scalar must be bigger than 0. New Scalar: "))

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

if(args.end != "False"):
	while(float(args.end) <= 0):
		args.end = float(input("End time must be later than 0. New end time: "))

if(args.start != "False" and args.end != "False"):
	while(float(args.start) >= float(args.end)):
		args.start = float(input("Start time must predate end time. New start time: "))
		args.end = float(input("End time must postdate start time. New end time: "))

if(args.frequencyEnd != "False"):
	while(float(args.frequencyEnd) <= 0):
		args.frequencyEnd = float(input("Frequency end must be higher than 0. New end frequency: "))

if(args.frequencyStart != "False" and args.frequencyEnd != "False"):
	while(float(args.frequencyStart) >= float(args.frequencyEnd)):
		args.frequencyStart = float(input("Frequency start must be lower than frequency end. New start frequency: "))
		args.frequencyEnd = float(input("Frequency end must be higher than frequency start. New end frequency: "))


# Flags
TEST = args.test									# Renders only a single frame for style testing. Default: False
VIDEO = args.video									# Additionaly creates a video (.mp4) from image sequence. Default: False
VIDEOAUDIO = args.videoAudio						# Additionaly creates a video (.mp4) from image sequence and audio. Default: False

# Positional arguments:
FILENAME = args.filename							# Name or path of the audio file

#Optional positional arguments:
DESTINATION = args.destination						# Name or path of the created directory in which the image sequence is saved. Default: Image Sequence

# Optional arguments:
BINS = args.bins									# Amount of bins (Bars, Points, etc). Default: 64
HEIGHT = args.height								# Max height of the bins (height of the images). Default: 540px
WIDTH = args.width									# Width of the image. Default: 1920px
FRAMERATE = args.framerate							# Framerate of the image sequence (Frames per second). Default: 30fps
XLOG = args.xlog									# Scales the X-axis logarithmically to a given base. Default: 1 (Linear Scaling)

if(args.bin_width == "auto" and args.bin_spacing != "auto"):		# Only bin_spacing is given
	BIN_WIDTH = WIDTH/BINS - float(args.bin_spacing)
	BIN_SPACING = float(args.bin_spacing)
elif(args.bin_width != "auto" and args.bin_spacing == "auto"):		# Only bin_width is given
	BIN_WIDTH = float(args.bin_width)
	BIN_SPACING = WIDTH/BINS - float(args.bin_width)
elif(args.bin_width == "auto" and args.bin_spacing == "auto"):		# Neither is given
	BIN_WIDTH = WIDTH/BINS * (5/6)
	BIN_SPACING = WIDTH/BINS * (1/6)
else:																# Both are given (Overwrites width)
	BIN_WIDTH = float(args.bin_width)
	BIN_SPACING = float(args.bin_spacing)

if(args.smoothT == "auto"):							# Smoothing over past/next <smoothT> frames (Smoothes bin over time). If smoothT=auto: Automatic smoothing is applied (framerate/15). Default: 0
	SMOOTHT = int(FRAMERATE/15)
else:
	SMOOTHT = int(args.smoothT)

if(args.smoothY == "auto"):							# Smoothing over past/next <smoothY> bins (Smoothes bin with adjacent bins). If smoothY=auto: Automatic smoothing is applied (bins/32). Default: 0
	SMOOTHY = int(BINS/32)
else:
	SMOOTHY = int(args.smoothY)

if(args.start == "False" or TEST == 1):				# Begins render at <start> seconds. If start=False: Renders from the start of the sound file. Default: False
	START = 0
else:
	START = float(args.start)

if(args.end == "False" or TEST == 1):				# Ends render at <end> seconds. If end=False: Renders to the end of the sound file. Default: False
	END = "False"
else:
	END = float(args.end)

if(args.frequencyStart == "False"):					# Limits the range of frequencies to <frequencyStart>Hz and onward. If frequencyStart=False: Starts at 0Hz. Default: False
	FREQUENCY_START = 0
else:
	FREQUENCY_START = float(args.frequencyStart)

if(args.frequencyEnd == "False"):					# Limits the range of frequencies to <frequencyEnd>Hz. If frequencyEnd=False: Ends at highest frequency. Default: False
	FREQUENCY_END = "False"
else:
	FREQUENCY_END = float(args.frequencyEnd)


"""
Loads data and samplerate from <FILENAME>.
"""
def loadAudio():
	fileData, samplerate = open_audio(FILENAME)
	if(len(fileData.shape) == 2):					# Averages multiple channels into a mono channel
		fileData = np.mean(fileData, axis=1)
	return fileData, samplerate


"""
Assigns data from <FILENAME> to its respective frame.
Example: samplerate: 44100, FRAMERATE:30 --> First frame consists of the first 44100/30 = 1470 samples.
After Fourier Transformation: 1470/2 + 1 = 736 Samples
"""
def calculateFrameData(samplerate, fileData):
	frameData = []
	frameCounter = 0

	# Slices fileData to start and end point
	if(END == "False"):
		fileData = fileData[int(START*samplerate):]
	else:
		fileData = fileData[int(START*samplerate):int(END*samplerate)]

	# Splits Data into frames
	stepSize = samplerate/FRAMERATE
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
		if(FREQUENCY_END == "False"):
			frameDataAmplitudes = frameDataAmplitudes[int(FREQUENCY_START/samplerate*len(frameDataAmplitudes)):]
		else:
			frameDataAmplitudes = frameDataAmplitudes[int(FREQUENCY_START/samplerate*len(frameDataAmplitudes)):int(FREQUENCY_END/samplerate*len(frameDataAmplitudes))]

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
		if(i < SMOOTHT):							# First n frame data
			frameDataSmoothed.append(np.mean(frameData[:i+SMOOTHT+1], axis=0))
		elif(i >= len(frameData)-SMOOTHT):			# Last n frame data
			frameDataSmoothed.append(np.mean(frameData[i-SMOOTHT:], axis=0))
		else:										# Normal Case
			frameDataSmoothed.append(np.mean(frameData[i-SMOOTHT:i+SMOOTHT+1], axis=0))

	return frameDataSmoothed


"""
Creates the bins for every frame. A bin contains an amplitude that will later be represented as the height of a bar, point, line, etc. on the frame.
Example: 736 amplitudes over 64 bins --> Every bin contains the mean amplitude of 736/64 = 11.5 amplitudes per bin if set to linear (xlog = 1).
Example: 736 amplitudes over 1080 bins --> Every bin contains the mean amplitude of 736/1080 = ~0.68 amplitudes per bin --> Some adjacent bins contain the same amplitude.
"""
def createBins(frameData):
	bins = []
	for data in frameData:
		for i in range(BINS):
			dataStart = int(((i*len(data)/BINS)/len(data))**XLOG * len(data))
			dataEnd = int((((i+1)*len(data)/BINS)/len(data))**XLOG * len(data))

			if (dataEnd == dataStart):
				dataEnd += 1						# Ensures [dataStart:dataEnd] does not result NaN
			bins.append(np.mean(data[dataStart:dataEnd]))

	return bins


"""
Smoothes the bins in a frame (Over the past/next n frames).
"""
def smoothBinData(bins):
	binDataSmoothed = []
	for j in range(int(len(bins)/BINS)):
		currentBins = bins[j*BINS:(j+1)*BINS]
		for k in range(int(len(currentBins))):
			if(k < SMOOTHY):						# First n bins
				binDataSmoothed.append(np.mean(currentBins[:k+SMOOTHY+1]))
			elif(k >= len(currentBins)-SMOOTHY):	# Last n bins
				binDataSmoothed.append(np.mean(currentBins[k-SMOOTHY:]))
			else:									# Normal Case
				binDataSmoothed.append(np.mean(currentBins[k-SMOOTHY:k+SMOOTHY+1]))

	return binDataSmoothed


"""
Renders frames from bin data.
"""
def renderFrames(bins):
	bins = bins/np.max(bins)						# Normalize vector length to [0,1]
	frames = []
	for j in range(int(len(bins)/BINS)):
		frame = np.zeros((HEIGHT, int(BINS*(BIN_WIDTH+BIN_SPACING))))
		for k in range(BINS):
			frame[int(0):int(np.ceil(bins[j*BINS + k]*frame.shape[0])),
				int(k*BIN_WIDTH + k*BIN_SPACING):int((k+1)*BIN_WIDTH + k*BIN_SPACING)] = 1
		frame = np.flipud(frame)
		frames.append(frame)

	return frames

"""
Creates directory named <DESTINATION> and exports the frames as a .png image sequence into it.
Starts at "0.png" for first frame
"""
def saveImageSequence(frames):
	# Create destination folder
	if not path.exists(DESTINATION):
		mkdir(DESTINATION)
	
	frameCounter = 0
	for frame in frames:
		plt.imsave(str(DESTINATION) + "/" + str(frameCounter) + ".png", frame, cmap='gray')
		frameCounter += 1
		printProgressBar(frameCounter, len(frames))


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
	START = 0
	END = "False"

	frameData = calculateFrameData(44100, testData)
	bins = createBins(frameData)
	frames = renderFrames(bins)
	plt.imsave("testFrame.png", frames[0], cmap='gray')
	print("Created Frame for Style Testing in current directory.")


"""
Main method. Initializes the complete process from start to finish.
"""
def full():
	startTime = time()

	fileData, samplerate = loadAudio()
	print("Audio succesfully loaded. (1/4)")

	frameData = calculateFrameData(samplerate, fileData)
	print("Frame data created. (2/4)")

	if(SMOOTHT > 0):
		frameDataSmoothed = smoothFrameData(frameData)
		frameData = frameDataSmoothed

	bins = createBins(frameData)
	print("Bins created. (3/4)")

	if(SMOOTHY > 0):
		binDataSmoothed = smoothBinData(bins)
		bins = binDataSmoothed

	frames = renderFrames(bins)
	print("Frames created. (4/4)")

	print("Saving Image Sequence to: " + DESTINATION)
	saveImageSequence(frames)

	print()
	processTime = time() - startTime
	print("Created and saved Image Sequence in " + str(format(processTime, ".3f")) + " seconds.")

	if VIDEOAUDIO or VIDEO:
		flags = '-hide_banner -loglevel error '
		flags += '-r {} '.format(str(FRAMERATE))
		flags += '-i "{}/%0d.png" '.format(str(DESTINATION))
		if VIDEOAUDIO:
			print("Converting image sequence to video (with audio).")
			if(START != 0):
				flags += '-ss {} '.format(str(START))
			flags += '-i "{}" '.format(str(FILENAME))
			if(END != "False"):
				flags += '-t {} '.format(END - START)
		else:
			print("Converting image sequence to video.")

		flags += '-c:v libx264 -preset ultrafast -crf 16 -pix_fmt yuv420p -y "{}.mp4"'.format(str(DESTINATION))
		
		system('ffmpeg {}'.format(flags))
		
		processTime = time() - startTime
		print("Succesfully converted image sequence to video in " + str(format(processTime, ".3f")) + " seconds.")

	print("Finished!")

if (TEST == 1):
	testRender()
else:
	full()
