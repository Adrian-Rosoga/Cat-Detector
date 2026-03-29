Set objArgs = WScript.Arguments
msg = "Starting the Cat Detector"
title = "Cat Detector"
Set objShell = CreateObject("WScript.Shell")
objShell.Popup msg, 10, title, 64
