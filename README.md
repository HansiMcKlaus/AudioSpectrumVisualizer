# AudioSpectrumVisualizer

Creates a customizable image sequence for the spectrum of an audio file.



## Dependencies

Requires the following packages: `numpy`, `audio2numpy`, `matplotlib`, `ffmpeg` and `joblib`



## Usage

Open a command line and change into the directory where the program is located. It is easiest to simply copy the audio file into the same directory, however not at all necessary.

To run the program: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder>` (If no destination folder is given, it defaults to `.\Image Sequence` and creates a new folder in the current directory named `Image Sequence`)

Example: `python AudioSpectrumVisualizer.py '.\Bursty Greedy Spider.mp3' 'Visualizer'`

This creates an image sequence for the audio spectrum of`Bursty Greedy Spider.mp3` into a newly created folder named `Visualizer` in the same directory.

Example for when audio and destination directory are not in the same directory as the program : `python AudioSpectrumVisualizer.py '.\User\Music\Bursty Greedy Spider.mp3' '.\User\Desktop\Visualizer'`



## Optional  arguments

`-h, --help` Shows the standard help message

`-b, --bins` Amount of bins (bars, points, etc). Default: 64

`-ht, --height` Height of the image in px. Default: 540

`-w, --width` Width of the image in px. Will be overwritten if both bin_width AND bin_spacing is given! Default: 1920

` -bw, --bin_width` Width of the bins in px. Default: auto (5/6 * width/bins)

`-bs, --bin_spacing` Spacing between bins in px. Default: auto (1/6 * width/bins)

`-fr, --framerate` Framerate of the image sequence (Frames per second). Default: 30

`-ch, --channel` Which channel to use (left, right, average). Default: average

`-xlog` Scales the X-axis logarithmically to a given base. Default: 0 (Linear)

`-ylog` Scales the Y-axis logarithmically to a given base. Default: 0 (Linear)

`-st, --smoothT` Smoothing over past/next \<smoothT> frames (Smoothes bin over time). If smoothT=auto: Automatic smoothing is applied (framerate/15). Default: 0

`-sy, --smoothY` Smoothing over past/next \<smoothY> bins (Smoothes bin with adjacent bins). If smoothY=auto: Automatic smoothing is applied (bins/32). Default: 0

`-s, --start` Begins render at \<start> seconds. Default: 0

`-e, --end` Ends render at \<end> seconds. If end = -1: Renders to the end of the sound file. Default: -1

`-fs, --frequencyStart` Limits the range of frequencies to \<frequencyStart>Hz and onward. Default: 0

`-fe, --frequencyEnd` Limits the range of frequencies to \<frequencyEnd>Hz. If frequencyEnd = -1: Ends at highest frequency. Default: -1

`-v, --video` Additionally creates a video (.mp4) from image sequence. Default: False"

`-va, --videoAudio` Additionally creates a video (.mp4) from image sequence and audio. Default: False"

`-ds, --disableSmoothing` Disables all smoothing (smoothT and smoothY). Default: False

<br>

`-cs, --chunkSize` Amount of frames cached before clearing (Higher chunk size lowers render time, but increases RAM usage). Default: auto

`-cr, --cores` Number of cores to use for rendering and export. Default: All cores

RAM usage is proportional to the chunksize multiplied by the number of cores. Per default (auto) the chunksize is set to 128 divided by the number of cores. Ex. 128/4 = chunksize of 32 per core on a machine with 4 cores. You may want to increase the chunksize on a machine with many cores for better performance, as a larger chunksize per core increases speed.
Warning: Setting the chunksize too high on a low amount of rendered frames may lead to bad load balancing, resulting in a slower export.



## Styles

Currently only a white bar chart, however more will be added at a later date!

`-t, --test` Renders only a single frame for style testing. Default: False

`-c, --color` Color of bins (bars, points, etc). Ex: ff0000 or red. Default: ffffff (white)

`-bgc, --backgroundColor` Color of the background. Ex: ff0000 or red. Default: 000000 (black)



## Examples

Default: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder>`

<img src="screenshots/default.png" alt="default" style="zoom: 50%;" />

Slim bins: `python AudioSpectrumVisualizer.py <Path to Audio File> <Destination Folder> -b 128 -bw 5`

<img src="screenshots/slimBins.png" alt="default" style="zoom: 50%;" />
