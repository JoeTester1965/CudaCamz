#!/usr/bin/python3

import configparser
import fileinput
from shutil import copyfile
import os
import sys
import stat
import time

def get_umask():
	umask = os.umask(0)
	os.umask(umask)
	return umask

def chmod_plus_x(path):
	os.chmod(
		path,
		os.stat(path).st_mode |
		(
			(
				stat.S_IXUSR |
				stat.S_IXGRP |
				stat.S_IXOTH
			)
			& ~get_umask()
		)
	)

config = configparser.ConfigParser()

if len(sys.argv) != 2:
	print("I need config file location as first paramater in command line")
	sys.exit(1)
	
config_file=sys.argv[1]
config.read(config_file)

cwd = os.getcwd()

startup_amendments = open("start.sh", 'w')

startup_amendments.write("#!/bin/sh \n")
startup_amendments.write("#The content below was created by configure.py \n\n")
startup_amendments.write("./stop.sh \n\n")


image_storage_dir = config["general"]["image_storage_dir"]
image_storage_dir_percent = config["general"]["image_storage_dir_percent"]
if not os.path.exists(image_storage_dir):
	os.makedirs(image_storage_dir)

video_storage_dir = config["general"]["video_storage_dir"]
video_storage_dir_percent = config["general"]["video_storage_dir_percent"]
if not os.path.exists(video_storage_dir):
	os.makedirs(video_storage_dir)

startup_amendments.write("nohup ./limit-directory-size.sh " + video_storage_dir  + " " + video_storage_dir_percent  + " 10  > /dev/null 2>&1 < /dev/null &\n")
startup_amendments.write("nohup ./limit-directory-size.sh " + image_storage_dir  + " " + image_storage_dir_percent + " 100  > /dev/null 2>&1 < /dev/null &\n\n")

global camerasAI
camerasAI = dict(config['camerasAI'])

global camerasREC
camerasREC = dict(config['camerasREC'])

copyfile("mediamtx/mediamtx.yml.original", "mediamtx/mediamtx.yml")

rtsp_amendments = open("mediamtx/mediamtx.yml", 'a')

for camera_details, uri in camerasAI.items():
	friendly_name, camera_type = camera_details.split(',')
	rtsp_amendments.write("  " + friendly_name + ":\n")
	rtsp_amendments.write("    source: " + uri + "\n")

for camera_details, uri in camerasREC.items():
	friendly_name, camera_type = camera_details.split(',')
	rtsp_amendments.write("  " + friendly_name + ":\n")
	rtsp_amendments.write("    source: " + uri + "\n")

rtsp_amendments.close()

using_rtsp_simple_proxy = int(config["general"]["using_rtsp_simple_proxy"])

if using_rtsp_simple_proxy:
	for camera_details, uri in camerasAI.items():
		friendly_name, camera_type = camera_details.split(',')
		if using_rtsp_simple_proxy:
			camerasAI[camera_details]="rtsp://127.0.0.1:8554/" + friendly_name
	for camera_details, uri in camerasREC.items():
		friendly_name, camera_type = camera_details.split(',')
		if using_rtsp_simple_proxy:
			camerasAI[camera_details]="rtsp://127.0.0.1:8554/" + friendly_name

	startup_amendments.write("cd " + cwd + "/mediamtx\n")
	startup_amendments.write("nohup ./mediamtx > /dev/null 2>&1 < /dev/null &\n")
	startup_amendments.write("\n")

recorder_amendments = open("recorder.sh", 'w')
recorder_amendments.write("#The content below was created by configure.py \n\n")
recorder_amendments.write("#!/bin/sh\n\n")

recorder_amendments.write("sleep 10\n\n")
recorder_amendments.write("while true; do\n\n")
recorder_amendments.write("NOW=$(date +\"%d-%m-%Y-%H-%M-%S\")\n\n")

for camera_details, uri in camerasAI.items():
	
	friendly_name, camera_type = camera_details.split(',')
	directory = config["general"]["image_storage_dir"] + friendly_name + "/"	
	if not os.path.exists(directory):
		os.mkdir(directory)

for camera_details, uri in camerasREC.items():

	friendly_name, camera_type = camera_details.split(',')
	directory = config["general"]["video_storage_dir"] + friendly_name + "/"	
	if not os.path.exists(directory):
		os.mkdir(directory)

	recorder_amendments.write("cd " + directory + " \n")
	filename = time.strftime("%d-%m-%Y-%H-%M-%S") + ".mp4"
	command_line = "nohup ffmpeg -i '" + uri + "' -acodec copy -vcodec copy $NOW.mp4  > /dev/null 2>&1 < /dev/null &"
	recorder_amendments.write(command_line + "\n\n")

recorder_amendments.write("sleep " + str(int(config["general"]["video_storage_slice_minutes"]) * 60) + "\n\n")
recorder_amendments.write("killall ffmpeg\n\n")
recorder_amendments.write("done\n\n")
recorder_amendments.close()

startup_amendments.write("cd " + cwd + "\n\n")

recording_all_video = int(config["general"]["recording_all_video"])
if recording_all_video:
	startup_amendments.write("nohup ./recorder.sh > /dev/null 2>&1 < /dev/null & \n\n")

mutelist_reminder_folder = config["general"]["mutelist_reminder_folder"]
if not os.path.exists(mutelist_reminder_folder):
	os.mkdir(mutelist_reminder_folder)

startup_amendments.write("nohup python3 CudaCam.py " + config_file + " > /dev/null 2>&1 < /dev/null &\n")
startup_amendments.close()

chmod_plus_x("start.sh")
chmod_plus_x("stop.sh")
chmod_plus_x("recorder.sh")
chmod_plus_x("limit-directory-size.sh")
