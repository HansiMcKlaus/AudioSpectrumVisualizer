from color import hex2rgb							# Handles colors

import argparse
import sys
import os
from joblib import cpu_count

args = None
DEFAULT_CHUNKSIZE = 128

"""
Instantiates the argument parser and sets arguments.
Returns arguments.
"""
def initArgs():

	# Instantiate the parser
	parser = argparse.ArgumentParser(description="Creates a customizable video for the spectrum of an audio file.")

	# Required positional arguments
	parser.add_argument("filename", type=str,
						help="Name or path of the audio file")
	parser.add_argument("destination", type=str, nargs='?', default="output",
						help="Path to file to which output video is to be saved, or to directory under which the image sequence is to be saved. Default: output")

	# Optional arguments - General
	parser.add_argument("-ps", "--preset", type=str, default="default",
						help="Name of a preset defined as a collection of flags in presets.txt. Default: default")

	parser.add_argument("-ht", "--height", type=int, default=540,
						help="Height of the output video/images in px. Default: 540")

	parser.add_argument("-w", "--width", type=int, default=1920,
						help="Width of the output video/images in px. Will be overwritten if both binWidth AND binSpacing is given! Default: 1920")

	parser.add_argument("-b", "--bins", type=int, default=64,
						help="Amount of bins (bars, points, etc). Default: 64")

	parser.add_argument("-bw", "--binWidth", type=float, default=-1,
						help="Width of the bins in px. Default: 5/6 * width/bins")

	parser.add_argument("-bs", "--binSpacing", type=float, default=-1,
						help="Spacing between bins in px. Default: 1/6 * width/bins")

	parser.add_argument("-fr", "--framerate", type=float, default=30,
						help="Framerate of the output video/image sequence (Frames per second). Default: 30")

	parser.add_argument("-ch", "--channel", type=str, default="average",
						help="Which channel to use (left, right, average, stereo). Default: average")

	parser.add_argument("-d", "--duration", type=float, default=-1,
						help="Length of audio input per frame in ms. Default: Duration will be one frame long (1/framerate)")

	parser.add_argument("-s", "--start", type=float, default=0,
						help="Begins render at <start> seconds. Default: Renders from the start of the sound file")

	parser.add_argument("-e", "--end", type=float, default=-1,
						help="Ends render at <end> seconds. Default: Renders to the end of the sound file")

	parser.add_argument("-xlog", type=float, default=0,
						help="Scales the X-axis logarithmically to a given base. Default: 0 (linear)")

	parser.add_argument("-ylog", type=float, default=0,
						help="Scales the Y-axis logarithmically to a given base. Default: 0 (linear)")

	parser.add_argument("-sy", "--smoothY", type=str, default="0",
						help="Smoothing over <n> adjacent bins. If smoothY=auto: Automatic smoothing is applied (bins/32). Default: 0")

	parser.add_argument("-fs", "--frequencyStart", type=float, default=0,
						help="Limits the range of frequencies to <frequencyStart>Hz and onward. Default: Starts at lowest frequency")

	parser.add_argument("-fe", "--frequencyEnd", type=float, default=-1,
						help="Limits the range of frequencies to <frequencyEnd>Hz. Default: Ends at highest frequency")

	parser.add_argument("-is", "--imageSequence", action='store_true', default=False,
						help="Export visualization as frame-by-frame image sequence instead of video with audio. Default: False")

	# Optional arguments - Style
	parser.add_argument("-t", "--test", action='store_true', default=False,
						help="Renders only a single frame for style testing. Default: False")

	parser.add_argument("-st", "--style", type=str, default="bars",
						help="Defines render style: bars, circles, donuts, line, fill. Default: bars")

	parser.add_argument("-bht", "--barHeight", type=float, default=-1,
						help="Height of the bars in px. Default: full")

	parser.add_argument("-lt", "--lineThickness", type=float, default=1,
					help="Thickness of the line in px. Default: 1")
	
	parser.add_argument("-m", "--mirror", type=int, default=0,
					help="Mirrors the spectrum at x-axis. 1: middle, 2: top/bottom Default: 0")

	parser.add_argument("-r", "--radial", action='store_true', default=False,
						help="Creates a radial (circle) visualization. Size is determined by height. Default: False")

	parser.add_argument("-rs", "--radiusStart", type=float, default=-1,
					help="Radius from where to start. Default: Quarter of Height")

	parser.add_argument("-re", "--radiusEnd", type=float, default=-1,
					help="Radius to where to end. Default: Half of Height")

	parser.add_argument("-c", "--color", type=str, default="ffffff",
						help="Color of bins (bars, points, etc). Ex: ff0000 or red. Default: ffffff (white)")

	parser.add_argument("-bgc", "--backgroundColor", type=str, default="000000",
						help="Color of the background. Ex: ff0000 or red. Default: 000000 (black)")

	# Optional arguments - Performance
	parser.add_argument("-cs", "--chunkSize", type=int, default=-1,
						help="Amount of frames cached before clearing (Higher chunk size lowers render time, but increases RAM usage). Default: 128")

	parser.add_argument("-p", "--processes", type=int, default=-1,
						help="Number of processes to use for rendering and export. Default: Number of processor cores (or hyperthreads, if applicable)")


	# Parse arguments once to get preset flag
	args = parser.parse_args()

	userArgs = sys.argv
	presetArgs = parsePreset(userArgs[0], args.preset)
	sys.argv = userArgs[0:1]
	sys.argv.extend(presetArgs)
	sys.argv.extend(userArgs[1:])

	# Parse arguments a second time after appending flags specified by preset
	args = parser.parse_args()

	return args

def parsePreset(scriptDirectory, argPreset):
	pathToPresets = changePath(scriptDirectory, "presets.txt")
	presetsFile = open(pathToPresets)
	lines = presetsFile.readlines()
	presetsFile.close()

	presets = []
	for line in lines:
		preset = line.split()[0]
		presets.append(preset)

	if argPreset in presets:
		lineNum = presets.index(argPreset)
		return lines[lineNum].split()[1:]
	else:
		exit("Preset doesn't exist.")

def changePath(pathToExec, filename):
	path = os.path.split(pathToExec)[0]
	path = os.path.join(path, filename)
	return path

"""
Exits on invalid inputs and processes arguments that can not be calculated independently.
"""
def processArgs(args, fileData, samplerate):
	# Exit on invalid input
	if args.bins <= 0:
		exit("Must have at least one bin.")

	if args.height <= 0:
		exit("Height must be at least 1px.")

	if args.width <= 0:
		exit("Width must be at least 1px.")

	if args.framerate <= 0:
		exit("Framerate must be at least 1.")

	if args.channel not in ["left", "right", "average", "stereo"]:
		exit("Invalid channel. Valid channels: left, right, average, stereo.")

	if len(fileData.shape) == 1 and args.channel == "stereo":
		exit("Audio only has a single channel. Valid channels: left, right, average.")

	if args.style not in ["bars", "circles", "donuts", "line", "fill"]:
		exit("Style not recognized. Available styles: bars, circles, donuts, line, fill.")

	if args.barHeight < 1 and args.barHeight != -1:
		exit("Bar height must be at least 1px.")

	if args.barHeight > args.height:
		exit("Bar height must not exceed image height of " + str(args.height) + "px.")

	if args.lineThickness < 1:
		exit("Line thickness must be at least 1px.")

	if args.mirror < 0 or args.mirror > 2:
		exit("Mirror argument only accepts 0 (off), 1 (middle), 2 (top/bottom).")

	if args.xlog < 0:
		exit("Scalar for xlog must not be smaller than 0.")

	if args.ylog < 0:
		exit("Scalar for ylog must not be smaller than 0.")

	if args.binWidth != -1:
		if args.binWidth < 1:
			exit("Bin width must be at least 1px.")

	if args.binSpacing != -1:
		if args.binSpacing < 0:
			exit("Bin spacing must be 0px or higher")

	if args.duration != -1 and not args.test:
		if args.duration <= 0:
			exit("Duration must be longer than 0ms.")

	if args.duration != -1 and not args.test:
		if args.duration > len(fileData)/samplerate:
			exit("Duration must not be longer than audio length of " + str(format(len(fileData)/samplerate, ".3f")) + "s.")

	if args.smoothY != "auto" :
		if int(args.smoothY) < 0:
			exit("Smoothing scalar for smoothing in frame must be 0 or higher.")

	if args.start != 0:
		if args.start < 0:
			exit("Start time must be 0 or later.")

	if args.end != -1:
		if args.end <= 0:
			exit("End time must be later than 0.")

	if args.start != 0:
		if args.start >= len(fileData)/samplerate:
			exit("Start time exceeds audio length of " + str(format(len(fileData)/samplerate, ".3f")) + "s.")

	if args.end != -1 and not args.test:
		if args.end > len(fileData)/samplerate:
			exit("End time exceeds audio length of " + str(format(len(fileData)/samplerate, ".3f")) + "s.")

	if args.start != 0 and args.end != -1:
		if args.start >= args.end:
			exit("Start time must predate end time.")

	if args.frequencyStart != 0:
		if args.frequencyStart < 0:
			exit("Frequency start must be 0 or higher.")

	if args.frequencyEnd != -1:
		if args.frequencyEnd <= 0:
			exit("Frequency end must be higher than 0.")

	if args.frequencyStart != 0:
		if args.frequencyStart >= samplerate/2:
			exit("Frequency start exceeds max frequency of " + str(int(samplerate/2)) + "Hz.")

	if args.frequencyEnd != -1:
		if args.frequencyEnd > samplerate/2:
			exit("Frequency end exceeds max frequency of " + str(int(samplerate/2)) + "Hz.")

	if args.frequencyStart != 0 and args.frequencyEnd != -1:
		if args.frequencyStart >= args.frequencyEnd:
			exit("Frequency start must be lower than frequency end.")

	if args.radiusStart != -1:
		if args.radiusStart < 0:
			exit("Start radius must must not be smaller than 0px.")

	if args.radiusEnd != -1:
		if args.radiusEnd <= 0:
			exit("End radius must be bigger than 0px.")

	if args.radiusStart != -1:
		if args.radiusStart >= args.height/2:
			exit("Start radius exceeds max radius of " + str(int(args.height/2)) + "px.")

	if args.radiusEnd != -1:
		if args.radiusEnd > args.height/2:
			exit("End radius exceeds max radius of " + str(int(args.height/2)) + "px.")

	if args.radiusStart != -1 and args.radiusEnd != -1:
		if args.radiusStart >= args.radiusEnd:
			exit("Start radius must be smaller than end radius.")

	if args.chunkSize == 0 or args.chunkSize < -1:
		exit("Chunk size must be at least 1.")

	if args.processes == 0 or args.processes < -1:
		exit("Number of processes must be at least 1")

	# Process optional arguments:
	if args.test:
		args.framerate = 30												# Forces framerate when style testing
		args.duration = -1
		args.processes = 1												# Makes the style-testing code easier to fit
		args.imageSequence = True										# Forces no video when style testing

	if args.binWidth == -1 and args.binSpacing != -1:					# Only binSpacing is given
		args.binWidth = args.width/args.bins - args.binSpacing
		args.binSpacing = args.binSpacing
	elif args.binWidth != -1 and args.binSpacing == -1:					# Only binWidth is given
		args.binWidth = args.binWidth
		args.binSpacing = args.width/args.bins - args.binWidth
	elif args.binWidth == -1 and args.binSpacing == -1:					# Neither is given
		args.binWidth = args.width/args.bins * (5/6)
		args.binSpacing = args.width/args.bins * (1/6)
	else:																# Both are given (Overwrites width)
		args.width = int((args.binWidth + args.binSpacing) * args.bins)

	args.color = hex2rgb(args.color)									# Color of bins

	args.backgroundColor = hex2rgb(args.backgroundColor)				# Color of the background

	if args.color == args.backgroundColor:
		print("Bro, what?")

	if args.channel == "stereo" and args.mirror == 0:
		args.mirror = 1

	if args.duration == -1:
		args.duration = 1000/args.framerate			# Length of audio input per frame in ms. If duration=-1: Duration will be one frame long (1/framerate). Default: -1

	if args.smoothY == "auto":						# Smoothing over past/next <smoothY> bins (Smooths bin with adjacent bins). If smoothY=auto: Automatic smoothing is applied (bins/32). Default: 0
		args.smoothY = int(args.bins/32)
	else:
		args.smoothY = int(args.smoothY)

	if args.start == 0 or args.test == 1:			# Begins render at <start> seconds. If start=-1: Renders from the start of the sound file. Default: -1
		args.start = 0
	else:
		args.start = args.start

	if args.end == -1 or args.test == 1:			# Ends render at <end> seconds. If end=-1: Renders to the end of the sound file. Default: -1
		args.end = len(fileData)/samplerate
	else:
		args.end = args.end

	if args.frequencyStart == 0:					# Limits the range of frequencies to <frequencyStart>Hz and onward. If frequencyStart=-1: Starts at 0Hz. Default: -1
		args.frequencyStart = 0
	else:
		args.frequencyStart = args.frequencyStart

	if args.frequencyEnd == -1:						# Limits the range of frequencies to <frequencyEnd>Hz. If frequencyEnd=-1: Ends at highest frequency. Default: -1
		args.frequencyEnd = samplerate/2
	else:
		args.frequencyEnd = args.frequencyEnd

	if args.radiusStart == -1:
		args.radiusStart = args.height/6

	if args.radiusEnd == -1:
		args.radiusEnd = args.height/2

	if args.processes == -1:
		args.processes = cpu_count()

	if args.chunkSize == -1:
		args.chunkSize = int(DEFAULT_CHUNKSIZE/args.processes)

	if not args.imageSequence:			# cv2 uses BGR instead of RGB and there is no setting in the videowriter to fix that
		args.color.reverse()			# so we have to convert the colors ourselves as long as we don't export images
		args.backgroundColor.reverse()
