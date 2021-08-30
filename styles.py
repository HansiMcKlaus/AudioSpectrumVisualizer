# from arguments import args						# Does not work for some reason
import numpy as np
# import scikit-image
from skimage.draw import disk

def renderFrame(args, bins, j):
	frame = np.full((args.height, int(args.bins*(args.bin_width+args.bin_spacing)), 3), args.backgroundColor)
	frame = frame.astype(np.uint8)					# Set datatype to uint8 to reduce RAM usage

	if(args.style == "bars"):
		for k in range(args.bins):
			frame[int(0):int(np.ceil(bins[j,k]*args.height)),
			int(k*args.bin_width + k*args.bin_spacing):int((k+1)*args.bin_width + k*args.bin_spacing)] = args.color
		frame = np.flipud(frame)
		return frame

	if(args.style == "points"):
		point = renderPoint(args)
		binSpace = args.height - point.shape[0]
		for k in range(args.bins):
			binStart = int(k*args.bin_width + k*args.bin_spacing)
			offset = int(args.bin_width - point.shape[1])

			frame[int(np.ceil(bins[j,k]*binSpace)):int(np.ceil(bins[j,k]*binSpace + point.shape[0])),
			binStart + offset:binStart + point.shape[1] + offset] = point
		frame = np.flipud(frame)
		return frame

def renderPoint(args):
	if(args.pointStyle == "block"):
		point = np.full((int(args.pointWidth), int(args.pointWidth), 3), args.color)
		return point
	elif(args.pointStyle == "slab"):
		point = np.full((int(args.pointWidth/2), int(args.pointWidth), 3), args.color)
		return point
	elif(args.pointStyle == "circle"):
		point = np.full((int(args.pointWidth), int(args.pointWidth), 3), args.backgroundColor)
		rr, cc = disk((int(args.pointWidth/2), int(args.pointWidth/2)), int(args.pointWidth/2))
		point[rr, cc, :] = args.color
		return point
	elif(args.pointStyle == "donut"):
		point = np.full((int(args.pointWidth), int(args.pointWidth), 3), args.backgroundColor)
		rr, cc = disk((int(args.pointWidth/2), int(args.pointWidth/2)), int(args.pointWidth/2))
		point[rr, cc, :] = args.color
		rr, cc = disk((int(args.pointWidth/2), int(args.pointWidth/2)), int(args.pointWidth/2 * 0.5))
		point[rr, cc, :] = args.backgroundColor
		return point