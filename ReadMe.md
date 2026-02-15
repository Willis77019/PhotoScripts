\# Geology Photo Stitcher Tools
A collection of Python scripts for automating geological image processing (HDRs and Panoramas).



\# Prerequisites
Install Hugin:
Many of these scripts require the Hugin Panorama Stitcher command-line tools.

Windows: Download from hugin.sourceforge.io.

Mac/Linux: Install via Homebrew (brew install hugin) or your package manager.

Install Python Libraries:

Bash
pip install -r requirements.txt



\# How to Use
There are currently five independent scripts that do different tasks.

1. Pano\_Batcher.py : Searches though a folder and finds sets of images to stitch into photomosaics.
2. HDR\_Batcher.py : Finds sets of images to combine to make high-dynamic-range (HDR) or focus-stack photos.
3. ImageSeq\_to\_Video.py : Combines images in a folder to make a video (Microsoft Moviemaker replacement)
4. PhotoMosaicPan.py: Makes a video than pans along a photomosaic (better for sharing and presentation of observations)
5. EarthTimelapse.py: User friendly download of high-resolution LandSat timelapse images from Google EarthEngine.



Open one of the scripts in Jupyter, CoLab, or other python environment.
Edit the Configuration Section at the top code segment
Run the script!



\# Notes on use.

The Pano\_Batcher and HDR\_Batcher might work on a folder with a mix of image files
by selecting images for processing with similar time stamps. If this auto-section fails,

then put just files to be processed in a separate folder.
The HDR\_Batcher.ipyn script will also do focus stacking, see comments in the code for details.
The ImageSeq\_to\_Video.ipynb script expects the files to ordered sequentially.
The PhotoMosaicPan.ipynb expects an image that is much longer than it is high.

More details on the use of each script are listed in the file header.

