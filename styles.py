import numpy as np
from skimage.draw import disk, line as line_, polygon

def renderFrame(args, bins, j):
	if len(bins) == 1:
		bins = bins[0]
		frame = renderMonoChannel(args, bins, j)
	if len(bins) == 2:
		frame = renderStereoChannel(args, bins, j)
	
	return frame

def renderMonoChannel(args, bins, j):
	if args.mirror == 0:
		height = args.height
	else:
		fullFrame = np.full((args.height, args.width, 3), args.backgroundColor).astype(np.uint8)
		height = int(args.height/2)

	frame = np.full((height, args.width, 3), args.backgroundColor).astype(np.uint8)

	if not args.radial:
		if args.style == "bars" and args.barHeight == -1:
			for k in range(args.bins):
				frame[:int(np.ceil(bins[j,k]*height)),
				int(k/args.bins*args.width + args.binSpacing/2):int((k+1)/args.bins*args.width - args.binSpacing/2)] = args.color

		if args.style == "bars" and args.barHeight != -1 or args.style == "circles" or args.style == "donuts":
			point = renderPoint(args)
			binSpace = height - point.shape[0]
			
			for k in range(args.bins):
				binStart = int(k*args.binWidth + k*args.binSpacing)
				offset = int(args.binWidth - point.shape[1])

				frame[int(bins[j,k]*binSpace):int(bins[j,k]*binSpace + point.shape[0]),
				int(k/args.bins*args.width + args.binSpacing/2):int((k+1)/args.bins*args.width - args.binSpacing/2)] = point

		if args.style == "line":
			binSpace = height - args.lineThickness
			paddedFrame = np.full((height, args.width + 2*args.lineThickness, 3), args.backgroundColor).astype(np.uint8)

			for k in range(args.bins):
				vector1Y = int(bins[j,k]*binSpace)

				if k == 0:
					vector1X = 0
				else:
					vector1X = int(k/args.bins*args.width)

				if k == args.bins - 1:
					vector2Y = int(bins[j,k]*binSpace)
					vector2X = frame.shape[1] - 1
				else:
					vector2Y = int(bins[j,k+1]*binSpace)
					vector2X = int((k+1)/args.bins*args.width)

				rr, cc = line_(vector1Y, vector1X, vector2Y, vector2X)
				for i in range(len(rr)):
					paddedFrame[rr[i]:int(rr[i]+args.lineThickness), int(cc[i] + 0.5*args.lineThickness):int(cc[i]+ 1.5*args.lineThickness)] = args.color
			frame = paddedFrame[:,int(args.lineThickness):int(-args.lineThickness)]

		if args.style == "fill":
			for k in range(args.bins):
				vector1Y = np.ceil(bins[j,k]*height)

				if k == 0:
					vector1X = 0
				else:
					vector1X = int(k/args.bins*args.width)

				if k == args.bins - 1:
					vector2Y = np.ceil(bins[j,k]*height)
					vector2X = frame.shape[1] - 1
				else:
					vector2Y = np.ceil(bins[j,k+1]*height)
					vector2X = int((k+1)/args.bins*args.width)

				r = [vector1Y, vector2Y, 0, 0]
				c = [vector1X, vector2X, vector2X, vector1X]
				rr, cc = polygon(r, c, frame.shape)
				frame[rr, cc] = args.color

	if args.radial:
		midHeight = int(height/2)
		midWidth = int(args.width/2)
		maxVectorLength = args.radiusEnd - args.radiusStart

		if args.style == "bars":
			for k in range(args.bins):
				angleStart = k/args.bins + (args.binSpacing/2)/args.width
				angleEnd = (k+1)/args.bins + (-args.binSpacing/2)/args.width

				vector1Y = int(midHeight + args.radiusStart * radialVectorY(args, angleStart))
				vector1X = int(midWidth + args.radiusStart * radialVectorX(args, angleStart))
				vector2Y = int(midHeight + (args.radiusStart + bins[j,k] * maxVectorLength) * radialVectorY(args, angleStart))
				vector2X = int(midWidth + (args.radiusStart + bins[j,k]*maxVectorLength) * radialVectorX(args, angleStart))

				vector3Y = int(midHeight + (args.radiusStart + bins[j,k]*maxVectorLength) * radialVectorY(args, angleEnd))
				vector3X = int(midWidth + (args.radiusStart + bins[j,k]*maxVectorLength) * radialVectorX(args, angleEnd))
				vector4Y = int(midHeight + args.radiusStart * radialVectorY(args, angleEnd))
				vector4X = int(midWidth + args.radiusStart * radialVectorX(args, angleEnd))

				r = [vector1Y, vector2Y, vector3Y, vector4Y]
				c = [vector1X, vector2X, vector3X, vector4X]
				rr, cc = polygon(r, c, frame.shape)
				frame[rr, cc] = args.color

		if args.style == "line":
			for k in range(args.bins):
				angleStart = k/args.bins
				angleEnd = (k+1)/args.bins

				vector1Y = int(midHeight + (args.radiusStart + bins[j,k] * maxVectorLength) * radialVectorY(args, angleStart) - 1)
				vector1X = int(midWidth + (args.radiusStart + bins[j,k]*maxVectorLength) * radialVectorX(args, angleStart) - 1)

				if k == args.bins - 1:
					k = k - 1

				vector2Y = int(midHeight + (args.radiusStart + bins[j,k+1]*maxVectorLength) * radialVectorY(args, angleEnd) - 1)
				vector2X = int(midWidth + (args.radiusStart + bins[j,k+1]*maxVectorLength) * radialVectorX(args, angleEnd) - 1)

				rr, cc = line_(vector1Y, vector1X, vector2Y, vector2X)

				for i in range(len(rr)):
					frame[rr[i]:int(rr[i]+args.lineThickness), int(cc[i] + 0.5*args.lineThickness):int(cc[i]+ 1.5*args.lineThickness)] = args.color

		if args.style == "fill":
			for k in range(args.bins):
				angleStart = k/args.bins
				angleEnd = (k+1)/args.bins

				vector1Y = int(midHeight + args.radiusStart * radialVectorY(args, angleStart))
				vector1X = int(midWidth + args.radiusStart * radialVectorX(args, angleStart))
				vector2Y = int(midHeight + (args.radiusStart + bins[j,k] * maxVectorLength) * radialVectorY(args, angleStart))
				vector2X = int(midWidth + (args.radiusStart + bins[j,k]*maxVectorLength) * radialVectorX(args, angleStart))

				if k == args.bins - 1:
					k = k - 1

				vector3Y = int(midHeight + (args.radiusStart + bins[j,k+1]*maxVectorLength) * radialVectorY(args, angleEnd))
				vector3X = int(midWidth + (args.radiusStart + bins[j,k+1]*maxVectorLength) * radialVectorX(args, angleEnd))
				vector4Y = int(midHeight + args.radiusStart * radialVectorY(args, angleEnd))
				vector4X = int(midWidth + args.radiusStart * radialVectorX(args, angleEnd))

				r = [vector1Y, vector2Y, vector3Y, vector4Y]
				c = [vector1X, vector2X, vector3X, vector4X]
				rr, cc = polygon(r, c, frame.shape)
				frame[rr, cc] = args.color

	frame = np.flipud(frame)

	if args.channel != "stereo":
		if args.mirror == 1:
			fullFrame[:frame.shape[0],:] = frame
			fullFrame[frame.shape[0]:frame.shape[0]*2,:] = np.flipud(frame)
			frame = fullFrame

		elif args.mirror == 2:
			fullFrame[:frame.shape[0],:] = np.flipud(frame)
			fullFrame[frame.shape[0]:frame.shape[0]*2,:] = frame
			frame = fullFrame

	return frame

def renderStereoChannel(args, bins, j):
	left = bins[0]
	right = bins[1]
	frame = np.full((args.height, args.width, 3), args.backgroundColor).astype(np.uint8)

	frame1 = renderMonoChannel(args, left, j)
	frame2 = renderMonoChannel(args, right, j)

	if args.mirror == 1:
		frame[:frame1.shape[0],:] = frame1
		frame[frame2.shape[0]:frame2.shape[0]*2,:] = np.flipud(frame2)

	elif args.mirror == 2:
		frame[:frame1.shape[0],:] = np.flipud(frame1)
		frame[frame2.shape[0]:frame.shape[0]*2,:] = frame2
	
	if args.radial:
		frame[:,:int(frame1.shape[1]/2)] = np.fliplr(frame1[:,int(frame1.shape[1]/2):])
		frame[:,int(frame2.shape[1]/2):] = frame2[:,int(frame2.shape[1]/2):]

		if args.catgirl:
			frame[args.frameMask] = args.catgirlImage[args.catgirlImageMask,:3]

	return frame


def renderPoint(args):
	if args.style == "bars":
		point = np.full((int(args.barHeight), int(args.binWidth), 3), args.color)
		return point
	if args.style == "circles":
		point = np.full((int(args.binWidth), int(args.binWidth), 3), args.backgroundColor)
		rr, cc = disk((int(args.binWidth/2), int(args.binWidth/2)), int(args.binWidth/2))
		point[rr, cc, :] = args.color
		return point
	if args.style == "donuts":
		point = np.full((int(args.binWidth), int(args.binWidth), 3), args.backgroundColor)
		rr, cc = disk((int(args.binWidth/2), int(args.binWidth/2)), int(args.binWidth/2))
		point[rr, cc, :] = args.color
		rr, cc = disk((int(args.binWidth/2), int(args.binWidth/2)), int(args.binWidth/2 * 0.5))
		point[rr, cc, :] = args.backgroundColor
		return point

def radialVectorY(args, angle):
	vector = np.cos(2*np.pi * (angle * args.circumference + args.rotation))
	return vector

def radialVectorX(args, angle):
	vector = np.sin(2*np.pi * (angle * args.circumference + args.rotation))
	return vector