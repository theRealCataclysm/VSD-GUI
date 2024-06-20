# About
This is a GUI for clitics vsd project available at:
>[clitic / vsd](https://github.com/clitic/vsd)


It is written in python and uses pysides2 to create the UI elements. This is a work in progress, some features have not been implemented even though the structure is in place for it.


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
- [ ] Enable auto capture from queue.
- [X] Enable Download/save through UI.
- [X] Create queue system for downloads.
- [ ] Allow auto downloading from queue.
- [X] Display of download status information.
- [X] Graphical progress bars.
- [X] Enable auto renaming of files after download completes.
- [X] Enable permanent user set working directory.
- [X] Enable usage of all flags.
- [ ] Create a pyinstaller release of the software.

# Error Reporting
Please keep in mind that this is still a work in progress.  There are going to be issues.  If you find an error that you think I should be aware of please run under:
```
PYTHONFAULTHANDLER=1 python vsd.py
```
and include the output in your report, as well as what operation you were performing when the error happened.  Thank You.

