# from arguments import args
import numpy as np

def renderFrame(args, bins, j):
	frame = np.full((args.height, int(args.bins*(args.bin_width+args.bin_spacing)), 3), args.backgroundColor)
	frame = frame.astype(np.uint8)					# Set datatype to uint8 to reduce RAM usage

	if(args.style == "bars"):
		for k in range(args.bins):
			frame[int(0):int(np.ceil(bins[j,k]*args.height)),
			int(k*args.bin_width + k*args.bin_spacing):int((k+1)*args.bin_width + k*args.bin_spacing)] = args.color
		frame = np.flipud(frame)
		return frame