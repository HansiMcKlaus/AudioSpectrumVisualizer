# AudioSpectrumVisualizer

**NOTE: This project is abandoned**. The new project can be found at [HansiAudioVisualizer](https://github.com/HansiMcKlaus/HansiAudioVisualizer).

Creates a customizable video for the spectrum of an audio file.



## Dependencies

Install python dependencies: `pip install -r requirements.txt`

This script requires [ffmpeg](https://ffmpeg.org/download.html).

  - Linux:
    - Debian/Ubuntu: `sudo apt-get install ffmpeg`
    - Arch: `sudo pacman -S ffmpeg`
  - macOS: `homebrew install ffmpeg`
  - Windows:
    1. [Download ffmpeg](https://ffmpeg.org/download.html)
    2. Extract it into a folder, for example `C:\FFmpeg`
    3. Add the ffmpeg bin folder to your PATH Environment Variable.
    
    [Here](https://www.thewindowsclub.com/how-to-install-ffmpeg-on-windows-10) is a guide that explains the process in detail.



## Usage

Open a command line and change into the directory where the program is located. It is easiest to simply copy the audio file into the same directory, however not at all necessary.

To run the program: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder>` (If no destination folder is given, it defaults to `output` in the current directory)

Example: `python AudioSpectrumVisualizer.py 'Bursty Greedy Spider.mp3' Visualizer`

This creates an image sequence for the audio spectrum of `Bursty Greedy Spider.mp3` into a newly created folder named `Visualizer` in the same directory.

Example for when audio and destination directory are not in the same directory as the program : `python AudioSpectrumVisualizer.py '.\User\Music\Bursty Greedy Spider.mp3' '.\User\Desktop\Visualizer'`



## General

`-ps, --preset` Name of a preset defined as a collection of flags in presets.txt. Default: default. Note that the default preset is blank on a fresh install, feel free to define it as you like

`-h, --help` Shows the standard help message

`-ht, --height` Height of the output video/images in px. Default: 540

`-w, --width` Width of the output video/images in px. Will be overwritten if both binWidth AND binSpacing is given! Default: 1920

`-b, --bins` Amount of bins (bars, points, etc). Default: 64

` -bw, --binWidth` Width of the bins in px. Default: 5/6 * width/bins

`-bs, --binSpacing` Spacing between bins in px. Default: 1/6 * width/bins

`-fr, --framerate` Framerate of the output video/image sequence (Frames per second). Default: 30

`-ch, --channel` Which channel to use (left, right, average, stereo). Default: average

`-d, --duration` Length of audio sample per frame in ms. Default: Duration will be one frame long (1/framerate)

`-s, --start` Begins render at \<start> seconds. Default: Renders from the start of the sound file

`-e, --end` Ends render at \<end> seconds. Default: Renders to the end of the sound file

`-xlog` Scales the X-axis logarithmically to a given base. Default: 0 (Linear)

`-ylog` Scales the Y-axis logarithmically to a given base. Default: 0 (Linear)

`-sy, --smoothY` Smoothing over \<n> adjacent bins. If smoothY=auto: Automatic smoothing is applied (bins/32). Default: 0

`-fs, --frequencyStart` Limits the range of frequencies to \<frequencyStart>Hz and onward. Default: Starts at lowest frequency

`-fe, --frequencyEnd` Limits the range of frequencies to \<frequencyEnd>Hz. Default: Ends at highest frequency

`-is, --imageSequence` Export visualization as frame-by-frame image sequence instead of .mp4 with audio. Default: False"



## Style

`-t, --test` Renders a single frame for style testing. Default: False

`-st, --style` Defines render style: bars, circles, donuts, line, fill. Default: bars

`-bht, --barHeight` Height of the bars in px. Default: full

`-lt, --lineThickness` Thickness of the line in px. Default: 3

`-m, --mirror` Mirrors the spectrum at x-axis. 1: Middle, 2: Top/Bottom Default: 0

`-r, --radial` Creates a radial (circle) visualization. Size is determined by height. Default: False

`-rs, --radiusStart` Inner radius in px. Default: 1/6 Height

`-re, --radiusEnd` Outer radius in px. Default: 1/2 Height

`-cc, --circumference` Circumference of radial visualization in degrees. Default: 360 (Full)

`-rt, --rotation` Rotation offset of radial visualization in degrees. Default: 0

`-c, --color` Color of bins (bars, points, etc). Ex: ff0000 or red. Default: ffffff (white)

`-bgc, --backgroundColor` Color of the background. Ex: ff0000 or red. Default: 000000 (black)

Color names are equal to the named colors supported by HTML and CSS: [Overview of named colors](https://htmlcolorcodes.com/color-names/).<br>
Custom colors can be added to the `colors` dictionary in `color.py` in the form of `"<color name>": [R, G, B],`.

`-i, --image` Adds an image in radial visualization if given path (See example)



## Performance

`-cs, --chunkSize` Amount of frames cached before clearing (Higher chunk size lowers render time, but increases RAM usage). Default: auto

`-p, --processes` Number of processes to use for rendering and export. Default: Number of processor cores (or hyperthreads, if supported)

RAM usage is proportional to the chunksize multiplied by the number of processes. Per default (auto) the chunksize is set to 128 divided by the number of processes. Ex. 128/4 = chunksize of 32 per process on a machine with 4 cores and no hyperthreading. You may want to increase the chunksize on a machine with large RAM for better performance, as a larger chunksize per process improves render times.



## Examples

Default: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder>`

<img src="screenshots/default.png" alt="default" style="zoom: 50%;" />

Slim bins: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder> -b 128 -bw 5`

<img src="screenshots/slimBins.png" alt="default" style="zoom: 50%;" />

IKEA: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder> -b 12 -c yellow -bgc blue`

<img src="screenshots/ikea.png" alt="default" style="zoom: 50%;" />

Circles: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder> -st circles -bw 15`

<img src="screenshots/circles.png" alt="default" style="zoom: 50%;" />

Donuts: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder> -b 32 -st donuts -c e9388c -bgc f17e06`

<img src="screenshots/donuts.png" alt="default" style="zoom: 50%;" />

Line: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder> -b 256 -st line -lt 3 -c lime`

<img src="screenshots/line.png" alt="default" style="zoom: 50%;" />

Fill: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder> -b 256 -st fill -c lime`

<img src="screenshots/fill.png" alt="default" style="zoom: 50%;" />

Mirror 1: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder> -m 1`

<img src="screenshots/mirror1.png" alt="default" style="zoom: 50%;" />

Mirror 2: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder> -m 2`

<img src="screenshots/mirror2.png" alt="default" style="zoom: 50%;" />

Radial 1: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder> -r -st line`

<img src="screenshots/radial_1.png" alt="default" style="zoom: 50%;" />

Radial 2: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder> -r -cc 180 -rt -90 -st fill`

<img src="screenshots/radial_2.png" alt="default" style="zoom: 50%;" />

Image: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder> -r -i "catgirl.png"`

<img src="screenshots/radial_image.png" alt="default" style="zoom: 50%;" />
