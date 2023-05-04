# Real-time Video Object Detection in a Distributed System with Heterogeneous Models


## To run the system:

&emsp; __client:__ python client.py [video source] [input server ip] [output server ip]

&emsp; &emsp; Example: python client.py test_video.mp4 192.168.1.2 192.168.1.3
  
&emsp; __input_server:__ python input_server.py
  
&emsp; __output_sever:__ python output_server.py
  
&emsp; __worker_server:__ python worker_server.py [object detection model]

&emsp; &emsp; Example: python worker_server.py yolov5s.pt
  
  
## To understand the system

Demos:
&emsp; __Add a new worker__ https://mega.nz/file/qEJy2ayT#upoEJw2RGP4bO91DUPDwrDepaxqTgw7fGQhgdp4bHdA



Please read "paper.pdf" to understand the system better.
