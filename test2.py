import tkinter as tk
from tkinter.ttk import *
from tkinter import *  
from PIL import ImageTk, Image

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack()
        self.create_widgets()
        

    def create_widgets(self):
        #add label for number
        self.label1 = Label(self)
        self.label1["text"] = "Face Mask Detector \nAlert System" 
        self.label1.config(font=('Helvetica 18 bold'))
        self.label1.pack(side="top", padx=1)

        self.hi_there = tk.Button(self,padx=7)
        self.hi_there["text"] = "Open camera"
        self.hi_there["command"] = self.say_hi
        self.hi_there.pack(side=tk.LEFT, padx=10)
        self.grid(padx=120, pady=10, row=30)

        #Create an object of tkinter ImageTk
        self.img=PhotoImage(file="face.png")
        self.l3=Label(image=self.img, text="Hello")
        self.l3.config(font=('Helvetica 18 bold'))
        self.l3.image=self.img
        self.l3.grid()

        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=root.destroy, padx=30, )
        self.quit.pack(side=tk.LEFT)

    def say_hi(self):
        print("hi there, everyone!")

#for debug
if __name__=="__main__":
  root = tk.Tk()
  root.title("Face Mask Detector - Papichaya-Dev")
  root.geometry("500x500")
  app = Application(master=root)
  app.mainloop()