# CudaCamz

Inspired by  https://github.com/dusty-nv/jetson-inference/ 

Did this as a lockdown project.

The neighbourhood cats, dogs and other more interesting wildlife are now more transparent.

CudaCamz runs on a Nvidia Jetson Nano giving your home or small office a bespoke meaningfully-filtered AI camera event generator on a budget.

Can record all incoming video as well in case something goes down.

Note that you can use **[camerasAI]** and **[camerasREC]** in the [configuration file](./example-config.txt) to select separate camera streams for AI processing and video recording. I have found using D1 mode (720x480) at 10fps works great for AI whilst using 1080p at 25fps for recording. Can then run four cameras concurrently with the AI running at about 10 fps with **[motion_detection_settings]** set in the configuration file at the given defaults.

Optionally can configure to use a RTSP proxy on the jetson nano **[using_rtsp_simple_proxy]** if your cameras cpu and/or network bandwidth is somehow constrained when running multiple sessions.

![!](./scope.jpg "")

You will need some basic Linux skills and a bit of time looking at initial application output to prune false positives by adjusting these sections in the [configuration file](./example-config.txt):

1. **[label_alarmlist_confidence_override]** sets what specific events (a list of possibilities is [here](./ssd_coco_labels.txt)) need alarmed above the given default confidence threshold **[baseline_model_confidence]**. Examine your logfiles and/or database to see what is coming in.

2. **[label_percent_screenfill_min]** states that a given event should only be considered if its percetage image area size is bigger than that given. I put this option in as certain types of leaves in the garden had the AI saying all sorts.

3. **[label_mutelist]** says that you are not interested in those things (e.g. tennis rackets) period. Be prudent though, my favourite cat is often labelled as a bear, and not-so favourite cat a cow!

4. **[object_mutelist-]** defines per camera areas where events are muted:

	**_inside-cameraname** (mute all events inside a defined area) : use for small things that repeatably generate false positives. For me that was a potted plant out front which AI said was a person at night.

	**_outside-cameraname** (mute all events outside, but also encapsulating, a defined area) : use for large things that do the same. For me, my front hedge became a dog as the sun began to set!

![!](./example2-mutelist.jpg "")

## Example alarmed event

![!](./example1-event.jpg "")

You also get an email and/or MQTT message for these if [smtp] and/or [mqtt] is configured in the [configuration file](./config.txt). If you do not use, just delete those sections.

[Samba](https://www.samba.org/) is useful if you want to access events, images and video folders on the Jetson from a PC, but I tend to use [WinSCP](https://winscp.net/eng/index.php).

## Important note

The first time CudaCamz is run using start.sh below, it will take five minutes or more for the AI model running on the GPU to be initially compiled.
 
After that on subsequent runs it will only take about thirty seconds to load from a cache.

Be patient!

## Installing and running

Note that the script ./configure.py below creates **start.sh** and does other configuration work as well. You will need to re-run if cameras are added and/or image/video folders deleted.

1. Put your camera URIs and image / video storage pathnames in the [configuration file](./example-config.txt), then:

```console
bash ./install-depends.sh

python3 ./configure.py ./config.txt

bash ./start.sh
```

2. Examine the images folder / logfiles or sqlite database then tune the [configuration file](./config.txt) to remove any false positives you get.

3. Then use this to start and stop CudaCamz:

```console
./start.sh

./stop.sh
```

3. If you delete an image or video folder, or add or delete a camera, things will need reconfigured again:
```console
python3 ./configure.py ./config.txt
```

## Basic operational outline

```python
For all cameras
	Get a frame
		Has any motion been detected in that frame ?
			Are there any unfiltered AI detection events in that frame ?
				Does any event in this frame meet any given alarm criteria ?
					Alarm (MQTT and SMTP email - as configured or not)
```

## Example startup logfile
```bash
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

## Contributing

Please do email JoeTester1965 at mail dot com with any questions.

## License
[MIT](https://choosealicense.com/licenses/mit/)
