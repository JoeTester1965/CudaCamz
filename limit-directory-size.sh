#!/bin/bash

if [ "$#" -ne 3 ]; 
then
	echo "I need a directory, persentage of partition to use and max number of files to delete each round e.g /home/mydir 20 1000"
	exit
fi

Watched_Directory=$1

Max_Directory_Percentage=$2

Number_Files_Deleted_Each_Loop=$3

while [ true ] ; do

	sleep 60

	Directory_Size=$( du -sk "$Watched_Directory" | cut -f1 )

	Disk_Size=$(( $(df $Watched_Directory | tail -n 1 | awk '{print $3}')+$(df $Watched_Directory | tail -n 1 | awk '{print $4}') ))       

	Directory_Percentage=$(echo "scale=2;100*$Directory_Size/$Disk_Size+0.5" | bc | awk '{printf("%d\n",$1 + 0.5)}')

	if [ $Directory_Percentage -gt $Max_Directory_Percentage ]; then

		find $Watched_Directory -type f -printf "%T@ %p\n" | sort -nr | tail -$Number_Files_Deleted_Each_Loop | cut -d' ' -f 2- | xargs rm

		find $Watched_Directory -type d -empty -delete

		Directory_Size=$( du -sk "$Watched_Directory" | cut -f1 )
		Directory_Percentage=$(echo "scale=2;100*$Directory_Size/$Disk_Size+0.5" | bc | awk '{printf("%d\n",$1 + 0.5)}')
	fi

done


