#!/usr/bin/python3
import cv2
import numpy as np;
import time

pixel_delta_threshold = 10
gaussian_kernel_size = 13

caps = {}
frame = {}
lastFrame = {}

cameras =   [ 
                ["video1", "/home/jetsondev/Desktop/D1-10fps.mp4"]
            ]

for camera,camera_uri in cameras:
    caps[camera] = cv2.VideoCapture(camera_uri)
    retval, frame[camera] = caps[camera].read()
    lastFrame[camera] = cv2.cvtColor(frame[camera], cv2.COLOR_BGR2GRAY)
    lastFrame[camera] = cv2.GaussianBlur(lastFrame[camera], (gaussian_kernel_size, gaussian_kernel_size), 0)

prev_frame_time = 0
new_frame_time = 0
  
while True:
    
    for camera,camera_uri in cameras:
        retval, frame[camera] = caps[camera].read()
    
    for camera,camera_uri in cameras:
        gray = cv2.cvtColor(frame[camera], cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (gaussian_kernel_size,gaussian_kernel_size), 0)

        frameDelta = cv2.absdiff(lastFrame[camera], gray)
        lastFrame[camera] = gray
        thresh = cv2.threshold(frameDelta, pixel_delta_threshold, 255, cv2.THRESH_BINARY)[1]

        cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
        for c in cnts[:1]:
            x,y,w,h = cv2.boundingRect(c)
            cv2.rectangle(frame[camera],(x,y),(x+w,y+h),(0,0,255),3)

    for camera,camera_uri in cameras:
        cv2.imshow(camera, frame[camera])

    new_frame_time = time.time()
    fps = 1/(new_frame_time-prev_frame_time)
    prev_frame_time = new_frame_time
    fps = int(fps)
    fps = str(fps)
    print(fps)

    c = cv2.waitKey(1)