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
