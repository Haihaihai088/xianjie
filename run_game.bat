@echo off
cd /d "%~dp0"

echo ==================================== > "launch_log.txt"
echo Launch time: %date% %time% >> "launch_log.txt"
echo ==================================== >> "launch_log.txt"
echo . >> "launch_log.txt"

echo Starting Heavenly Tribulation...

python main.py >> "launch_log.txt" 2>&1
if %errorlevel% neq 0 (
    python3 main.py >> "launch_log.txt" 2>&1
)

echo . >> "launch_log.txt"
echo Exit code: %errorlevel% >> "launch_log.txt"
echo ==================================== >> "launch_log.txt"

if %errorlevel% neq 0 (
    type "launch_log.txt"
    echo .
    echo Game crashed. See launch_log.txt for details.
    pause
)
