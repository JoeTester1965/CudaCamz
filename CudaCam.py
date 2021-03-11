#!/usr/bin/python3

import platform
import jetson.utils
import jetson.inference
import sys
import configparser
import sys
import time
from datetime import datetime
import json
import logging
import sqlite3
import paho.mqtt.client as mqtt
import shutil
import os
from PIL import Image, ImageFont, ImageDraw, ImageEnhance
import collections
import numpy
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

cameras = {}
rtsp_streams = {}
image_buffers = {}
object_mutelist_inside = {}
object_mutelist_outside = {}
event_state_filter = {}
basic_stats = {}
config = None

def read_config(config_file):

	global config
	config = configparser.ConfigParser()
	config.read(sys.argv[1])
	
	global cameras
	cameras = dict(config['cameras'])

	global using_rtsp_simple_proxy
	using_rtsp_simple_proxy = int(config["general"]["using_rtsp_simple_proxy"])

	global object_mutelist_inside
	for camera_details, uri in cameras.items():
		camera, type = camera_details.split(',')
		mutelist_key="object_mutelist_inside-" + camera 
		try:
			object_mutelist_inside[camera] = dict(config[mutelist_key])
		except:
			pass

	global object_mutelist_outside
	for camera_details, uri in cameras.items(): 
		camera, type = camera_details.split(',')
		mutelist_key="object_mutelist_outside-" + camera 
		try:
			object_mutelist_outside[camera] = dict(config[mutelist_key])
		except:
			pass

	global label_mutelist
	label_mutelist = config["label_mutelist"]["labels"]

	global ai_resize_factor
	ai_resize_factor = float(config["general"]["ai_resize_factor"])

	global camera_down_timeout_ms
	camera_down_timeout_ms = int(config["general"]["camera_down_timeout_ms"])

	global camera_starting_up_timeout
	camera_starting_up_timeout = int(config["general"]["camera_starting_up_timeout"])

	global label_alarmlist
	label_alarmlist = dict(config['label_alarmlist'])

	global label_percent_screenfill_min
	label_percent_screenfill_min = dict(config['label_percent_screenfill_min'])

	global image_storage_dir
	image_storage_dir = config["general"]["image_storage_dir"]

	global label_file_name
	label_file_name = config["general"]["label_filename"]

	global baseline_model_confidence
	baseline_model_confidence = config["general"]["baseline_model_confidence"]

	global label_name_index_array
	with open(label_file_name, "r") as filehandle:
		label_name_index_array = filehandle.read().splitlines()

	global logfile
	logfile = config["general"]["logfile"]

	global sqlite_db 
	sqlite_db = config["general"]["sqlite_db"]

	global video_storage_dir
	video_storage_dir = config["general"]["video_storage_dir"]

	global stats_update_seconds
	stats_update_seconds = int(config["general"]["stats_update_seconds"])

	global time_to_ignore_repeating_object_seconds
	time_to_ignore_repeating_object_seconds = int(config["general"]["time_to_ignore_repeating_object_seconds"])

	global bounding_box_fraction_for_repeating_object
	bounding_box_fraction_for_repeating_object = float(config["general"]["bounding_box_fraction_for_repeating_object"])

	global mutelist_reminder_folder
	mutelist_reminder_folder = config["general"]["mutelist_reminder_folder"]

	global logging_level_debug
	logging_level_debug = int(config["general"]["logging_level_debug"])

	global motion_resize_factor
	motion_resize_factor = float(config["motion_detect_settings"]["motion_resize_factor"])

	global frame_check_delta
	frame_check_delta = int(config["motion_detect_settings"]["frame_check_delta"])

	global movement_delta_threshold
	movement_delta_threshold = int(config["motion_detect_settings"]["movement_delta_threshold"])

	global movement_hits_threshold_percent 
	movement_hits_threshold_percent = float(config["motion_detect_settings"]["movement_hits_threshold_percent"])

	try:
		global mqtt_ip_address
		mqtt_ip_address = config["mqtt"]["mqtt_ip_address"]

		global mqtt_username 
		mqtt_username = config["mqtt"]["mqtt_username"]

		global mqtt_password
		mqtt_password = config["mqtt"]["mqtt_password"]

		global mqtt_topic
		mqtt_topic = config["mqtt"]["mqtt_topic"]
	except:
		pass

	try:
		global sender_email
		sender_email = config["smtp"]["sender_email"]

		global receiver_email
		receiver_email= config["smtp"]["receiver_email"]

		global smtp_password
		smtp_password= config["smtp"]["smtp_password"]

	except:
		pass

def test_event_needs_filtered(camera, eventclass, left, right, top, bottom, percent_screenfill): 
	
	global label_percent_screenfill_min

	if eventclass in label_mutelist:
		return eventclass

	try:
		if percent_screenfill < float(label_percent_screenfill_min[eventclass]):
			return "percent_screenfill"
	except:
		pass

	try:
		my_mutellist =  object_mutelist_inside[camera]
		for name, mutelist_coords in my_mutellist.items():
			mute_left,mute_right,mute_top,mute_bottom = mutelist_coords.split(',')
			mute_left = int(mute_left)
			mute_right = int(mute_right)
			mute_top = int(mute_top)
			mute_bottom = int(mute_bottom)
					
			if ( (left > mute_left) and (right < mute_right) and (top > mute_top) and (bottom < mute_bottom) ):
				return name
	except:
		pass

	try:
		my_mutellist =  object_mutelist_outside[camera]
		for name, mutelist_coords in my_mutellist.items():
			mute_left,mute_right,mute_top,mute_bottom = mutelist_coords.split(',')
			mute_left = int(mute_left)
			mute_right = int(mute_right)
			mute_top = int(mute_top)
			mute_bottom = int(mute_bottom)
					
			if ( (left < mute_left) and (right > mute_right) and (top < mute_top) and (bottom > mute_bottom) ):
				return name
	except:
		pass

	return ""

class BasicStatsAgainstThreshold:

	def __init__(self, threshold):
		self._threshold = threshold
		self._minumum = sys.float_info.max
		self._maximum = 0.0
		self._total = 0.0
		self._calls = 0
		self._count_events_exceeding_threshold = 0

	def reset(self):
		if self._threshold is None:
			return None
		self._minumum = 0.0
		self._maximum = 0.0
		self._total = 0.0
		self._calls = 0
		self._count_events_exceeding_threshold = 0

	def update(self, value):
		if self._threshold is None:
			return None
		self._calls = self._calls + 1	
		self._total = self._total + value
		if value < self._minumum:
			self._minumum = value
		if value > self._maximum:
			 self._maximum = value
		if value > self._threshold:
			self._count_events_exceeding_threshold = self._count_events_exceeding_threshold + 1
	
	def getstats(self): 
		if self._calls > 0:
			average = self._total / self._calls
		else:
			average = 0.0

		return self._minumum, self._maximum, average , self._count_events_exceeding_threshold, self._calls, self._threshold

class TimeoutCheck:

	def __init__(self, seconds_to_expire):
		self._start_time = time.perf_counter()
		self._seconds_to_expire = seconds_to_expire

	def reset(self):
		if self._start_time is None:
			return None
		self._start_time = time.perf_counter()

	def expired(self):
		if self._start_time is None:
			return None
		elapsed_time = time.perf_counter() - self._start_time
		if elapsed_time > self._seconds_to_expire:
			self._start_time = time.perf_counter()
			return True
		else:
			return False

class StatefulEventFilter:
	def __init__(self, left, right, top, bottom):
		self._left = int (left - left * bounding_box_fraction_for_repeating_object)
		self._right = int (right + right * bounding_box_fraction_for_repeating_object)
		self._top = int (top  - top  * bounding_box_fraction_for_repeating_object)
		self._bottom = int (bottom + bottom * bounding_box_fraction_for_repeating_object)
		self._TimeoutCheck = TimeoutCheck(time_to_ignore_repeating_object_seconds)
		self._just_initialised = True

	def filtered(self, left, right, top, bottom):
		if self._just_initialised == True:
			self._just_initialised = False
			return True, "Initialised"
		else:
			if (left > self._left) and (right < self._right) and (top > self._top) and (bottom < self._bottom):
				if self._TimeoutCheck.expired() == True:
					self._TimeoutCheck.reset()
					return True, "TimeoutCheck expired"
				else:
					return False, "TimeoutCheck not expired"
			else:
				self._left = int (left - left * bounding_box_fraction_for_repeating_object)
				self._right = int (right + right * bounding_box_fraction_for_repeating_object)
				self._top = int (top  - top  * bounding_box_fraction_for_repeating_object)
				self._bottom = int (bottom + bottom * bounding_box_fraction_for_repeating_object)
				self._TimeoutCheck.reset()
				return True, "Has moved"

def is_motion_detected(camera, image):

	global image_buffers
	global frame_check_delta
	global movement_delta_threshold 
	global movement_hits_threshold_percent 
	global basic_stats
	global motion_resize_factor

	if not camera in image_buffers:
		image_buffers[camera] = collections.deque()
		
	image_bw = jetson.utils.cudaAllocMapped(width = image.width, height = image.height, format="gray8")	
	jetson.utils.cudaConvertColor(image, image_bw)
	jetson.utils.cudaDeviceSynchronize()

	resized_image_bw = jetson.utils.cudaAllocMapped(	width=int(image.width * motion_resize_factor),
														height=int(image.height * motion_resize_factor),
														format="gray8")

	jetson.utils.cudaResize(image_bw, resized_image_bw)
	jetson.utils.cudaDeviceSynchronize()
	del image_bw

	numpy_image_bw = jetson.utils.cudaToNumpy(resized_image_bw)
	jetson.utils.cudaDeviceSynchronize()

	image_buffers[camera].append(numpy_image_bw)

	if len(image_buffers[camera]) > (frame_check_delta + 1):
		
		stale_image=image_buffers[camera][0]
		del stale_image
		image_buffers[camera].popleft()

		delta = numpy.absolute(numpy.subtract(	image_buffers[camera][len(image_buffers[camera]) - 1 - frame_check_delta].astype(numpy.int16), 
												image_buffers[camera][len(image_buffers[camera]) - 1].astype(numpy.int16)))

		movement = delta >= movement_delta_threshold  

		movement_hits = len(delta[movement])

		movement_hits_percent = float(movement_hits / (resized_image_bw.width * resized_image_bw.height)) * 100

		basic_stats[camera].update(movement_hits_percent)

		if movement_hits_percent >  movement_hits_threshold_percent:
			return movement_hits_percent
	
	return False

def send_smtp_message(camera, eventclass, image):

	subject = camera
	body = eventclass
	message = MIMEMultipart()
	message["From"] = sender_email
	message["To"] = receiver_email
	message["Subject"] = subject
	
	message.attach(MIMEText(body, "plain"))
	
	filename = image
	with open(filename, "rb") as attachment:
		part = MIMEBase("application", "octet-stream")
		part.set_payload(attachment.read())

	encoders.encode_base64(part)

	part.add_header(
		"Content-Disposition",
		f"attachment; filename= {filename}",
	)

	message.attach(part)
	text = message.as_string()

	context = ssl.create_default_context()
	with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
		server.login(sender_email, smtp_password)
		server.sendmail(sender_email, receiver_email, text)

def test_event_needs_alarmed(confidence, eventclass): 
	
	retval = False
	
	try:
		configured_confidence_threshold = float(label_alarmlist[eventclass])
		if confidence > float(configured_confidence_threshold):
			retval = True
	except:
		pass

	return retval

def GetBestDetection(camera, detections, detection_image_size):

	best_unfiltered_detection = None

	for detection in detections:

		index			= detection.Instance
		detected_class	= int(detection.ClassID)
		eventclass		= label_name_index_array[detected_class]
		confidence		= round(detection.Confidence, 2)
		left			= int(detection.Left)
		right			= int(detection.Right)
		top				= int(detection.Top)		
		bottom			= int(detection.Bottom)

		percent_screenfill = float((((right - left) * (bottom - top)) / detection_image_size) * 100)	

		needs_filtered_reason  = test_event_needs_filtered(camera, eventclass, left, right, top, bottom, percent_screenfill)

		if needs_filtered_reason:
			logger.debug("TESTING WOULD HAVE Filtered out event reason '%s', %s-%s : %.2f %d,%d,%d,%d", 
								needs_filtered_reason, camera, eventclass, confidence, left, right, top, bottom)
			continue

		if not best_unfiltered_detection:
			best_unfiltered_detection = detections[index]

		needs_alarmed = test_event_needs_alarmed(confidence, eventclass)

		if needs_alarmed:
			# a detection event needs alarmed so take that one without looking any further
			return best_unfiltered_detection

		if not best_unfiltered_detection:
			best_unfiltered_detection = detections[index]
		else:
			if confidence > round(best_unfiltered_detection.Confidence, 2):
				best_unfiltered_detection = detections[index]

	return best_unfiltered_detection

def check_cameras_on_startup():
	for camera, jetson_videoSource in rtsp_streams.items():
		try:
			height = jetson_videoSource.GetHeight()
			if not height:
				logger.error("Camera %s is not up, removing. Do you need to re-run configure.py and start.sh?", camera)
				rtsp_streams[camera] = None
		except:
			pass

	number_of_cameras_up = 0
	for camera in rtsp_streams:
		if rtsp_streams[camera] is not None:
			number_of_cameras_up = number_of_cameras_up + 1
	if number_of_cameras_up == 0:
		logger.critical("No cameras are operational after inspection on startup, may as well shut down.")
		raise SystemExit
	return

# Initialisation

if len(sys.argv) != 2:
	print("I need config file location as first paramater in command line")
	sys.exit(1)

read_config(sys.argv[1]) 

if logging_level_debug > 0:
	logging_level = logging.DEBUG
else:
	logging_level = logging.INFO

logging.basicConfig(    handlers=[
								logging.FileHandler(logfile),
								logging.StreamHandler()],
						format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
						datefmt='%Y-%m-%d:%H:%M:%S',
						level=logging_level)

logger = logging.getLogger(__name__)

logger.info("CudaCam started")

for camera_details, uri in cameras.items():
	if using_rtsp_simple_proxy:
		friendly_name, camera_type = camera_details.split(',')
		cameras[camera_details]="rtsp://127.0.0.1:8554/" + friendly_name
		logger.info("Remapped %s to %s as using_rtsp_simple_proxy set", uri, cameras[camera_details])

for camera_details, uri in cameras.items():
	friendly_name, camera_type = camera_details.split(',')
	basic_stats[friendly_name] = BasicStatsAgainstThreshold(movement_hits_threshold_percent)

for camera_details, uri in cameras.items():
	friendly_name, camera_type = camera_details.split(',')
	input_codec_string = "----input-codec=" + camera_type
	rtsp_streams[friendly_name] = jetson.utils.videoSource(uri, ['me', input_codec_string])

logger.info("Starting inference engine, can take a while")
net = jetson.inference.detectNet("ssd-mobilenet-v2", baseline_model_confidence)
logger.info("Inference engine is up")

sqlite_connection = sqlite3.connect(sqlite_db)
sqlite_cursor = sqlite_connection.cursor() 

create_sqlite_event_table = '''CREATE TABLE IF NOT EXISTS events (
									camera text NOT NULL,
									timestamp text NOT NULL,
									eventclass text NOT NULL,
									confidence real NOT NULL,
									alarmed integer NOT NULL,
									left integer NOT NULL,
									right integer NOT NULL,
									top integer NOT NULL,
									bottom integer NOT NULL,
									image_filename text NOT NULL
								)'''

try:
	sqlite_cursor.execute(create_sqlite_event_table)
except Exception as e:
	logging.error('Exception occured: %s' % e, exc_info=True)
	pass

if config.has_section("mqtt"):
	mqtt_client = mqtt.Client()
	mqtt_client.username_pw_set(mqtt_username, mqtt_password)
	try:
		mqtt_client.connect(mqtt_ip_address, 1883)
	except:
		logger.error("Cannot connect to your MQTT server")

StatsTimeoutCheck = TimeoutCheck(stats_update_seconds)
images_processed=0

logger.info("Starting cameras and getting test images for %s, can take a while", mutelist_reminder_folder)

for name, jetson_videoSource in rtsp_streams.items():
	try:
		image = jetson_videoSource.Capture(format='rgb8', timeout = camera_starting_up_timeout*1000)
		resized_image = jetson.utils.cudaAllocMapped(	width=int(image.width * ai_resize_factor),
															height=int(image.height * ai_resize_factor),
															format=image.format)
		jetson.utils.cudaResize(image, resized_image)
		jetson.utils.cudaDeviceSynchronize()

		try:
			filename = mutelist_reminder_folder + "/" + name + ".jpg"
			jetson.utils.saveImageRGBA(filename , resized_image, resized_image.width, resized_image.height)
			jetson.utils.cudaDeviceSynchronize()
			source_image = Image.open(filename)
			draw = ImageDraw.Draw(source_image)

			try:
				mutelist_inside = object_mutelist_inside[name]
				for mutelist_name, mutelist in mutelist_inside.items():
					left,right,top,bottom = mutelist.split(',')
					draw.rectangle(((int(left), int(top)), (int(right), int(bottom))), width=3, outline="green")
					draw.text(((int(left)+int(right))/2, (int(top)+int(bottom))/2), mutelist_name, fill="green")
			except:
				pass

			try:
				mutelist_outside = object_mutelist_outside[name]
				for mutelist_name, mutelist in mutelist_outside.items():
					left,right,top,bottom = mutelist.split(',')
					draw.rectangle(((int(left), int(top)), (int(right), int(bottom))), width=3, outline="red")
					draw.text(((int(left)+int(right))/2, (int(top)+int(bottom))/2), mutelist_name, fill="red")
			except:
				pass

			source_image.save(filename, "JPEG")
		except:
			pass

		del resized_image

	except:
		pass

# Remove cameras that do not come up on startup

check_cameras_on_startup()

# Main loop

while True:
	if StatsTimeoutCheck.expired():
		logger.info("Processed %d images in the past %d seconds",images_processed, stats_update_seconds)
		images_processed = 0
		for camera, jetson_videoSource in rtsp_streams.items():
			minimum,maximum,average,count_events_exceeding_threshold,count,threshold = basic_stats[camera].getstats()
			logger.debug("%s had %d images from %d exceeding motion threshold %.2f : min %.2f , max  %.2f, average %.2f", 
							camera, count_events_exceeding_threshold, count, threshold, minimum, maximum, average)
			basic_stats[camera].reset()

	for camera, jetson_videoSource in rtsp_streams.items():
		try:
			image = jetson_videoSource.Capture(format='rgb8', timeout = camera_down_timeout_ms)
		except:
			logger.debug("Timeout in getting image from %s", camera)
			try:
				if not jetson_videoSource.IsStreaming():
					logger.error("Camera %s is not up, removing.", camera)
					rtsp_streams[camera] = None
					number_of_cameras_up = 0
					for camera in rtsp_streams:
						if rtsp_streams[camera] is not None:
							number_of_cameras_up = number_of_cameras_up + 1
					if number_of_cameras_up == 0:
						logger.critical("No cameras are operational, have called helpdesk, they suggest trying a reboot")
						raise SystemExit
			except:
				pass
			continue

		images_processed = images_processed + 1

		resized_image = jetson.utils.cudaAllocMapped(	width=int(image.width * ai_resize_factor),
															height=int(image.height * ai_resize_factor),
															format=image.format)

		jetson.utils.cudaResize(image, resized_image)
		jetson.utils.cudaDeviceSynchronize()

		movement = is_motion_detected(camera, resized_image)

		if movement:

			logger.debug("Got movement value %.2f percent from %s", movement, camera)

			detections = net.Detect(resized_image, resized_image.width, resized_image.height, 'box,labels,conf')	
					
			best_unfiltered_detection =	GetBestDetection(camera, detections, resized_image.size)
				
			if best_unfiltered_detection:	

				detected_class	= int(best_unfiltered_detection.ClassID)
				eventclass		= label_name_index_array[detected_class]
				confidence		= round(best_unfiltered_detection.Confidence, 2)
				left			= int(best_unfiltered_detection.Left)
				right			= int(best_unfiltered_detection.Right)
				top				= int(best_unfiltered_detection.Top)		
				bottom			= int(best_unfiltered_detection.Bottom)

				if not camera+eventclass in event_state_filter:
					event_state_filter[camera+eventclass] = StatefulEventFilter(left, right, top, bottom)
					
				can_use_event, can_use_event_message = event_state_filter[camera+eventclass].filtered(left, right, top, bottom) 

				if can_use_event:
		
					timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S-%f")
					image_path = image_storage_dir + camera + "/"				
					image_filename	= timestamp + ".jpg"	
			
					new_image_filename = image_filename.split('-', 3)[-1] 
					split = image_filename.split('-', 3)
					image_filename_before_date  = split[0] + "-" + split[1] + "-" + split[2] 
					new_image_path =  image_path +  image_filename_before_date + "/"

					needs_alarmed = test_event_needs_alarmed(confidence, eventclass)

					if not needs_alarmed:		
						new_image_path = new_image_path + "not_alarmed/"
	
					image_location = new_image_path + new_image_filename

					os.makedirs(os.path.dirname(new_image_path), exist_ok=True)

					jetson.utils.saveImageRGBA(image_location, resized_image, resized_image.width, resized_image.height)
					jetson.utils.cudaDeviceSynchronize()
				
					sqlite_cursor.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?)" , 
							(camera, timestamp, eventclass , confidence, needs_alarmed,  
								left, right, top, bottom, image_location))

					sqlite_connection.commit()

					if needs_alarmed:
							
						message_needs_alarmed = camera + " : " + eventclass

						if config.has_section("mqtt"):
							mqtt_client.publish(mqtt_topic, message_needs_alarmed) 

						if config.has_section("smtp"):
							send_smtp_message(camera, eventclass, image_location)

					logger.info("Event '%s' : %s - %s, confidence %.2f : %d,%d,%d,%d", 
									can_use_event_message, camera, eventclass, confidence, left, right, top, bottom)	
				else:
					logger.debug("Filtered out event in StatefulEventFilter reason '%s', alarmed %d : %s - %s:%.2f %d,%d,%d,%d", 
								can_use_event_message, needs_alarmed, camera, eventclass, confidence, left, right, top, bottom)		

		del resized_image
