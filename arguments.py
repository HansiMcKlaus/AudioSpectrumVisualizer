from color import hex2rgb							# Handles colors

import argparse
from joblib import cpu_count

args = None
DEFAULT_CHUNKSIZE = 128

"""
Instantiates the argument parser and sets arguments.
Returns arguments.
"""
def initArgs():

	# Instantiate the parser
	parser = argparse.ArgumentParser(description="Creates an image sequence for the audio spectrum of an audio file.")

	# Required positional arguments
	parser.add_argument("filename", type=str,
						help="Name or path of the audio file")
	parser.add_argument("destination", type=str, nargs='?', default="imageSequence",
						help="Name or path of the created directory in which the image sequence is saved. Default: imageSequence")

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

	parser.add_argument("-st", "--style", type=str, default="bars",
						help="Defines render style: bars, points. Default: bars")

	parser.add_argument("-pst", "--pointStyle", type=str, default="circle",
						help="Defines point style: slab, block, circle. Default: circle")

	parser.add_argument("-pw", "--pointWidth", type=float, default=-1,
						help="Width of the points in px. Default: bin width")

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

	parser.add_argument("-d", "--duration", type=float, default=-1,
						help="Length of audio input per frame in ms. If duration=-1: Duration will be one frame long (1/framerate). Default: -1")

	parser.add_argument("-sy", "--smoothY", type=str, default="0",
						help="Smoothing over past/next <smoothY> bins (Smoothes bin with adjacent bins). If smoothY=auto: Automatic smoothing is applied (bins/32). Default: 0")

	parser.add_argument("-s", "--start", type=float, default=0,
						help="Begins render at <start> seconds. Default: 0")

	parser.add_argument("-e", "--end", type=float, default=-1,
						help="Ends render at <end> seconds. If end=-1: Renders to the end of the sound file. Default: -1")

	parser.add_argument("-fs", "--frequencyStart", type=float, default=0,
						help="Limits the range of frequencies to <frequencyStart>Hz and onward. Default: 0")

	parser.add_argument("-fe", "--frequencyEnd", type=float, default=-1,
						help="Limits the range of frequencies to <frequencyEnd>Hz. If frequencyEnd=-1: Ends at highest frequency. Default: -1")

	parser.add_argument("-cs", "--chunkSize", type=int, default=-1,
						help="Amount of frames cached before clearing (Higher chunk size lowers render time, but increases RAM usage). Default: 64")

	parser.add_argument("-p", "--processes", type=int, default=-1,
						help="Number of processes to use for rendering and export. Default: Number of processor cores (or hyperthreads, if supported)")

	parser.add_argument("-t", "--test", action='store_true', default=False,
						help="Renders only a single frame for style testing. Default: False")

	parser.add_argument("-v", "--video", action='store_true', default=False,
						help="Additionally creates a video (.mp4) from image sequence. Default: False")

	parser.add_argument("-va", "--videoAudio", action='store_true', default=False,
						help="Additionally creates a video (.mp4) from image sequence and audio. Default: False")

	parser.add_argument("-ds", "--disableSmoothing", action='store_true', default=False,
						help="Disables all smoothing (smoothT and smoothY). Default: False")

	args = parser.parse_args()

	return args


"""
Exits on invalid inputs and processes arguments that can not be calculated independently.
"""
def processArgs(args, fileData, samplerate):
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

	if(args.style != "bars" and args.style != "points"):
		exit("Style not recognized. Available styles: bars, points.")

	if(args.pointStyle != "slab" and args.pointStyle != "block" and args.pointStyle != "circle" and args.pointStyle != "donut"):
		exit("Point style not recognized. Available styles: bar, block, circle.")

	if(args.pointWidth < 1 and args.pointWidth != -1):
		exit("Point width must be at least 1px.")

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

	if(args.duration != -1):
		if(args.duration <= 0):
			exit("Duratio must be longer than 0ms.")

	if(args.duration != -1):
		if(float(args.duration) > len(fileData)/samplerate):
			exit("Duratio must not be longer than audio length of " + str(format(len(fileData)/samplerate, ".3f")) + "s.")

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

	if(args.end != -1 and not args.test):
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

	if(args.processes == 0 or args.processes < -1):
		exit("Number of processes must be at least 1")

	# Process optional arguments:
	if(args.disableSmoothing):
		args.smoothY = 0
	
	if(args.test):
		args.framerate = 30												# Forces framerate when style testing
		args.video = 0													# Forces no video when style testing
		args.videoAudio = 0

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

	if(args.pointWidth > args.bin_width):
		exit("Point width must not exceed bin width of " + str(args.bin_width) + "px.")

	if(args.pointWidth == -1):
		args.pointWidth = args.bin_width								# Point fills bin

	args.color = hex2rgb(args.color)									# Color of bins

	args.backgroundColor = hex2rgb(args.backgroundColor)				# Color of the background

	if(args.duration == -1):
		args.duration = 1000/args.framerate			# Length of audio input per frame in ms. If duration=-1: Duration will be one frame long (1/framerate). Default: -1

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

	if(args.processes == -1):
		args.processes = cpu_count()