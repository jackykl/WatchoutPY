#import the necessary modules
import freenect
import cv2
import numpy as np
import socket,time, json, random, base64

clientsocket=""
 
#function to  saveImage
def saveImage(selection):
	if selection == 1:
		cv2.imwrite("temp.png",get_video())
	elif selection == 2:
		return cv2.imencode(".png",get_depth())
		#cv2.imwrite("test.png",get_video())


#function to set tilt from kinect
def set_tilt():
	TILT_MAX = 30
	TILT_STEP = 10
	TILT_START = 0
	ctx = freenect.init()
	dev = freenect.open_device(ctx, freenect.num_devices(ctx) - 1)
	if not dev:
		freenect.error_open_device()
 		print "Starting TILT Cycle"

	for tilt in xrange(TILT_START, TILT_MAX+TILT_STEP, TILT_STEP):
		print "Setting TILT: ", tilt
		freenect.set_led(dev, 6)
		freenect.set_tilt_degs(dev, tilt)
		time.sleep(3)

	freenect.set_tilt_degs(dev, 0) 

#function to get RGB image from kinect
def get_video():
    array,_ = freenect.sync_get_video()
    array = cv2.cvtColor(array,cv2.COLOR_RGB2BGR)
    return array
 
#function to get depth image from kinect
def get_depth():
    array,_ = freenect.sync_get_depth()
    array = array.astype(np.uint8)
    #print array
    return array

def startsocket():
	global clientsocket
	try:
		clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		print "Starting Connect Server"
		clientsocket.connect(('192.168.0.2',8990))
	except (socket.error) as msg:
		print "Starting Connection"
		print 'Error in socket binding',msg

if __name__ == "__main__":
	global clientsocket
	startsocket()
while 1:
	#set_tilt()
	#saveImage()
	#get a frame from RGB camera
	frame = get_video()
	#get a frame from depth sensor
	#depth = get_depth()
	#display RGB image
	#cv2.imshow('RGB image',frame)
	saveImage(1)
	with open ("temp.png","rb") as image_str:
		imgstr=base64.b64encode(image_str.read())
		#print(imgstr)
		#kdata=base64.b64encode(saveImage(1))
		#print(kdata)
		data=[{"func":"2"},{"id":"kinectStream","data":imgstr}]
		send_json = json.dumps(data)
		clientsocket.send(send_json)
	time.sleep(.5)
	#display depth image
	#cv2.imshow('Depth image',depth)
	# quit program when 'esc' key is pressed
	k = cv2.waitKey(5) & 0xFF
	if k == 27:
		break
		cv2.destroyAllWindows()	