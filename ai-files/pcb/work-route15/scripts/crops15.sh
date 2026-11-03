#!/bin/sh
# crops14.sh GEO PREFIX : evidence crops of the RT-15 work areas
cd /home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route15; mkdir -p evidence
G=$1; P=$2
python3 scripts/crop.py $G 108 106 130 128 evidence/$P-fault.png --labels --px 1300 | tail -1
python3 scripts/crop.py $G 184 31 194 40 evidence/$P-r242.png --labels --px 1100 | tail -1
python3 scripts/crop.py $G 146 120 156 130 evidence/$P-u4qon.png --labels --px 1100 | tail -1
