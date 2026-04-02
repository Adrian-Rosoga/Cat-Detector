# Prompts Used To Create This Utility

Ordered list of user prompts used during development.

1. Create an utility that uses yolo26 and that is able to identify whether a cat exists in a photo or within a video stream.
2. Create a virtual env if necessary, install all dependencies and test the utility on the photos in the C:\# PROJECTS #2\Cat Detector\Cat Photo Samples folder
3. Do it
4. Add batch command
5. Add support for accessing the video stream from a Tapo C310 webcam running at a configurable IP. Test it with IP 192.168.1.111.
6. Try again using username tapocam and password DUMMY. Add the credentials in a secrets file.
7. When running on video stream put the detection message on the bottom left corner of the stream. Write with red font on a pale yellow background. Add a beep-beep alert when a cat is detected.
8. Move the detection banner to the left side on the midlle.
9. The displayed video screen is truncated, it does not cover the entire video area. Fix that.
10. Add toggle. By deafult I want to see the entire video stream with no cropping.
11. Make the font in the banner 3 times bigger. Change the alert to a 1 khz tone that lasts 2 seconds.
12. When an animal, cat or else, is detected, take a snapshot of the stream image and save it into a timestamped file.
13. Add configurable support for sending the snaphots via telegram-send using the token 1234567890:DUMMYbAaCxiT2NUuhcbhql80RMSNfPRUAsQ. Add the token to secrets.env.
14. Change of plan, create a telegram-send.conf file from where to get the token and chat-id as following: [telegram]
    token = 1234567890:DUMMYbAaCxiT2NUuhcbhql80RMSNfPRUAsQ
    chat_id = 1234567890
15. Send a test image via Telegram to test continuity, I have received none so far.
16. Try now.
17. Create a .bat file I can use to run the utility.
18. Create a file with all the prompts used in order to create this utility.
19. What better model than yolo26n can I use?
20. Setup the utility to use a configurable model, for now yolo26n and yolo26s.
21. Test with yolo26s.
22. Run the second test.
23. Ok, do it.
24. Make the program more resilient to errors like the following one that crashed it: [h264] error while decoding MB ... bytestream -7.
25. Run it.
26. Verify the program detects cats, other animals, birds and people and that it sends the snapshot via Telegram in each of these cases.
27. Remove the 3 directories starting with test_outputs from git without deleting the files.
28. Make detect_coco.bat read the tapo username and password from secrets.env.
29. Why is CAT_DETECTOR_MODEL in secrets.env? It is not a secret. Consider removing it.
30. Yes, add config.env.
31. The program is slow, probably when sending the snapshots by Telegram. Consider sending snapshots from a separate thread.
32. Do all 3 of them.
33. There is a small cat right now but not detected. Verify and fix.
34. Git ignore MY_README and then commit all.
35. Verify and update detect_coco.bat to use the best options.
36. Replace the 1 second 1000 Hz alert tone with a much shorter, more pleasant and non intrusive audio alert.
37. There is a false detection of a train right now. Remove train detection, not interested in it.
38. There is a small cat standing upright now but it's detected as dog or a bird.
39. Fix it only there is a safe way.
40. Update README and PROMPTS_USED.
41. Commit.
42. Some of the prompts have not be entred in prompts_used. Why? Review them and update prompts_used.md with all prompts used from the beginning of the activity.
43. Create a summary file with all activities, issues, fixes and enhancements from the very beginning of the activity until now.
44. There is about a 20 second delay for the video stream, it's not real time. How can that be explained and reduced?
45. UpdatePROMPTS_USED.md, README.md and ACTIVITY_SUMMARY.md. Commit and push after that.
46. The "NO CAT" banner is flickering. Fix that, if not revert the last change that was about decreasing the stream latency.
47. Banner is stable.
48. Do it. (commit the fix)
49. Push the branch.
50. Add cleaning the oldest photos in the snapshots directory after reaching a configurable number of files in it. The default is 1000 files, add this as a new config in config.env. Do this in a separate thread if you think it's better.
51. Create copies of secrets.env and telegram-send.conf, add .EXAMPLE as suffix to the new files, then obfuscate the passwords and the other secrets in them. Want this so a new user knows the format of the configs.
52. Add the 2 new files to git. Also, the snapshots dir in gitignored, however it still shows up in github. Fix that. Update prompts, activity and readme files, commit everything and sync.
53. Make the text in the popup window just smaller enough to fit the current window size.
54. Update activity, prompts and readme. Commit and sync.
55. Add functionality to record the video stream when pressing 'r' in the video capture window and stop the video recording when pressing 's'.
56. Save the recordings in a directory named recordings within the current directory.
57. Add functionality to save a snapshot of the video screen plus all the video screen captions and overlays when the user presses the p key. These should be saved in a directory named snapshots_manual.
58. Add a visual cue to the bottom left of the video stream when recording is active.
59. Instead of using s to control recording, make instead recording toggle when pressing r.
60. Save snapshot when using s instead of p.
61. When taking the snapshot alert about that with popup window that dissapears after a short interval.
62. Move the recording cue a few mms up because it overlays with the existing help banner at the bottom left of the window.
63. Use the hints of window control for the helper on the bottom left of the screen.
64. Make the REC visual cue blink to indicate recording.
65. Move the helper and the REC cue on the bottom left a few mms up.
66. Update ACTIVITY_SUMMARY, PROMPTS_USES by appending to the end of them.

## Session: OpenVINO Optimization and M900-CFR Benchmarking

67. Get the changes from github.
68. Overwrite the local change.
69. Install openVINO and benchmark to see if inference running on GPU is better than the current one on CPU.
70. Do it.
71. Don't change config.env, but create a copy of detect_cat.bat, name it detect_cat_m900_cfr.bat and add to it the 2 recommended settings.
72. Append to the end of the files README.md and ACTIVITY_SUMMARY.md what has been done, adding the important detail that the optimization has been performed for the M900-CFR computer. Add the details of the machine CPU and GPU.
73. Append the necessary info, i.e. prompts used to PROMPTS_USED.md. Add info from other sessions as well if possible to bring the file as up to date as possible.
74. mp4 doesn't play. Why? Fix.
75. The mp4 ercording do not play in the mpeg4 extension. Why?
76. Do it.
77. The REC visual cue doesn't blink smoothly. Fix.
78. These errors appear in the log when recording. Why? Fix.
79. Same error in the log: (.venv) PS C:\# PROJECTS #2\Cat Detector> ./detect_cat.bat ...
80. The error went away but the last mp4 is no longer playable on the mpeg4 viewer. Fix that.
81. Update ACTIVITY_SUMMARY, PROMPTS_USES by appending to the end of them.
82. Use the same bolder font for the "CAT DETECTED" banner as for "NO CAT YET".
83. Record also audio.
84. Audio should already be in the video stream from the webcam. Don't think it exposes a microphone.
85. Still no audio and getting this error in the log: (.venv) PS C:\# PROJECTS #2\Cat Detector> ./detect_cat.bat ... interactive_recording_audio_warning=ffmpeg not found in PATH; source audio capture disabled
86. I don't see a .wav file, was one supposed to appear or is the audio embedded in the video stream?
87. Still no audio as expected, fix. Here is the log: (.venv) PS C:\# PROJECTS #2\Cat Detector> ./detect_cat.bat ... interactive_recording_audio_saved=... interactive_recording_muxed=...
88. This is what Gemini says about the webcam: RTSP (Real-Time Streaming Protocol): This is the most common way to get audio into a DIY "cat detector" setup. The audio is multiplexed (interleaved) directly into the video stream. URL Format: rtsp://[Your-Camera-IP]/stream1 Audio Path: In this stream, the video is H.264 and the audio is G.711. They arrive at your PC at the same time.
89. Actually the sound worked before. Now no sound and the log says: (.venv) PS C:\# PROJECTS #2\Cat Detector> ./detect_cat.bat ... interactive_recording_audio_warning=source audio capture exited immediately (source may not expose an audio stream)
90. No audio. It used to work at some moment in a previous iteration. Log is: (.venv) PS C:\# PROJECTS #2\Cat Detector> ./detect_cat.bat ... interactive_recording_audio_started=...wav ... interactive_recording_stopped=...mp4
91. Still no audio. Log is: Starting the Cat Detector... ... interactive_recording_audio_warning=audio capture process exited with code 2880417800 ... audio sidecar was not created ...
92. It works, can hear audio. Log is: (.venv) PS C:\# PROJECTS #2\Cat Detector> ./detect_cat.bat ... interactive_recording_audio_saved=...wav ... interactive_recording_audio_gain_db=24.0 ... interactive_recording_muxed=...mp4
93. Do it.
94. Add audio also to the video stream on the PC, not only in the recording. Add a toggle to be able to turn it on or off.
95. Audio continues to work on recordings but I hear nothing in the live video stream on pc.
96. Didn't work: (.venv) PS C:\# PROJECTS #2\Cat Detector> ./detect_cat.bat ... AttributeError: 'FFmpegPipeAudioPlayer' object has no attribute 'poll'
97. Now the audio during the live stream works well, but there is no audio in the mp4 recording. That used to work. Log: Starting the Cat Detector... ... interactive_recording_audio_warning=audio capture process exited with code 4294967295 ... audio sidecar was not created ...
98. Both audio in the live stream and in the mp4 work now. Just make the audio in the audio stream louder and provide a config to increase/decrease live audio.
99. Append to the end of ACTIVITY_SUMMARY.md a detailed summary of all what was tried, what worked and what not. Then update the prompts used by appending to the end of PROMPTS_USED.md.
