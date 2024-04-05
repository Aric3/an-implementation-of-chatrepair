@echo off
setlocal enabledelayedexpansion

set "source_folder=%CD%"

if "%~1" == "" (
    echo Please provide a list of numbers as arguments.
    exit /b
)

set "keep_files="
for %%i in (%*) do (
    set "keep_files=!keep_files! %%i.json"
)

echo Files to keep: %keep_files%

for %%f in (*.json) do (
    if "!keep_files: %%~nf.json=!" neq "!keep_files!" (
        echo Keeping file: %%f
    ) else (
        echo Deleting file: %%f
        del "%%f"
    )
)

echo Cleanup complete.
pause
