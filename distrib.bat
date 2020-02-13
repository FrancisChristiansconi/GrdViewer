REM checkout %1 branch as it should be the only one to be published
git checkout %1

REM Create standalone executable
python -m PyInstaller --onefile --icon=grdviewer.ico --clean grdviewer.py

REM Backup last version of executable
mkdir P:\Antenna_models\GrdViewer\old
copy P:\Antenna_models\GrdViewer\grdviewer-%1.exe P:\Antenna_models\GrdViewer\old\grdviewer-%1.exe

REM Copy executable to Payload EU
copy .\dist\grdviewer.exe P:\Antenna_models\GrdViewer\grdviewer-%1.exe
copy .\README.md P:\Antenna_models\GrdViewer\README-%1.md
