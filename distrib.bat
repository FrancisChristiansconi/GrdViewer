REM Create standalone executable
python -m PyInstaller --onefile --icon=grdviewer.ico --clean grdviewer.py

REM Backup last version of executable
mkdir P:\Antenna_models\GrdViewer\old
copy P:\Antenna_models\GrdViewer\grdviewer.exe P:\Antenna_models\GrdViewer\old\grdviewer.exe

REM Copy executable to Payload EU
copy .\dist\grdviewer.exe P:\Antenna_models\GrdViewer\