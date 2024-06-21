# About
This is a GUI for clitics vsd project available at:
>[clitic / vsd](https://github.com/clitic/vsd)


It is written in python and uses pysides2 to create the UI elements. Effort has been made to make it platform independent, but not all platforms are available to test.


# Requirements
1. clitics vsd:
>[clitic / vsd](https://github.com/clitic/vsd)
2. python 3.11 or higher:
>[python.org](https://www.python.org/?downloads)
3. pysides2
>[pypi.org](https://pypi.org/project/PySide2/)
```
pip install PySide2
```

# Planned Features/Progress

- [X] Enable downloads and captures to be conducted in seperate process from UI.
- [X] Enable capture through UI.
- [X] Allow selection of available video quality from capture.
- [X] Allow user set auto selection of video quality.
- [X] Create queue system for captures.
- [X] Enable auto add to download queue after capture.
- [X] Enable auto capture from queue.
- [X] Enable Download/save through UI.
- [X] Create queue system for downloads.
- [X] Allow auto downloading from queue.
- [X] Display of download status information.
- [X] Graphical progress bars.
- [X] Enable auto renaming of files after download completes.
- [X] Enable permanent user set working directory.
- [X] Enable usage of all flags.
- [X] Create a pyinstaller release of the software.
- [ ] Create Dark Mode Theme.

# Usage
```
Queue Tab
1. Displays all the URLs currently loaded in their respective queue.
2. Clicking the 'Start Queue Processing' button will start processing of the queue starting with any captures in queue.  If there is not any captures in the queue it will skip it and start the downloads in the queue.
    - Note: After a download is started from the queue it will automatically be removed from the queue.
3. After clicking the 'Start Queue Processing' button the button will be replaced by a 'Cancel Queue Processing button. Clicking this button will cause the queue to stop but the current download should continue.

Capture Tab
1. URL to Capture: Paste the url to the website you wish to capture the video from.
2. Auto Download after capture: After capturing the URL for the desired video the video will be automatically downloaded.
3. Select dropdown: Select the quality of video you desire the capture to download after capture.
    - Note: If Select is selected, the video will not be auto captured and a pop-up window will appear after capture for the user to select the desired video and it will be added to the download queue.
4. After Processing: Determine what you want done with the video after it is downloaded.
  a. Send to ffmpeg: After the video is captured it will be sent to ffmpeg to be processed.
  b. Rename the file to a desired name after the download is complete.
    - Note: You input the name of the desired file in the 'As' field for either of these actions to happen. Do not forget to include the desired format. (ie, .mp4, .mpeg, .mkv)
    - Additional Note: Files are typically in a .mp4 format, so if renaming it is best to rename with the .mp4 format name.   
5. 'Capture' button: Clicking this button will start the capture now with the desired settings you set.
    - Note: by double clicking a capture in the queue window it will load it back on the input fields.
6. 'Cancel' button: Clicking this button will cancel the current capture in operation.
7. 'Add to Queue': Clicking this button will load the current capture in the input fields into the queue.
8. 'Remove from Queue': Clicking this button will remove the currently selected item from the capture queue.

Download Tab
1. URL to Download: Paste the url to the video from the website to be downloaded.
2. After Processing: Performs the same function as the After Processing in the Capture Tab (4).
3. 'Download' button: Clicking this button will start the download of the video file currently in the input fields with the desired options selected.
4. 'Cancel' button: Clicking this button will cancel the current download in operation.
5. 'Add to Queue' button: Clicking this button will add the current data in the input fields into the download queue.
6. 'Remove from Queue': Clicking this button will remove the currently selected item from the download queue.

Preferences Window
Accessed by selecting preferences in the Edit Menu Bar option.

General Options
1. Use directory for temporarily downloaded files: Where you want the video files to be saved after downloaded.
    - Note: Files will be renamed in this loaction as well if the 'Rename' option is selected.
2. 'Select' button: Clicking this button will allow the user to select the desired directory for temporarily downloaded files.
3. Adjust the maximum number of retries to download an individual segment: Default 15.
4. Adjust the maximum number of threads for parallel downloading of segments: Range 1-16 inclusive Default 5.

Playlist Options
1. Use Preferred language for audio streams: Select preferred language for audio streams if the option is available from playlist.
2. Use Preferred language for subtitles streams: Select the preferred language for subtitle streams if the option is available from playlist.
3. Use automatic selection of resolution from playlist: Select the preferred resolution for the video if the option is available from the playlist.




    - Note: This software uses json files to swap information between processes. They will be created automatically by the software. Deleting them or editing them can cause the software to behave irradically.

```
# Error Reporting
Please keep in mind that this has not been tested on all platforms.  There are going to be issues.  If you find an error that you think I should be aware of please run under:
```
PYTHONFAULTHANDLER=1 python vsd.py
```
and include the output in your report, as well as what operation you were performing when the error happened.  Thank You.

