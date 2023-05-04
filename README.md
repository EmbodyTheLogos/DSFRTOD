# Real-time Video Object Detection in a Distributed System with Heterogeneous Models


## To run the system:

&emsp; __client:__ python client.py [video source] [input server ip] [output server ip]

&emsp; &emsp; Example: python client.py test_video.mp4 192.168.1.2 192.168.1.3
  
&emsp; __input_server:__ python input_server.py
  
&emsp; __output_sever:__ python output_server.py
  
&emsp; __worker_server:__ python worker_server.py [object detection model]

&emsp; &emsp; Example: python worker_server.py yolov5s.pt
  
  
## To understand the system

Please read "paper.pdf" to understand the system better.

Demos:

&emsp; __Synchorinization__ https://mega.nz/file/SBx1kIxQ#mnLTucX_h3aptyB8EU3wQ9QOG5oS2-bomzvyzdJW2ec

&emsp; __Working System__ https://mega.nz/file/HIJGXIwR#vhSYR7waDg_EPyFeU6Wfh36S64GwX46mstj_Lkv8lGE

&emsp; __Disconnect and connect client__ https://mega.nz/file/LVg0URAY#TVAt-3kMEbMIUEFYkc2SoTFDAjbmHWiyygzQ1t-_P9g

&emsp; __Disconnect a worker__ https://mega.nz/file/iJQD2CQI#Gewyi5zUL3mjUGi4l-gwM18HfkZkw-MSVHEJls8RzJU

&emsp; __Add a new worker__ https://mega.nz/file/qEJy2ayT#upoEJw2RGP4bO91DUPDwrDepaxqTgw7fGQhgdp4bHdA



