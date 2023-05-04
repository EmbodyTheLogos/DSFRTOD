# object_detection_DS
Real-time Video Object Detection in a Distributed System with Heterogeneous Models

To run the system:

&emsp; client: python client.py [video source] [input server ip] [output server ip]

&emsp; &emsp; Example: python client.py test_video.mp4 192.168.1.2 192.168.1.3
  
&emsp; input_server: python input_server.py
  
&emsp; output_sever: python output_server.py
  
&emsp; worker_server: python worker_server.py [object detection model]

&emsp; &emsp; Example: python worker_server.py yolov5s.pt
  
  
Please read "paper.pdf" to understand the system better
