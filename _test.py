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


def getArgs():
    args = arguments.initArgs()
    fileData = np.load("testData.npy")
    samplerate = 44100
    arguments.processArgs(args, fileData, samplerate)
    return args

def test_exitOnInvalidArgs():
    baseArgs = ['AudioSpectrumVisualizer.py','inputfile', 'destination', '-t']

    # Presets
    sys.argv = baseArgs + ['-ps', 'sChwUrasdADlavASD']
    with pytest.raises(SystemExit):
        args = getArgs()

    # Output dimensions
    sys.argv = baseArgs + ['-ht', '0']
    with pytest.raises(SystemExit):
        args = getArgs()

    sys.argv = baseArgs + ['-w', '0']
    with pytest.raises(SystemExit):
        args = getArgs()

    # Bins
    sys.argv = baseArgs + ['-b', '0']
    with pytest.raises(SystemExit):
        args = getArgs()

    sys.argv = baseArgs + ['-bw', '0']
    with pytest.raises(SystemExit):
        args = getArgs()

    sys.argv = baseArgs + ['-bs', '-2']
    with pytest.raises(SystemExit):
        args = getArgs()

    # Frequencies
    sys.argv = baseArgs + ['-fe', '0']
    with pytest.raises(SystemExit):
        args = getArgs()

    sys.argv = baseArgs + ['-fe', '1000', '-fs', '1001']
    with pytest.raises(SystemExit):
        args = getArgs()


def test_processArgs():
    baseArgs = ['AudioSpectrumVisualizer.py','inputfile', 'destination', '-t']

    # Bins & Width
    sys.argv = baseArgs + ['-w', '1920', '-bw', '25', '-bs', '25']
    args = getArgs()
    assert args.width == 3200
