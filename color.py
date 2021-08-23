from sys import exit

"""
This dictionary contains all named colors.
To add a new color:
"<Color name>": <[R, G, B],
"""
colors = {
	# No color
	"black": [0, 0, 0],
	"white": [255, 255, 255],

	# Red
	"indianRed": [205, 92, 92],
	"lightCoral": [240, 128, 128],
	"salmon": [250, 128, 114],
	"darkSalmon": [233, 150, 122],
	"lightSalmon": [255, 160, 122],
	"crimson": [220, 20, 60],
	"red": [255, 0, 0],
	"fireBrick": [178, 34, 34],
	"darkRed": [139, 0, 0],

	# Pink
	"pink": [255, 192, 203],
	"lightPink": [255, 182, 193],
	"hotPink": [255, 105, 180],
	"deepPink": [255, 20, 147],
	"mediumVioletRed": [199, 21, 133],
	"paleVioletRed": [219, 112, 147],

	# Orange
	"coral": [255, 127, 80],
	"tomato": [255, 99, 71],
	"orangeRed": [255, 69, 0],
	"darkOrange": [255, 140, 0],
	"orange": [255, 165, 0],

	# Yellow
	"gold": [255, 215, 0],
	"yellow": [255, 255, 0],
	"lightYellow": [255, 255, 224],
	"lemonChiffon": [255, 250, 205],
	"lightGoldenrodYellow": [250, 250, 210],
	"papayaWhip": [255, 239, 213],
	"moccasin": [255, 228, 181],
	"peachPuff": [255, 218, 185],
	"paleGoldenrod": [238, 232, 170],
	"khaki": [240, 230, 140],
	"darkKhaki": [189, 183, 107],

	# Purple
	"lavender": [230, 230, 250],
	"thistle": [216, 191, 216],
	"plum": [221, 160, 221],
	"violet": [238, 130, 238],
	"orchid": [218, 112, 214],
	"magenta": [255, 0, 255],
	"fuchsia": [255, 0, 255],
	"mediumOrchid": [186, 85, 211],
	"mediumPurple": [147, 112, 219],
	"rebeccaPurple": [102, 51, 153],
	"blueViolet": [138, 43, 226],
	"darkViolet": [148, 0, 211],
	"darkOrchid": [153, 50, 204],
	"darkMagenta": [139, 0, 139],
	"purple": [128, 0, 128],
	"indigo": [75, 0, 130],
	"slateBlue": [106, 90, 205],
	"darkSlateBlue": [72, 61, 139],
	"mediumSlateBlue": [123, 104, 238],

	# Green
	"greenYellow": [173, 255, 47],
	"chartreuse": [127, 255, 0],
	"lawnGreen": [124, 252, 0],
	"lime": [0, 255, 0],
	"limeGreen": [50, 205, 50],
	"paleGreen": [152, 251, 152],
	"lightGreen": [144, 238, 144],
	"mediumSpringGreen": [0, 250, 154],
	"springGreen": [0, 255, 127],
	"mediumSeaGreen": [60, 179, 113],
	"seaGreen": [46, 139, 87],
	"forestGreen": [34, 139, 34],
	"green": [0, 128, 0],
	"darkGreen": [0, 100, 0],
	"yellowGreen": [154, 205, 50],
	"oliveDrab": [107, 142, 35],
	"olive": [128, 128, 0],
	"darkOliveGreen": [85, 107, 47],
	"mediumAquamarine": [102, 205, 170],
	"darkSeaGreen": [143, 188, 139],
	"lightSeaGreen": [32, 178, 170],
	"darkCyan": [0, 139, 139],
	"teal": [0, 128, 128],

	# Blue
	"cyan": [0, 255, 255],
	"aqua": [0, 255, 255],
	"lightCyan": [224, 255, 255],
	"paleTurqouoise": [175, 238, 238],
	"aquamarine": [127, 255, 212],
	"turquoise": [64, 224, 208],
	"mediumTurqouoise": [72, 209, 204],
	"darkTurqouoise": [0, 206, 209],
	"cadetBlue": [95, 158, 160],
	"steelBlue": [70, 130, 180],
	"lightSteelBlue": [176, 196, 222],
	"powderBlue": [176, 224, 230],
	"lightBlue": [173, 216, 230],
	"skyBlue": [135, 206, 235],
	"lightSkyBlue": [135, 206, 250],
	"deepSkyBlue": [0, 191, 255],
	"dodgerBlue": [30, 144, 255],
	"cornflowerBlue": [100, 149, 237],
	"royaleBlue": [65, 105, 225],
	"blue": [0, 0, 255],
	"mediumBlue": [0, 0, 205],
	"darkBlue": [0, 0, 139],
	"navy": [0, 0, 128],
	"midnightBlue": [25, 25, 112],

	# Brown
	"cornsilk": [255, 248, 220],
	"blanchedAlmond": [255, 235, 205],
	"bisque": [255, 228, 196],
	"navojoWhite": [255, 222, 173],
	"wheat": [245, 222, 179],
	"burlyWood": [222, 184, 135],
	"tan": [210, 180, 140],
	"rosyBrown": [188, 143, 143],
	"sandyBrown": [244, 164, 96],
	"goldenrod": [218, 165, 32],
	"darkGoldenrod": [184, 134, 11],
	"peru": [205, 133, 63],
	"chocolate": [210, 105, 30],
	"saddleBrown": [139, 69, 19],
	"sienna": [160, 82, 45],
	"brown": [165, 42, 42],
	"maroon": [128, 0, 0],

	# White
	"snow": [255, 250, 250],
	"honeyDew": [240, 255, 240],
	"mintCream": [245, 255, 250],
	"azure": [240, 255, 255],
	"aliceBlue": [240, 248, 255],
	"ghostWhite": [248, 248, 255],
	"whiteSmoke": [245, 245, 245],
	"seaShell": [255, 245, 238],
	"beige": [245, 245, 220],
	"oldLace": [253, 245, 230],
	"floralWhite": [255, 250, 240],
	"ivory": [255, 255, 240],
	"antiqueWhite": [250, 235, 215],
	"linen": [250, 240, 230],
	"lavenderBlush": [255, 240, 245],
	"mystyRose": [255, 228, 225],

	# Gray
	"gainsboro": [220, 220, 220],
	"lightGray": [211, 211, 211],
	"silver": [192, 192, 192],
	"darkGray": [169, 169, 169],
	"gray": [128, 128, 128],
	"dimGray": [105, 105, 105],
	"lightSlateGray": [119, 136, 153],
	"slateGray": [112, 128, 144],
	"darkSlateGray": [47, 79, 79]
}


"""
Converts HEX string or color name into RGB.
"""
def hex2rgb(hex):
	if hex in colors:
		return colors[hex]
	else:
		if(len(hex) != 6):
			exit("Color is not a valid HEX code, eg. ff0000.")
		try:
			color = []
			for i in (0, 2, 4):
				color.append(int(hex[i:i+2], 16))
			return color
		except:
			exit("Color is neither a named color, e.g. red or a valid HEX code, eg. ff0000.")