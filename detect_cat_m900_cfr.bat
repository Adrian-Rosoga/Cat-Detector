@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%" >nul

if exist "config.env" (
	for /f "usebackq tokens=1,* delims==" %%A in ("config.env") do (
		set "KEY=%%A"
		set "VAL=%%B"
		if defined KEY (
			if not "!KEY:~0,1!"=="#" (
				set "!KEY!=!VAL!"
			)
		)
	)
)

if exist "secrets.env" (
	for /f "usebackq tokens=1,* delims==" %%A in ("secrets.env") do (
		set "KEY=%%A"
		set "VAL=%%B"
		if defined KEY (
			if not "!KEY:~0,1!"=="#" (
				set "!KEY!=!VAL!"
			)
		)
	)
)

if not defined TAPO_USERNAME (
	echo Missing TAPO_USERNAME in secrets.env
	popd >nul
	exit /b 1
)

if not defined TAPO_PASSWORD (
	echo Missing TAPO_PASSWORD in secrets.env
	popd >nul
	exit /b 1
)

if not defined CAT_DETECTOR_MODEL (
	set "CAT_DETECTOR_MODEL=yolo26n_ov"
)

if not defined CAT_DETECTOR_DEVICE (
	set "CAT_DETECTOR_DEVICE=CPU"
)

if not defined SNAPSHOT_COOLDOWN (
	set "SNAPSHOT_COOLDOWN=2"
)

if not defined TAPO_IP (
	echo Missing TAPO_IP in config.env
	popd >nul
	exit /b 1
)

REM Activate virtual environment if it exists
if exist "%SCRIPT_DIR%\.venv\Scripts\activate.bat" (
	call "%SCRIPT_DIR%\.venv\Scripts\activate.bat"
)

echo.
echo.
echo Starting the Cat Detector (OpenVINO CPU Optimized)...
echo.
echo.

python cat_detector.py ^
	--model "%CAT_DETECTOR_MODEL%" ^
	--device "%CAT_DETECTOR_DEVICE%" ^
	--conf 0.20 ^
	--imgsz 1280 ^
	video ^
	--tapo-ip %TAPO_IP% ^
	--tapo-username "%TAPO_USERNAME%" ^
	--tapo-password "%TAPO_PASSWORD%" ^
	--tapo-profile main ^
	--capture-buffer-size 1 ^
	--frame-skip 1 ^
	--display ^
	--beep-cooldown 1.5 ^
	--snapshot-cooldown "%SNAPSHOT_COOLDOWN%" ^
	--telegram-send ^
	--telegram-config telegram-send.conf ^
	--no-alert-person ^
	--no-alert-bird ^
	--no-alert-dog ^
	--no-alert-bear %*
set "EXIT_CODE=%ERRORLEVEL%"

popd >nul
exit /b %EXIT_CODE%
