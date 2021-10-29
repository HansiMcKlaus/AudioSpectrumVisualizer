import color
import arguments

import pytest
import sys
import numpy as np
from math import isclose

def test_colorDict2rgb():
    for cStr in color.colors.keys():
        assert color.hex2rgb(cStr) == color.colors[cStr]

def test_str2rgb():
    assert color.hex2rgb("hotpink") == [255, 105, 180]
    assert color.hex2rgb("HOTPINK") == [255, 105, 180]
    assert color.hex2rgb("hOtPiNk") == [255, 105, 180]

def test_hexcode2rgb():
    assert color.hex2rgb("ff69b4") == [255, 105, 180]
    assert color.hex2rgb("FF69B4") == [255, 105, 180]
    assert color.hex2rgb("fF69b4") == [255, 105, 180]

def test_shortHexcode2rgb():
    assert color.hex2rgb("acf") == [170, 204, 255]
    assert color.hex2rgb("ACF") == [170, 204, 255]
    assert color.hex2rgb("aCf") == [170, 204, 255]

# args helpers
def getArgs(argsList):
    baseArgs = ['AudioSpectrumVisualizer.py','inputfile', 'destination']
    sys.argv = baseArgs + argsList

    args = arguments.initArgs()
    fileData = np.load("testData.npy")
    samplerate = 44100
    arguments.processArgs(args, fileData, samplerate)
    return args

# args tests
def test_exitOnInvalidArgs():
    # Presets
    with pytest.raises(SystemExit):
        args = getArgs(['-ps', 'sChwUrasdADlavASD'])

    # Output dimensions
    with pytest.raises(SystemExit):
        args = getArgs(['-ht', '0'])
    with pytest.raises(SystemExit):
        args = getArgs(['-w', '0'])

    # Bins
    with pytest.raises(SystemExit):
        args = getArgs(['-b', '0'])
    with pytest.raises(SystemExit):
        args = getArgs(['-bw', '0'])
    with pytest.raises(SystemExit):
        args = getArgs(['-bs', '-2'])

    # Framerate
    with pytest.raises(SystemExit):
        args = getArgs(['-fr', '0'])

    # Channels
    with pytest.raises(SystemExit):
        args = getArgs(['-ch', 'random'])

    # Duration
    with pytest.raises(SystemExit):
        args = getArgs(['-d', '0'])
    with pytest.raises(SystemExit):
        args = getArgs(['-d', '50'])    # too long for the test frame data

    # Delimiters
    with pytest.raises(SystemExit):
        args = getArgs(['-s', '-1'])
    with pytest.raises(SystemExit):
        args = getArgs(['-e', '0'])
    with pytest.raises(SystemExit):
        args = getArgs(['-s', '0.01', '-e', '0'])

    # Logarithms
    with pytest.raises(SystemExit):
        args = getArgs(['-xlog', '-1'])
    with pytest.raises(SystemExit):
        args = getArgs(['-ylog', '-1'])

    # Smoothing
    with pytest.raises(SystemExit):
        args = getArgs(['-sy', '-1'])           # fix smoothY type, make int instead of str?

    # Frequencies
    with pytest.raises(SystemExit):
        args = getArgs(['-fe', '0'])
    with pytest.raises(SystemExit):
        args = getArgs(['-fs', '-1'])
    with pytest.raises(SystemExit):
        args = getArgs(['-fe', '1000', '-fs', '1001'])

    # Styles
    with pytest.raises(SystemExit):
        args = getArgs(['-st', 'random'])
    with pytest.raises(SystemExit):
        args = getArgs(['-bht', '0'])
    with pytest.raises(SystemExit):
        args = getArgs(['-lt', '0'])
    with pytest.raises(SystemExit):
        args = getArgs(['-m', '3'])
        # Colors
    with pytest.raises(SystemExit):
        args = getArgs(['-bgc', '00'])
    with pytest.raises(SystemExit):
        args = getArgs(['-c', '00'])
    with pytest.raises(SystemExit):
        args = getArgs(['-c', 'ggg'])
    with pytest.raises(SystemExit):
        args = getArgs(['-c', '0000000'])

    # Performance
    with pytest.raises(SystemExit):
        args = getArgs(['-cs', '0'])
    with pytest.raises(SystemExit):
        args = getArgs(['-p', '0'])


def test_processArgs():
    # Bins & Width
    args = getArgs(['-w', '1920', '-bw', '25', '-bs', '25'])
    assert args.width == 3200

    # Colors
    args = getArgs(['-c', 'hotpink'])
    assert args.color == [180, 105, 255]
    assert color.colors['hotpink'] == [255, 105, 180]       # Check if object in colors dictionary is reversed

    args = getArgs(['-c', 'hotpink', '-bgc', 'hotpink'])
    assert args.color == [180, 105, 255]
    assert args.backgroundColor == [180, 105, 255]
