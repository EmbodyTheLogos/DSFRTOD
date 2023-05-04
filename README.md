# Real-time Video Object Detection in a Distributed System with Heterogeneous Models


## To run the system:

&emsp; __client:__ python client.py [video source] [input server ip] [output server ip]

&emsp; &emsp; Example: python client.py test_video.mp4 192.168.1.2 192.168.1.3
  
&emsp; __input_server:__ python input_server.py
  
&emsp; __output_sever:__ python output_server.py
  
&emsp; __worker_server:__ python worker_server.py [object detection model]

&emsp; &emsp; Example: python worker_server.py yolov5s.pt
  
  
Please see the "demo" folder for demos of the project.

Please read "paper.pdf" to understand the system better.
