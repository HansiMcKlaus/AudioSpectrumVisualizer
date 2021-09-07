import numpy as np
from skimage.draw import disk, line as line_, polygon

def renderFrame(args, bins, j):
	frame = np.full((args.height, int(args.bins*(args.binWidth+args.binSpacing)), 3), args.backgroundColor)
	frame = frame.astype(np.uint8)					# Set datatype to uint8 to reduce RAM usage

	if(args.style == "bars" and args.barHeight == -1):
		for k in range(args.bins):
			frame[int(0):int(np.ceil(bins[j,k]*args.height)),
			int(k*args.binWidth + k*args.binSpacing):int((k+1)*args.binWidth + k*args.binSpacing)] = args.color

	if(args.style == "bars" and args.barHeight != -1 or args.style == "circles" or args.style == "donuts"):
		point = renderPoint(args)
		binSpace = args.height - point.shape[0]
		for k in range(args.bins):
			binStart = int(k*args.binWidth + k*args.binSpacing)
			offset = int(args.binWidth - point.shape[1])

			frame[int(np.ceil(bins[j,k]*binSpace)):int(np.ceil(bins[j,k]*binSpace + point.shape[0])),
			binStart + offset:binStart + point.shape[1] + offset] = point

	if(args.style == "line"):
		binSpace = args.height - args.lineThickness
		paddedFrame = np.full((args.height, int(args.bins*(args.binWidth+args.binSpacing) + 2*args.lineThickness), 3), args.backgroundColor)
		paddedFrame = paddedFrame.astype(np.uint8)
		for k in range(args.bins - 1):
			startY = int(bins[j,k]*binSpace)
			if(k == 0):
				startX = 0
			else:
				startX = int(k * (args.binWidth + args.binSpacing) + 0.5 * (args.binWidth + args.binSpacing))
			endY = int(bins[j,k+1]*binSpace)
			if(k == args.bins - 2):
				endX = frame.shape[1] - 1
			else:
				endX = int((k+1) * (args.binWidth + args.binSpacing) + 0.5 * (args.binWidth + args.binSpacing))

			rr, cc = line_(startY, startX, endY, endX)
			for i in range(len(rr)):
				paddedFrame[rr[i]:int(rr[i]+args.lineThickness), int(cc[i] + 0.5*args.lineThickness):int(cc[i]+ 1.5*args.lineThickness)] = args.color
		frame = paddedFrame[:,int(args.lineThickness):int(-args.lineThickness)]

	if(args.style == "fill"):
		for k in range(args.bins - 1):
			startY = np.ceil(bins[j,k]*args.height)
			if(k == 0):
				startX = 0
			else:
				startX = int(k * (args.binWidth + args.binSpacing) + 0.5 * (args.binWidth + args.binSpacing))
			endY = np.ceil(bins[j,k+1]*args.height)
			if(k == args.bins - 2):
				endX = frame.shape[1] - 1
			else:
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