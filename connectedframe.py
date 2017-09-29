#!/usr/bin/env python

from Tkinter import *
from os import putenv, getenv, system
from PIL import Image, ImageTk
import pexif
from PIL.ExifTags import TAGS
from glob import glob

dropbox_link = getenv("DROPBOX_LINK")
download_interval = int(getenv("DOWNLOAD_INTERVAL_HOURS")) * 60 * 60 * 1000
carousel_interval = int(getenv("CAROUSEL_INTERVAL_SECONDS")) * 1000
frame_owner = getenv("FRAME_OWNER")
ifttt_key = getenv("IFTTT_KEY")

base_path = "/usr/src/app/images/"
carrousel_status = True
image_index = 0
image_list = []
initial_init = True

def download_images(url):
	archive = base_path + "temp.zip"

	remove = "sudo rm -rf " + base_path + "*"
	download = "wget -q  "+ url + " -O " + archive
	extract = "unzip -o " + archive + " -d " + base_path
	print("Removing old images...")
	system(remove)
	print("Images removed.")
	print("Downloading new images from Dropbox...")
	system(download)
	print("Download complete.")
	print("Extracting images...")
	system(extract)
	print("Extract complete.")
	
def rotate_images():
	images = list_images()
	print ("debug 34: ",images)
	for file in images:
		print ("debug 36: ", file)
		img = pexif.JpegFile.fromFile(file)
		print ("debug 38: ", img)
		if img.exif.primary.Orientation is not 0:
			try:
				print ("debug 40: exif prim.orient is not None for ", img)
				#Get the orientation if it exists
				orientation = img.exif.primary.Orientation[0]
				img.exif.primary.Orientation = [1]
				img.writeFile(file)

				#now rotate the image using the Python Image Library (PIL)
				img = Image.open(file)
				if orientation is 6: img = img.rotate(-90)
				elif orientation is 8: img = img.rotate(90)
				elif orientation is 3: img = img.rotate(180)
				elif orientation is 2: img = img.transpose(Image.FLIP_LEFT_RIGHT)
				elif orientation is 5: img = img.rotate(-90).transpose(Image.FLIP_LEFT_RIGHT)
				elif orientation is 7: img = img.rotate(90).transpose(Image.FLIP_LEFT_RIGHT)
				elif orientation is 4: img = img.rotate(180).transpose(Image.FLIP_LEFT_RIGHT)

				#save the result
				print ("debug 60: saving ", img, " as ", file)
				img.save(file)
			except Exception: 
				print ("debug 61: exception called by line 40")
				pass
		else:
			print ("debug 64: else called by line 40: exif prim.orient is None for ", img)
			pass
		
def resize_images():
	baseheight = 480
	images = list_images()
	for file in images:
		img = Image.open(file)
		hpercent = float(float(img.size[0])/float(img.size[1]))
		neww = int(baseheight*float(hpercent))
		img = img.resize((neww,baseheight), Image.ANTIALIAS)
		img.save(file, "JPEG")

def add_borders():
	images = list_images()
	for file in images:
		old_im = Image.open(file)
		old_size = old_im.size
		new_size = (640, 480)
		new_im = Image.new("RGB", new_size)   ## luckily, this is already black!
		new_im.paste(old_im, ((new_size[0]-old_size[0])/2,
							  (new_size[1]-old_size[1])/2))
		new_im.save(file)
		
def list_images():
	images = []

	dir = base_path + "*.jpg"

	images = glob(dir)

	return images

def previous_image():
	global image_index
	image_index = image_index - 1

	if image_index < 0:
		image_index = len(image_list) - 1

	image_path = image_list[image_index]

	update_image(image_path)
	
def next_image():
	global image_index
	image_index = image_index + 1

	if image_index > len(image_list) - 1:
		image_index = 0

	image_path = image_list[image_index]

	update_image(image_path)

def play_pause():
	global carrousel_status

	carrousel_status = not carrousel_status

	if(carrousel_status):
		img = ImageTk.PhotoImage(Image.open("/usr/src/app/icons/pause.png"))
	else:
		img = ImageTk.PhotoImage(Image.open("/usr/src/app/icons/play.png"))
	
	play_button.configure(image=img)
	play_button.image = img

def carrousel():
	if(carrousel_status):
		next_image()

	root.after(carousel_interval, carrousel)

def update_image(image_path):
	img = ImageTk.PhotoImage(Image.open(image_path))
	center_label.configure(image=img)
	center_label.image = img

	img = ImageTk.PhotoImage(Image.open("/usr/src/app/icons/like.png"))
	like_button.configure(image=img)
	like_button.image = img

def initialize():
	global image_list, carrousel_status, initial_init
	current_carrousel_status = carrousel_status
	carrousel_status = False

	download_images(dropbox_link)
	#rotate_images()
	resize_images()
	add_borders()
	image_list = list_images()

	carrousel_status = current_carrousel_status

	if(initial_init):
		print ("Connected Frame is now running...")
		initial_init = False
		root.after(1000, initialize)
	else:
		root.after(download_interval, initialize)

def send_event():
	img = ImageTk.PhotoImage(Image.open("/usr/src/app/icons/liked.png"))
	like_button.configure(image=img)
	like_button.image = img

	command = "curl -X POST -H \"Content-Type: application/json\" -d '{\"value1\":\"" + frame_owner + "\",\"value2\":\"" + image_list[image_index] + "\"}' https://maker.ifttt.com/trigger/connectedframe_like/with/key/" + ifttt_key

	system(command)

root = Tk()
root.title('Connected Frame')
root.geometry('{}x{}'.format(800, 480))
root.attributes("-fullscreen", True)
root.config(cursor='none')

initialize()

left_column = Frame(root, bg='black', width=80, height=480)
center_column = Frame(root, bg='black', width=640, height=480)
right_column = Frame(root, bg='black', width=80, height=480)

left_column.pack_propagate(0)
center_column.pack_propagate(0)
right_column.pack_propagate(0)

left_column.grid(row=0, column=0, sticky="nsew")
center_column.grid(row=0, column=1, sticky="nsew")
right_column.grid(row=0, column=2, sticky="nsew")

next_icon = ImageTk.PhotoImage(Image.open("/usr/src/app/icons/next.png"))
previous_icon = ImageTk.PhotoImage(Image.open("/usr/src/app/icons/previous.png"))
play_icon = ImageTk.PhotoImage(Image.open("/usr/src/app/icons/pause.png"))
like_icon = ImageTk.PhotoImage(Image.open("/usr/src/app/icons/like.png"))

previous_button = Button(left_column, image=previous_icon, borderwidth=0, background="black", foreground="white", activebackground="black", activeforeground="white", highlightthickness=0, command=previous_image)
next_button = Button(left_column, image=next_icon, borderwidth=0, background="black", foreground="white", activebackground="black", activeforeground="white", highlightthickness=0, command=next_image)
play_button = Button(right_column, image=play_icon, borderwidth=0, background="black", foreground="white", activebackground="black", activeforeground="white", highlightthickness=0, command=play_pause)
like_button = Button(right_column, image=like_icon, borderwidth=0, background="black", foreground="white", activebackground="black", activeforeground="white", highlightthickness=0, command=send_event)

center_image = Image.open(image_list[0])
center_photo = ImageTk.PhotoImage(center_image)
center_label = Label(center_column, image=center_photo)

previous_button.pack(fill=BOTH, expand=1)
next_button.pack(fill=BOTH, expand=1)
center_label.pack(side="bottom", fill=BOTH, expand=1)
play_button.pack(fill=BOTH, expand=1)
like_button.pack(fill=BOTH, expand=1)

carrousel()

root.mainloop()
