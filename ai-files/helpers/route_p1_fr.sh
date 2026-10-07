#!/bin/sh
# route_p1_fr.sh NAME MP : background Freerouting on work-p1/NAME.dsn -> NAME.ses, log frNAME.log
W=/home/chithi/Desktop/DesktopSpeaker/ai-files/pcb/work-p1
J=$HOME/Applications/freerouting/jre25/jdk-25.0.4.1+1-jre/bin/java
nohup timeout 1500 $J -Djava.awt.headless=true -jar $HOME/Applications/freerouting/freerouting-2.5.0.jar -de $W/$1.dsn -do $W/$1.ses -mp $2 > $W/fr$1.log 2>&1 &
