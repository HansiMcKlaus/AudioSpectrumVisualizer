# from arguments import args						# Does not work for some reason
import numpy as np
from skimage.draw import disk, polygon

def renderFrame(args, bins, j):
	frame = np.full((args.height, int(args.bins*(args.binWidth+args.binSpacing)), 3), args.backgroundColor)
	frame = frame.astype(np.uint8)					# Set datatype to uint8 to reduce RAM usage

	if(args.style == "bars" and args.barHeight == -1):
		for k in range(args.bins):
			frame[int(0):int(np.ceil(bins[j,k]*args.height)),
			int(k*args.binWidth + k*args.binSpacing):int((k+1)*args.binWidth + k*args.binSpacing)] = args.color
		frame = np.flipud(frame)
		return frame

	if(args.style == "bars" and args.barHeight != -1 or args.style == "circles" or args.style == "donuts"):
		point = renderPoint(args)
		binSpace = args.height - point.shape[0]
		for k in range(args.bins):
			binStart = int(k*args.binWidth + k*args.binSpacing)
			offset = int(args.binWidth - point.shape[1])

			frame[int(np.ceil(bins[j,k]*binSpace)):int(np.ceil(bins[j,k]*binSpace + point.shape[0])),
			binStart + offset:binStart + point.shape[1] + offset] = point
		frame = np.flipud(frame)
		return frame

	if(args.style == "line"):
		binSpace = args.height - args.lineThickness
		for k in range(args.bins - 1):
			startY = int(np.ceil(bins[j,k]*binSpace))
			startX = int(k * (args.binWidth + args.binSpacing) + 0.5 * (args.binWidth + args.binSpacing))
			endY = int(np.ceil(bins[j,k+1]*binSpace))
			endX = int((k+1) * (args.binWidth + args.binSpacing) + 0.5 * (args.binWidth + args.binSpacing))
			line = np.array((
				(startY + args.lineThickness, startX),					# Up Left
				(startY, startX),										# Down Left
				(endY, endX),											# Down Right
				(endY + args.lineThickness, endX),						# Up Right
			))
			start, end = polygon(line[:, 0], line[:, 1], frame.shape)
			frame[start, end] = args.color
		frame = np.flipud(frame)
		return frame

	if(args.style == "fill"):
		for k in range(args.bins - 1):
			startY = int(np.ceil(bins[j,k]*args.height))
			startX = int(k * (args.binWidth + args.binSpacing) + 0.5 * (args.binWidth + args.binSpacing))
			endY = int(np.ceil(bins[j,k+1]*args.height))
			endX = int((k+1) * (args.binWidth + args.binSpacing) + 0.5 * (args.binWidth + args.binSpacing))
			line = np.array((
				(startY, startX),					# Up Left
				(0, startX),						# Down Left
				(0, endX),							# Down Right
				(endY, endX),						# Up Right
			))
			start, end = polygon(line[:, 0], line[:, 1], frame.shape)
			frame[start, end] = args.color
		frame = np.flipud(frame)
		return frame


def renderPoint(args):
	if(args.style == "bars"):
		point = np.full((int(args.barHeight), int(args.binWidth), 3), args.color)
		return point
	if(args.style == "circles"):
		point = np.full((int(args.binWidth), int(args.binWidth), 3), args.backgroundColor)
		rr, cc = disk((int(args.binWidth/2), int(args.binWidth/2)), int(args.binWidth/2))
		point[rr, cc, :] = args.color
		return point
	if(args.style == "donuts"):
		point = np.full((int(args.binWidth), int(args.binWidth), 3), args.backgroundColor)
		rr, cc = disk((int(args.binWidth/2), int(args.binWidth/2)), int(args.binWidth/2))
		point[rr, cc, :] = args.color
		rr, cc = disk((int(args.binWidth/2), int(args.binWidth/2)), int(args.binWidth/2 * 0.5))
		point[rr, cc, :] = args.backgroundColor
		return point