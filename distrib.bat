REM checkout %1 branch as it should be the only one to be published
git checkout %1

REM REM Create standalone executable
python -m PyInstaller --onefile --icon=grdviewer.ico --clean grdviewer.py

REM REM Backup last version of executable
mkdir P:\Antenna_models\GrdViewer\old
copy P:\Antenna_models\GrdViewer\grdviewer.exe P:\Antenna_models\GrdViewer\old\grdviewer.exe

REM REM Copy executable to Payload EU
copy .\dist\grdviewer.exe P:\Antenna_models\GrdViewer\