#!/bin/bash

echo ""
echo "Say Y to all questions and just choose the defaults (press OK) when the menus pop up installing jetson-inference models"
echo ""
echo "Will need root password to install jetson libraries"
echo ""

sudo apt-get update
sudo apt-get install dialog
sudo apt-get install git cmake libpython3-dev python3-numpy python3-pip libjpeg-dev zlib1g-dev

pip3 install paho-mqtt
pip3 install pillow

FOLDER="jetson-inference"
URL="https://github.com/dusty-nv/jetson-inference"

if [ ! -d "$FOLDER" ] ; then
	git clone $URL

fi
cd "$FOLDER"

FOLDER="build"
if [ ! -d "$FOLDER" ] ; then
	mkdir $FOLDER
fi
cd $FOLDER
cmake ../ 
sudo make install
sudo ldconfig
cd ../..

FOLDER="jetson-utils"
URL="https://github.com/dusty-nv/jetson-utils"

if [ ! -d "$FOLDER" ] ; then
	git clone $URL
fi
cd "$FOLDER"

FOLDER="build"
if [ ! -d "$FOLDER" ] ; then
	mkdir $FOLDER
fi
cd $FOLDER
cmake ../ 
sudo make install
sudo ldconfig
cd ../..

chmod u+x ./configure.py

mkdir -p rtsp_simple_server
cd rtsp_simple_server
wget https://github.com/aler9/rtsp-simple-server/releases/download/v0.14.2/rtsp-simple-server_v0.14.2_linux_arm64v8.tar.gz
gunzip rtsp-simple-server_v0.14.2_linux_arm64v8.tar.gz
tar -xvf  rtsp-simple-server_v0.14.2_linux_arm64v8.tar
rm rtsp-simple-server_v0.14.2_linux_arm64v8.tar
mv rtsp-simple-server.yml rtsp-simple-server.yml.original
