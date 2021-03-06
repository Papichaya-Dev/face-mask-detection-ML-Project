# import library
import tkinter as tk
from tkinter.ttk import *
from tkinter import *  
from PIL import ImageTk, Image
from email import message
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from imutils.video import VideoStream
import numpy as np
import imutils
import time
import cv2
import os
import smtplib
from pygame import mixer
from tkinter import messagebox
import threading
import asyncio
from config import SMTP_EMAIL, SMTP_PASSWORD

#login gmail for sending if people doesn't wear a mask
mail = smtplib.SMTP('smtp.gmail.com', 587)
mail.ehlo()
mail.starttls()
# ('you email', 'your password')
mail.login(SMTP_EMAIL,SMTP_PASSWORD)
		
#defined function for detect and predict mask
def detect_and_predict_mask(frame, faceNet, maskNet):
    # grab the dimensions of the frame and then construct a blob
	# from it
	(h, w) = frame.shape[:2]
	blob = cv2.dnn.blobFromImage(frame, 1.0, (224, 224),
		(104.0, 177.0, 123.0))

	# pass the blob through the network and obtain the face detections
	faceNet.setInput(blob)
	detections = faceNet.forward()
	# print(detections.shape)

	#สร้าง ตัวแปร faces,locs,preds เป็น Array เพื่อรอรับค่า
	faces = []
	locs = []
	preds = []

	# loop over the detections
	for i in range(0, detections.shape[2]):
		# extract the confidence (i.e., probability) associated with
		# the detection
		confidence = detections[0, 0, i, 2]

		# filter out weak detections by ensuring the confidence is
		# greater than the minimum confidence
		if confidence > 0.5:
			# compute the (x, y)-coordinates of the bounding box for
			# the object
			box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
			(startX, startY, endX, endY) = box.astype("int")

			#ตีกรอบตามแกน x , แกน y
			(startX, startY) = (max(0, startX), max(0, startY))
			(endX, endY) = (min(w - 1, endX), min(h - 1, endY))

			# แยก Region of interest (ROI) ของเเต่ละใบหน้า, แปลงจาก BGR => RGB
			# resize เป็น 224*224 และทำการ preprocessing
			face = frame[startY:endY, startX:endX]
			face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
			face = cv2.resize(face, (224, 224))
			face = img_to_array(face)
			face = preprocess_input(face)

			# add the face and bounding boxes to their respective
			# lists
			#เอาไปใส่หลายหน้า
			faces.append(face)
			#location ในการวาดรอบตำแหน่งหน้า, loc คือพิกัดที่จะเอาไปวาดหน้า
			locs.append((startX, startY, endX, endY))

	# จะ predict ก็ต่อเมื่อตรวจพบใบหน้ามากกว่า 1 หน้าขึ้นไป
	if len(faces) > 0:
		#มาแปลง face เป็น numpy เพราะไวกว่าตัวอื่น 50x faster
		faces = np.array(faces, dtype="float32")
		preds = maskNet.predict(faces, batch_size=32)

	# return a 2-tuple of the face locations and their corresponding
	# locations
	return (locs, preds)

#import framework และ model ที่ใช้ในการ detect face
prototxtPath = r"face_detector\deploy.prototxt" #framework ไปอ่าน model  #detect หน้า ต้อง หน้าก่อน เเมส
weightsPath = r"face_detector\res10_300x300_ssd_iter_140000.caffemodel" #model
faceNet = cv2.dnn.readNet(prototxtPath, weightsPath)

# load the face mask detector model จากโมเดลที่เราเทรนเสร็จ
maskNet = load_model("mask_detector.model")
# initialize the video stream
print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
#load sound use for No wearing mask
mixer.init()
sound = mixer.Sound('Alert_Beep.wav')
#create subject and text for sending e-mail
SUBJECT = "Security Alert"
TEXT = "Found One Visitor that doesn't wear a mask at 44 garden place around the entrance of the resident."
#set variable use for People who don't wear a mask
already_loaded = False
already_sent = False
sound_cooldown = False
email_cooldown = False

def releaseCooldown():
	global sound_cooldown
	sound_cooldown = False

def playSound():
	global sound_cooldown
	if sound_cooldown:return 
	sound.play(time.daylight)
	sound_cooldown = True
	threading.Timer(2, releaseCooldown).start()

def setAlreadyLoaded():
	global already_loaded
	if already_loaded == False:
		already_loaded = True

def sendWarningEmail():
	global already_sent
	if already_sent:return 
	message = 'Subject: {}\n\n{}'.format(SUBJECT, TEXT)
	mail.sendmail(SMTP_EMAIL,SMTP_EMAIL, message)
	mail.close()
	already_sent = True

def detection_function():
    # loop over the frames from the video stream
    global email_cooldown
    while True:
        #อ่านตัว frame / ปรับขนาด framr = 600 px
        frame = vs.read()
        frame = imutils.resize(frame, width=800)

        # detect ใบหน้าในเฟรมและ detect ดูว่ามีคนใส่เเมสหรือไม่ใส่
        # detect ก่อนถึงได้ locs , preds
        (locs, preds) = detect_and_predict_mask(frame, faceNet, maskNet)

        # เข้า loop ตามตำแหน่งใบหน้าที่ detect
        # locs = ทำกรอบ , preds
        for (box, pred) in zip(locs, preds):
            # unpack the bounding box and predictions
            (startX, startY, endX, endY) = box
            (mask, withoutMask) = pred

            #กำหนด label เเละให้ค่า label = Mask , No mask กำหนดสีให้ text 
            label = "Mask" if mask > withoutMask else "No Mask"
            color = (0, 255, 0) if label == "Mask" else (0, 0, 255)
            #กำหนดเงื่อนไขถ้าไม่ใส่เเมสให้ put txt และ play sound ให้ threading timer 1 วิเเละค่อยส่ง E-mail
            # if(label == "Mask"):
            #     cv2.putText(frame, "You are arounded to go inside", ( 120, 60),
            #     cv2.FONT_HERSHEY_SIMPLEX, 1.2, color,2)
            if(label == "No Mask"):
                if(already_loaded == False):
                    continue
                cv2.putText(frame, "Please wear a Mask !", ( 200, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, color,2)
                playSound()
                #กันไม่ให้ thread สร้างซ้ำๆ
                if not email_cooldown:
                    email_cooldown = True
                    threading.Timer(1, sendWarningEmail).start()

            # ระบุค่า accuracy ใน label
            label = "{} {:.2f}%".format(label, max(mask, withoutMask) * 100)

            #แสดงผล label และ ตีกรอบสี่เหลี่ยมบริเวณ output 
            cv2.putText(frame, label, (startX, startY - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color,2)
            cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)

            
        # show the output frame
        cv2.imshow("Face mask detector - Papichaya-Dev", frame)
        threading.Timer(2, setAlreadyLoaded).start()
        key = cv2.waitKey(1) & 0xFF

        # ถ้ากด q จะเป็นการ break loop
        if key == ord("q"):
            break

    # do a bit of cleanup
    cv2.destroyAllWindows()
    vs.stop()
class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        #add label for number
        self.label_info = Label(self)
        self.label_info["text"] = "Face Mask Detector \nAlert System" 
        self.label_info.config(font=('Helvetica 18 bold'))
        self.label_info.pack(side="top", padx=1)
        #add 
        self.open_button = tk.Button(self,padx=7)
        self.open_button["text"] = "Open camera"
        self.open_button["command"] = self.detection
        self.open_button.pack(side=tk.LEFT, padx=10)
        self.grid(padx=120, pady=10, row=30)

        #Create an object of tkinter ImageTk
        self.img=PhotoImage(file="face_GUI.png")
        self.pic=Label(image=self.img)
        self.pic.config(font=('Helvetica 18 bold'))
        self.pic.image=self.img
        self.pic.grid()

        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=root.destroy, padx=30, )
        self.quit.pack(side=tk.LEFT)

    def detection(self):
        detection_function()

#for debug
if __name__=="__main__":
  root = tk.Tk()
  root.title("Face Mask Detector - Papichaya-Dev")
  root.geometry("500x500")
  app = Application(master=root)
  app.mainloop()