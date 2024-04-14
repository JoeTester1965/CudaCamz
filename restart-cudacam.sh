nohup pkill -f CudaCam.py > /dev/null

nohup python3 CudaCam.py config.txt > /dev/null 2>&1 < /dev/null &
