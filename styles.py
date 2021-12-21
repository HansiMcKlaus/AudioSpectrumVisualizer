import numpy as np
from skimage.draw import disk, line as line_, polygon

def renderFrame(args, bins, j):
	if(len(bins) == 1):
		bins = bins[0]
		frame = renderMonoChannel(args, bins, j)
	if(len(bins) == 2):
		frame = renderStereoChannel(args, bins, j)
	
	return frame


def renderMonoChannel(args, bins, j):
	if(args.mirror != 0):
		fullFrame = np.full((args.height, int(args.bins*(args.binWidth+args.binSpacing)), 3), args.backgroundColor)
		fullFrame = fullFrame.astype(np.uint8)
		height = int(args.height/2)
	else:
		height = args.height

	frame = np.full((height, int(args.bins*(args.binWidth+args.binSpacing)), 3), args.backgroundColor)
	frame = frame.astype(np.uint8)					# Set datatype to uint8 to reduce RAM usage

	if(args.style == "bars" and args.barHeight == -1):
		for k in range(args.bins):
			frame[int(0):int(np.ceil(bins[j,k]*height)),
			int(k*args.binWidth + k*args.binSpacing):int((k+1)*args.binWidth + k*args.binSpacing)] = args.color

	if(args.style == "bars" and args.barHeight != -1 or args.style == "circles" or args.style == "donuts"):
		point = renderPoint(args)
		binSpace = height - point.shape[0]
		for k in range(args.bins):
			binStart = int(k*args.binWidth + k*args.binSpacing)
			offset = int(args.binWidth - point.shape[1])

			frame[int(np.ceil(bins[j,k]*binSpace)):int(np.ceil(bins[j,k]*binSpace + point.shape[0])),
			binStart + offset:binStart + point.shape[1] + offset] = point

	if(args.style == "line"):
		binSpace = height - args.lineThickness
		paddedFrame = np.full((height, int(args.bins*(args.binWidth+args.binSpacing) + 2*args.lineThickness), 3), args.backgroundColor)
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
		if args.radial:
			midHeight = int(height/2)
			midWidth = int(args.width/2)
			maxLength = args.radiusEnd - args.radiusStart
			for k in range(args.bins):
				vertex1Y = int(midHeight + (args.radiusStart * np.cos(2*np.pi * (k/args.bins))))
				vertex1X = int(midWidth + (args.radiusStart * np.sin(2*np.pi * (k/args.bins))))
				vertex2Y = int(midHeight + (args.radiusStart + bins[j,k]*maxLength) * np.cos(2*np.pi * (k/args.bins)))
				vertex2X = int(midWidth + (args.radiusStart + bins[j,k]*maxLength) * np.sin(2*np.pi * (k/args.bins)))
				kNext = (k+1) % (args.bins)
				vertex3Y = int(midHeight + (args.radiusStart + bins[j,kNext]*maxLength) * np.cos(2*np.pi * (kNext/args.bins)))
				vertex3X = int(midWidth + (args.radiusStart + bins[j,kNext]*maxLength) * np.sin(2*np.pi * (kNext/args.bins)))
				vertex4Y = int(midHeight + (args.radiusStart * np.cos(2*np.pi * (kNext/args.bins))))
				vertex4X = int(midWidth + (args.radiusStart * np.sin(2*np.pi * (kNext/args.bins))))

				r = [vertex1Y, vertex2Y, vertex3Y, vertex4Y]
				c = [vertex1X, vertex2X, vertex3X, vertex4X]
				rr, cc = polygon(r, c, frame.shape)
				frame[rr, cc] = args.color
		else:
			for k in range(args.bins - 1):
				startY = np.ceil(bins[j,k]*height)
				if(k == 0):
					startX = 0
				else:
					startX = int(k * (args.binWidth + args.binSpacing) + 0.5 * (args.binWidth + args.binSpacing))
				endY = np.ceil(bins[j,k+1]*height)
				if(k == args.bins - 2):
					endX = frame.shape[1] - 1
				else:
					endX = int((k+1) * (args.binWidth + args.binSpacing) + 0.5 * (args.binWidth + args.binSpacing))
				r = [startY, endY, 0, 0]
				c = [startX, endX, endX, startX]
				rr, cc = polygon(r, c, frame.shape)
				frame[rr, cc] = args.color

	frame = np.flipud(frame)
	if(args.channel != "stereo"):
		if(args.mirror == 1):
			fullFrame[:frame.shape[0],:] = frame
			fullFrame[frame.shape[0]:frame.shape[0]*2,:] = np.flipud(frame)
			frame = fullFrame
		elif(args.mirror == 2):
			fullFrame[:frame.shape[0],:] = np.flipud(frame)
			fullFrame[frame.shape[0]:frame.shape[0]*2,:] = frame
			frame = fullFrame

	return frame

def renderStereoChannel(args, bins, j):
	left = bins[0]
	right = bins[1]
	frame = np.full((args.height, int(args.bins*(args.binWidth+args.binSpacing)), 3), args.backgroundColor)
	frame = frame.astype(np.uint8)

	frame1 = renderMonoChannel(args, left, j)
	frame2 = renderMonoChannel(args, right, j)

	if(args.mirror == 1):
		frame[:frame1.shape[0],:] = frame1
		frame[frame2.shape[0]:frame2.shape[0]*2,:] = np.flipud(frame2)
	elif(args.mirror == 2):
		frame[:frame1.shape[0],:] = np.flipud(frame1)
		frame[frame2.shape[0]:frame.shape[0]*2,:] = frame2

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