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

	parser.add_argument("-d", "--duration", type=float, default="-1",
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

	# parser.add_argument("-t", "--test", action='store_true', default=False,
	# 					help="Renders only a single frame for style testing. Default: False")

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

	if(args.processes == 0 or args.processes < -1):
		exit("Number of processes must be at least 1")

	# Process optional arguments:
	if(args.disableSmoothing):
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

	args.color = hex2rgb(args.color)									# Color of bins

	args.backgroundColor = hex2rgb(args.backgroundColor)				# Color of the background

	if(args.duration == -1):
		args.duration = 1000/args.framerate			# Length of audio input per frame in ms. If duration=-1: Duration will be one frame long (1/framerate). Default: -1

	if(args.smoothY == "auto"):						# Smoothing over past/next <smoothY> bins (Smoothes bin with adjacent bins). If smoothY=auto: Automatic smoothing is applied (bins/32). Default: 0
		args.smoothY = int(args.bins/32)
	else:
		args.smoothY = int(args.smoothY)

	if(args.start == 0):							# Begins render at <start> seconds. If start=-1: Renders from the start of the sound file. Default: -1
		args.start = 0
	else:
		args.start = float(args.start)

	if(args.end == -1):								# Ends render at <end> seconds. If end=-1: Renders to the end of the sound file. Default: -1
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


"""
Converts HEX string or color name into RGB.
"""
def hex2rgb(hex):
	# No color
	if(hex == "black"):
		return [0, 0, 0]
	elif(hex == "white"):
		return [255, 255, 255]

	# Red
	elif(hex == "indianRed"):
		return [205, 92, 92]
	elif(hex == "lightCoral"):
		return [240, 128, 128]
	elif(hex == "salmon"):
		return [250, 128, 114]
	elif(hex == "darkSalmon"):
		return [233, 150, 122]
	elif(hex == "lightSalmon"):
		return [255, 160, 122]
	elif(hex == "crimson"):
		return [220, 20, 60]
	elif(hex == "red"):
		return [255, 0, 0]
	elif(hex == "fireBrick"):
		return [178, 34, 34]
	elif(hex == "darkRed"):
		return [139, 0, 0]

	# Pink
	elif(hex == "pink"):
		return [255, 192, 203]
	elif(hex == "lightPink"):
		return [255, 182, 193]
	elif(hex == "hotPink"):
		return [255, 105, 180]
	elif(hex == "deepPink"):
		return [255, 20, 147]
	elif(hex == "mediumVioletRed"):
		return [199, 21, 133]
	elif(hex == "paleVioletRed"):
		return [219, 112, 147]

	# Orange
	elif(hex == "coral"):
		return [255, 127, 80]
	elif(hex == "tomato"):
		return [255, 99, 71]
	elif(hex == "orangeRed"):
		return [255, 69, 0]
	elif(hex == "darkOrange"):
		return [255, 140, 0]
	elif(hex == "orange"):
		return [255, 165, 0]

	# Yellow
	elif(hex == "gold"):
		return [255, 215, 0]
	elif(hex == "yellow"):
		return [255, 255, 0]
	elif(hex == "lightYellow"):
		return [255, 255, 224]
	elif(hex == "lemonChiffon"):
		return [255, 250, 205]
	elif(hex == "lightGoldenrodYellow"):
		return [250, 250, 210]
	elif(hex == "papayaWhip"):
		return [255, 239, 213]
	elif(hex == "moccasin"):
		return [255, 228, 181]
	elif(hex == "peachPuff"):
		return [255, 218, 185]
	elif(hex == "paleGoldenrod"):
		return [238, 232, 170]
	elif(hex == "khaki"):
		return [240, 230, 140]
	elif(hex == "darkKhaki"):
		return [189, 183, 107]

	# Purple
	elif(hex == "lavnder"):
		return [230, 230, 250]
	elif(hex == "thistle"):
		return [216, 191, 216]
	elif(hex == "plum"):
		return [221, 160, 221]
	elif(hex == "viplet"):
		return [238, 130, 238]
	elif(hex == "orchid"):
		return [218, 112, 214]
	elif(hex == "magenta" or hex == "fuchsia"):
		return [255, 0, 255]
	elif(hex == "mediumOrchid"):
		return [186, 85, 211]
	elif(hex == "mediumPurple"):
		return [147, 112, 219]
	elif(hex == "rebeccaPurple"):
		return [102, 51, 153]
	elif(hex == "blueViolet"):
		return [138, 43, 226]
	elif(hex == "darkViolet"):
		return [148, 0, 211]
	elif(hex == "darkOrchid"):
		return [153, 50, 204]
	elif(hex == "darkMagenta"):
		return [139, 0, 139]
	elif(hex == "purple"):
		return [128, 0, 128]
	elif(hex == "indigo"):
		return [75, 0, 130]
	elif(hex == "slateBlue"):
		return [106, 90, 205]
	elif(hex == "darkSlateBlue"):
		return [72, 61, 139]
	elif(hex == "mediumSlateBlue"):
		return [123, 104, 238]

	# Green
	elif(hex == "greenYellow"):
		return [173, 255, 47]
	elif(hex == "chartreuse"):
		return [127, 255, 0]
	elif(hex == "lawnGreen"):
		return [124, 252, 0]
	elif(hex == "lime"):
		return [0, 255, 0]
	elif(hex == "limeGreen"):
		return [50, 205, 50]
	elif(hex == "paleGreen"):
		return [152, 251, 152]
	elif(hex == "lightGreen"):
		return [144, 238, 144]
	elif(hex == "mediumSpringGreen"):
		return [0, 250, 154]
	elif(hex == "springGreen"):
		return [0, 255, 127]
	elif(hex == "mediumSeaGreen"):
		return [60, 179, 113]
	elif(hex == "seaGreen"):
		return [46, 139, 87]
	elif(hex == "forestGreen"):
		return [34, 139, 34]
	elif(hex == "green"):
		return [0, 128, 0]
	elif(hex == "darkGreen"):
		return [0, 100, 0]
	elif(hex == "yellowGreen"):
		return [154, 205, 50]
	elif(hex == "oliveDrab"):
		return [107, 142, 35]
	elif(hex == "olive"):
		return [128, 128, 0]
	elif(hex == "darkOliveGreen"):
		return [85, 107, 47]
	elif(hex == "mediumAquamarine"):
		return [102, 205, 170]
	elif(hex == "darkSeaGreen"):
		return [143, 188, 139]
	elif(hex == "lightSeaGreen"):
		return [32, 178, 170]
	elif(hex == "darkCyan"):
		return [0, 139, 139]
	elif(hex == "teal"):
		return [0, 128, 128]
	
	
	# Blue
	elif(hex == "cyan" or hex == "aqua"):
		return [0, 255, 255]
	elif(hex == "lightCyan"):
		return [224, 255, 255]
	elif(hex == "paleTurqouoise"):
		return [175, 238, 238]
	elif(hex == "aquamarine"):
		return [127, 255, 212]
	elif(hex == "turquoise"):
		return [64, 224, 208]
	elif(hex == "mediumTurqouoise"):
		return [72, 209, 204]
	elif(hex == "darkTurqouoise"):
		return [0, 206, 209]
	elif(hex == "cadetBlue"):
		return [95, 158, 160]
	elif(hex == "steelBlue"):
		return [70, 130, 180]
	elif(hex == "lightSteelBlue"):
		return [176, 196, 222]
	elif(hex == "powderBlue"):
		return [176, 224, 230]
	elif(hex == "lightBlue"):
		return [173, 216, 230]
	elif(hex == "skyBlue"):
		return [135, 206, 235]
	elif(hex == "lightSkyBlue"):
		return [135, 206, 250]
	elif(hex == "deepSkyBlue"):
		return [0, 191, 255]
	elif(hex == "dodgerBlue"):
		return [30, 144, 255]
	elif(hex == "cornflowerBlue"):
		return [100, 149, 237]
	elif(hex == "royaleBlue"):
		return [65, 105, 225]
	elif(hex == "blue"):
		return [0, 0, 255]
	elif(hex == "mediumBlue"):
		return [0, 0, 205]
	elif(hex == "darkBlue"):
		return [0, 0, 139]
	elif(hex == "navy"):
		return [0, 0, 128]
	elif(hex == "midnightBlue"):
		return [25, 25, 112]

	# Brown
	elif(hex == "cornsilk"):
		return [255, 248, 220]
	elif(hex == "blanchedAlmond"):
		return [255, 235, 205]
	elif(hex == "bisque"):
		return [255, 228, 196]
	elif(hex == "navojoWhite"):
		return [255, 222, 173]
	elif(hex == "wheat"):
		return [245, 222, 179]
	elif(hex == "burlyWood"):
		return [222, 184, 135]
	elif(hex == "tan"):
		return [210, 180, 140]
	elif(hex == "rosyBrown"):
		return [188, 143, 143]
	elif(hex == "sandyBrown"):
		return [244, 164, 96]
	elif(hex == "goldenrod"):
		return [218, 165, 32]
	elif(hex == "darkGoldenrod"):
		return [184, 134, 11]
	elif(hex == "peru"):
		return [205, 133, 63]
	elif(hex == "chocolate"):
		return [210, 105, 30]
	elif(hex == "saddleBrown"):
		return [139, 69, 19]
	elif(hex == "sienna"):
		return [160, 82, 45]
	elif(hex == "brown"):
		return [165, 42, 42]
	elif(hex == "maroon"):
		return [128, 0, 0]

	# White
	elif(hex == "snow"):
		return [255, 250, 250]
	elif(hex == "honeyDew"):
		return [240, 255, 240]
	elif(hex == "mintCream"):
		return [245, 255, 250]
	elif(hex == "azure"):
		return [240, 255, 255]
	elif(hex == "aliceBlue"):
		return [240, 248, 255]
	elif(hex == "ghostWhite"):
		return [248, 248, 255]
	elif(hex == "whiteSmoke"):
		return [245, 245, 245]
	elif(hex == "seaShell"):
		return [255, 245, 238]
	elif(hex == "beige"):
		return [245, 245, 220]
	elif(hex == "oldLace"):
		return [253, 245, 230]
	elif(hex == "floralWhite"):
		return [255, 250, 240]
	elif(hex == "ivory"):
		return [255, 255, 240]
	elif(hex == "antiqueWhite"):
		return [250, 235, 215]
	elif(hex == "linen"):
		return [250, 240, 230]
	elif(hex == "lavenderBlush"):
		return [255, 240, 245]
	elif(hex == "mystyRose"):
		return [255, 228, 225]

	# Gray
	elif(hex == "gainsboro"):
		return [220, 220, 220]
	elif(hex == "lightGray"):
		return [211, 211, 211]
	elif(hex == "silver"):
		return [192, 192, 192]
	elif(hex == "darkGray"):
		return [169, 169, 169]
	elif(hex == "gray"):
		return [128, 128, 128]
	elif(hex == "dimGray"):
		return [105, 105, 105]
	elif(hex == "lightSlateGray"):
		return [119, 136, 153]
	elif(hex == "slateGray"):
		return [112, 128, 144]
	elif(hex == "darkSlateGray"):
		return [47, 79, 79]

	# Converts HEX to RGB
	else:
		color = []
		for i in (0, 2, 4):
			color.append(int(hex[i:i+2], 16))
		return color