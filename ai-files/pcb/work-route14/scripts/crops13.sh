#!/bin/sh
# crops13.sh GEO PREFIX : evidence crops of the RT-13 work areas
cd /home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-route13; mkdir -p evidence
G=$1; P=$2
python3 scripts/crop.py $G 86 90 100 104 evidence/$P-r142.png --labels --px 1200 | tail -1
python3 scripts/crop.py $G 172 102 188 116 evidence/$P-q101.png --labels --px 1200 | tail -1
python3 scripts/crop.py $G 146 120 158 134 evidence/$P-u4.png --labels --px 1200 | tail -1
python3 scripts/crop.py $G 134 26 158 56 evidence/$P-cc.png --labels --px 1300 | tail -1
python3 scripts/crop.py $G 182 30 200 58 evidence/$P-jack.png --labels --px 1300 | tail -1
