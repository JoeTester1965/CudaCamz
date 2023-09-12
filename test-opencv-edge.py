import cv2
import numpy as np;

cap = cv2.VideoCapture("/home/jetsondev/Desktop/test1.mp4")

ret, frame = cap.read()
firstFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
firstFrame = cv2.GaussianBlur(firstFrame, (21, 21), 0)

while cap.isOpened():

    ret, frame = cap.read()
    if ret:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        frameDelta = cv2.absdiff(firstFrame, gray)
        thresh = cv2.threshold(frameDelta, 5, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
     
        cv2.imshow("Source", frame)

        cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
        for c in cnts:
            # Highlight contours
            cv2.drawContours(thresh, [c], -1, (36,255,12), 3)
            x,y,w,h = cv2.boundingRect(c)
            cv2.rectangle(thresh,(x,y),(x+w,y+h),(255,255,255),2)

        cv2.imshow("Motion contours", thresh)

        firstFrame = gray

        c = cv2.waitKey(1)
        if c & 0xFF == ord('q'):
            break
    else:
        break

cap.release()