# 35. Remove detect.cat.vbs and detect_cat_launcher.bat (video window now opens maximized, watermark shows all controls)
36. Rename "Snapshots - Hits and some misses" to "Some hits, some misses".
37. Fix watermark flicker so it is always visible.
38. Update documentation to reflect these changes and new options (dog/bear disable, video controls, etc).
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
# 53. Make the text in the popup window just smaller enough to fit the current window size
# 54. Update activity, prompts and readme. Commit and sync.
