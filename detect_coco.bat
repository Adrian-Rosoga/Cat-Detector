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
	set "CAT_DETECTOR_MODEL=yolo26s"
)

call .\run_cat_detector.bat --model "%CAT_DETECTOR_MODEL%" --conf 0.10 --imgsz 1280 video --tapo-ip 192.168.1.111 --tapo-username "%TAPO_USERNAME%" --tapo-password "%TAPO_PASSWORD%" --tapo-profile main --display --beep-cooldown 1.5 --telegram-send --telegram-config telegram-send.conf %*
set "EXIT_CODE=%ERRORLEVEL%"

popd >nul
exit /b %EXIT_CODE%