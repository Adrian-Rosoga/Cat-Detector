python cat_detector.py --model yolo26n video --tapo-ip 192.168.1.111 --tapo-username admin --tapo-password YOUR_PASSWORD --tapo-profile main --display

python cat_detector.py --model yolo26s video --tapo-ip 192.168.1.111 --tapo-username tapocam --tapo-password ccnfrnfd444 --tapo-profile main --display

# Optional session default model in PowerShell:
# $env:CAT_DETECTOR_MODEL="yolo26s"

# Use this
python cat_detector.py --model yolo26s video --tapo-ip 192.168.1.111 --tapo-username tapocam --tapo-password ccnfrnfd444 --tapo-profile main --display --beep-cooldown 1.5

(.venv) PS C:\# PROJECTS #2\Cat Detector> .\run_cat_detector.bat
usage: cat_detector.py [-h] [--model MODEL] [--conf CONF] {image,video,batch} ...
cat_detector.py: error: the following arguments are required: mode

.\run_cat_detector.bat --model yolo26s video --tapo-ip 192.168.1.111 --tapo-username tapocam --tapo-password ccnfrnfd444 --tapo-profile main --display --beep-cooldown 1.5
