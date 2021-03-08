# CudaCam

Inspired by  https://github.com/dusty-nv/jetson-inference/ 

Did this as a lockdown project.

The neighbourhood cats, dogz and other more interesting wildlife are now more transparent ...

CudaCam runs on a Nvidia Jetson Nano giving your home or small office a bespoke well-filtered AI camera event generator & recording appliance on a budget.

All without selling your soul to GAFA  (I hope).

Can record all incoming video as well in case something goes down.

Uses a very network efficient [RTSP proxy](https://github.com/aler9/rtsp-simple-server) for live monitoring as well with something like VLC media player.

If using cheap imported IP cameras, make sure you change the password and turn all the cloud stuff off with the configuration sofwtare.

Some of that uses an IE active X control ...

You will need some basic Linux skills and a wee bit of time initially looking at the application output
to weed out false positives. More advice given in the example config file config.txt.

Samba is useful if you want to access events, images and videos as defined by the locations in your config.txt file on the Jetson from a PC, but I tend to use WinSCP.

## Important note

The fist time the program is run using start.sh in step 4. below, it will take five minutes of more for the AI model to be initially compiled.
 
After that and on subsequent runs it will only take about thirty seconds to load from a cache.

Be patient!

## Installing and running

1. Put your camera URIs and sutiable image and video pathnames in config.txt

2. bash ./install-depends.sh

3. python3 ./configure.py ./config.txt 

4. bash ./start.sh

5. Look at what you see in the images folders and logfiles and database (I use DBbrowser for SQLite) and tune config.txt to remove any false positives you get.

6. Use ./start.sh to start and ./stop.sh to stop.

## Basic operational outline

```python
For all cameras
	Get a frame
		Has any motion been detected in that frame ?
			Are there any unfilered AI detection events in that frame ?
				Does any event in this frame meet any given alarm criteria?
					Alarm (MQTT and SMTP email)
```

## Performance

Experiment - Four cameras attached at 720p, 20fps - Constant Bit Rate. Ambient temperature was 15C. No cooling. 

Measured using [jtop](https://pypi.org/project/jetson-stats/)

power plan mode		1		2.5A	AO (alws-on) temp 52C	~190 images per second		
power plan mode		0		6.0A	AO (alws-on) temp 66C	~310 images per second		

Note to change power plan mode permanently: 

sudo nano /etc/nvpmodel.conf		change PM_CONFIG DEFAULT to 1 (low power) or 0 (high power) 
rm /var/lib/nvpmodel/status
reboot

## Example startup logfile
```python
2021-03-08:19:19:43,355 INFO     [CudaCam.py:463] CudaCam started
2021-03-08:19:19:43,356 INFO     [CudaCam.py:469] Remapped rtsp://192.168.1.10:554/user=admin&password=secret&channel=1&stream=0.sdp to rtsp://127.0.0.1:8554/front_garden as using_rtsp_simple_proxy set
2021-03-08:19:19:43,356 INFO     [CudaCam.py:469] Remapped rtsp://192.168.1.12:554/user=admin&password=secret&channel=1&stream=0.sdp to rtsp://127.0.0.1:8554/back_garden as using_rtsp_simple_proxy set
2021-03-08:19:19:43,357 INFO     [CudaCam.py:469] Remapped rtsp://192.168.1.11:554/user=admin&password=secret&channel=1&stream=0.sdp to rtsp://127.0.0.1:8554/back_patio as using_rtsp_simple_proxy set
2021-03-08:19:19:46,892 INFO     [CudaCam.py:480] Starting inference engine, can take a while
2021-03-08:19:20:03,587 INFO     [CudaCam.py:482] Inference engine is up
2021-03-08:19:20:03,733 INFO     [CudaCam.py:517] Starting cameras and getting test images for /media/nano1/usbhdd/mutelist_reminder, can take a while
2021-03-08:19:20:14,936 INFO     [CudaCam.py:571] Processed 0 images in the past 10 seconds
2021-03-08:19:20:25,089 INFO     [CudaCam.py:571] Processed 320 images in the past 10 seconds
2021-03-08:19:21:22,700 INFO     [CudaCam.py:657] Event 'Initialised' : front_garden - person, confidence 0.54 : 211,286,13,247
2021-03-08:19:21:25,760 INFO     [CudaCam.py:657] Event 'Has moved' : front_garden - person, confidence 0.84 : 220,314,3,245
2021-03-08:19:21:25,969 INFO     [CudaCam.py:571] Processed 302 images in the past 10 seconds
```

## Exampe  mutelist (see config.txt), Green = _inside, Red = _outside

See example2-mutelist.jpg

## Example alarmed event (see config.txt). Alse get email and MQTT message if configured in config.txt.

See example1-event.jpg

## Contributing
Have moved on to the next thing, have archived for forkz.

email JoeTester1965 at mail dot com with any questions.

## License
[MIT](https://choosealicense.com/licenses/mit/)
