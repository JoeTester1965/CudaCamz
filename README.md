# CudaCam

Inspired by  https://github.com/dusty-nv/jetson-inference/ 

Did this as a lockdown project.

The neighbourhood cats, dogs and other more interesting wildlife are now more transparent.

CudaCam runs on a Nvidia Jetson Nano giving your home or small office a bespoke well-filtered AI camera event generator & recording appliance on a budget.

All without selling your soul to GAFA  (I hope).

Can record all incoming video as well in case something goes down.

Uses a very network efficient [RTSP proxy](https://github.com/aler9/rtsp-simple-server) for concurrent live monitoring with something like [VLC media player](https://www.videolan.org/vlc/index.en-GB.html).

You will need some basic Linux skills and a wee bit of time initially looking at the application output
to weed out false positives. 

More advice on this is given in the [example configuration file](./config.txt).

[Samba](https://www.samba.org/) is useful if you want to access events, images and video folders on the Jetson from a PC, but I tend to use [WinSCP](https://winscp.net/eng/index.php).

## Important note

The first time CudaCam is run using start.sh in step 4. below, it will take five minutes or more for the AI model running on the GPU to be initially compiled.
 
After that on subsequent runs it will only take about thirty seconds to load from a cache.

Be patient!

## Installing and running

Note that the script ./configure.py below creates start.sh and does other configuration work as well. You will need to re-run if cameras are added and/or image/video folders deleted.

1. Put your camera URIs and image / video storage pathnames in [config.txt](./config.txt), then:

```console
bash ./install-depends.sh

python3 ./configure.py ./config.txt

bash ./start.sh
```

2. Look at what you see in the images folders and logfiles and database (I use DBbrowser for SQLite) and tune config.txt to remove any false positives you get, then this to start and stop as needed:

```console
./start.sh

./stop.sh
```

3. If you delete an image / video folder and/or add / delete a camera, stuff will need reconfigured again:
```console
python3 ./configure.py ./config.txt
```

## Basic operational outline

```python
For all cameras
	Get a frame
		Has any motion been detected in that frame ?
			Are there any unfilered AI detection events in that frame ?
				Does any event in this frame meet any given alarm criteria ?
					Alarm (MQTT and SMTP email)
```

## Performance and power plans

Experiment - Four cameras attached at 720p, 20fps - Constant Bit Rate. Ambient temperature was 15C. No cooling. 

Measured using [jtop](https://pypi.org/project/jetson-stats/).

| Power plan mode |    Current   | AO temp (C)  | Images per second |
| :-------------: | :----------: | :-----------:| :-----------------|
|       1         |     2.5A     |      52      |         190       |
|       0         |     6.0A     |      66      |         310       |   
	
To change power plan mode on Jetson Nano (and survive a reboot): 

```console
sudo nano /etc/nvpmodel.conf
```

*change PM_CONFIG DEFAULT at bottom of that file to 1 (low power) or 0 (high power)*

```console
rm /var/lib/nvpmodel/status
sudo reboot
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

## Example of some fine-grained detection area filtering

See [config.txt](./config.txt) for more details on how to set these up.

Use _inside **mute all events inside this window** , (green in image below) for small things in frame that constantly generate false positives. For me that was a potted plant out front (came up as person at night) and a hosereel out back (again sometimes came up us a person depending on the light)

Use _outside **mute all events outside, but also encapsulating, this window** ,  (red in image belo) for large things in frame again generating false positives. For me, my front hedge became a dog as the sun began to set!

![!](./example2-mutelist.jpg "")

## Example alarmed event (see [config.txt](./config.txt) for details). 

![!](./example1-event.jpg "")

You alse get email and/or MQTT message for these (if configured) in [config.txt](./config.txt).

## Contributing
Have moved on to the next thing, so is archived.

Please do email JoeTester1965 at mail dot com with any questions.

## License
[MIT](https://choosealicense.com/licenses/mit/)
