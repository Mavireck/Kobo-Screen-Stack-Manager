#!/usr/bin/env python
import sys
import os
import threading
from time import sleep
# Load the wrapper module, it's linked against FBInk, so the dynamic loader will take care of pulling in the actual FBInk library
from _fbink import ffi, lib as FBInk
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
# My own librairies (Kobo-Input-Python, Kobo-Python-OSKandUtils)
sys.path.append('../Kobo-Input-Python')
import KIP


fbink_cfg = ffi.new("FBInkConfig *")
fbink_dumpcfg = ffi.new("FBInkDump *")
fbfd = FBInk.fbink_open()
FBInk.fbink_init(fbfd, fbink_cfg)
#Get screen infos
state = ffi.new("FBInkState *")
FBInk.fbink_get_state(fbink_cfg, state)
screen_width=state.screen_width
screen_height=state.screen_height
view_width=state.view_width
view_height=state.view_height

h_offset = screen_height - view_height
w_offset = screen_width - view_width


def mprint_raw(raw_data,x,y,w,h,length=None,isInverted=False):
	if length==None:
		length = len(raw_data)
	# FBInk.fbink_print_image(fbfd, str(path).encode('ascii'), x, y, fbink_cfg)
	FBInk.fbink_print_raw_data(fbfd, raw_data, w, h, length, x, y, fbink_cfg)
	if isInverted == True:
		# Workaround : print_raw_data cannot print something inverted, so we print the thing
		# Then we invert-refresh the region
		mode = bool(fbink_cfg.is_nightmode)
		fbink_cfg.is_nightmode = not fbink_cfg.is_nightmode
		FBInk.fbink_refresh(fbfd, y+h_offset,x+w_offset,w,h, FBInk.HWD_PASSTHROUGH, fbink_cfg)
		fbink_cfg.is_nightmode = mode

def do_screen_refresh(isInverted=False,isPermanent=True):
	mode = bool(fbink_cfg.is_flashing)
	mode2 = bool(fbink_cfg.is_nightmode)
	fbink_cfg.is_flashing = True
	fbink_cfg.is_nightmode = isInverted
	FBInk.fbink_refresh(fbfd, 0, 0, 0, 0, FBInk.HWD_PASSTHROUGH, fbink_cfg)
	fbink_cfg.is_flashing = mode
	if not isPermanent:
		fbink_cfg.is_nightmode = mode2

def do_screen_clear():
	FBInk.fbink_cls(fbfd, fbink_cfg)

def coordsInArea(x,y,area):
	if len(area)>2:
		if x>=area[0] and x<area[2] and y>=area[1] and y<area[3]:
			return True
		else:
			return False
	else:
		if x>=area[0][0] and x<area[1][0] and y>=area[0][1] and y<area[1][1]:
			return True
		else:
			return False

def getRectanglesIntersection(area1,area2):
	x1 = max(area1[0][0],area2[0][0])
	x2 = min(area1[1][0],area2[1][0])
	y1 = max(area1[0][1],area2[0][1])
	y2 = min(area1[1][1],area2[1][1])
	if x2-x1>0 and y2-y1>0:
		return [[x1,y1],[x2,y2]]
	else:
		return None

def returnFalse(a=False,b=False,c=False):
	return False

def pillowImgToScreenObject(img,x,y,name="noname",onclickInside=returnFalse,onclickOutside=returnFalse):
	raw_data = img.tobytes("raw")
	obj =  ScreenObject(raw_data,(x,y),(x + img.width, y + img.height),name, onclickInside, onclickOutside)
	return obj



class ScreenObject:
	def __init__(self,imgData,xy1,xy2,name="noname",onclickInside=returnFalse,onclickOutside=returnFalse,isInverted=False,data=[]):
		"""
		If onclickInside == None, then the stack will keep searching for another object under this one. 
		Use onclickInside == returnFalse if you want the stack to do nothing when touhching the object.
		OnclickInside and onclickOutside will be given as argument : x,y,data
		"""
		self.imgData = imgData
		self.name = name
		self.xy1 = xy1
		self.x = xy1[0]
		self.y = xy1[1]
		self.xy2 = xy2
		self.x2 = xy2[0]
		self.y2 = xy2[1]
		self.w = self.x2-self.x
		self.h = self.y2-self.y
		self.onclickInside = onclickInside
		self.onclickOutside = onclickOutside
		self.isInverted = isInverted
		self.data = data

	def printObj(self):
		"""
		Standalone print. Printing can also be done through the stack manager, after adding the object
		Should NOT be used on its own
		"""
		mprint_raw(self.imgData,self.x, self.y, self.w, self.h,isInverted=self.isInverted)

	def setInverted(self,mode):
		self.isInverted = mode

	def invert(self,invertDuration):
		mode = bool(self.isInverted)
		self.setInverted(not self.isInverted)
		self.printObj()
		threading.Timer(invertDuration,self.setInverted,[mode]).start()
		threading.Timer(invertDuration,self.printObj).start()

	def updateImg(self,newImg,xy1,xy2):
		"""
		Updates the object without displaying it.
		"""
		self.imgData = imgData
		self.xy1 = xy1
		self.x = xy1[0]
		self.y = xy1[1]
		self.xy2 = xy2
		self.x2 = xy2[0]
		self.y2 = xy2[1]
		self.w = x2-x
		self.h = y2-y



class ScreenStackManager:
	def __init__(self,inputObject,name="screen",stack=[],isInverted=False):
		self.inputObject = inputObject
		self.name = name
		self.stack = stack
		self.isInverted = isInverted
		self.isInputThreadStarted = False

	def printStack(self,skipObj=None,areaFromObject=None):
		"""
		Prints the stack elements in the stack order
		If a skipObj is specified, then the function will not display the skipObj.
		If a areaFromObject is set, then, we only display
			the part of the stack which is at the place of areaFromObject object
		"""
		mainIntersectionArea = [(areaFromObject.x,areaFromObject.y),(areaFromObject.x2,areaFromObject.y2)] if areaFromObject else [(0,0),(screen_width,screen_height)]
		print("Printing stack")
		for obj in self.stack:
			print("-----")
			print("Looking at object : " + str(obj.name))
			if (not skipObj) or (skipObj and obj != skipObj):
				# We loop through the objects behind the screenObject we are working on
				objArea = [(obj.x,obj.y),(obj.x2,obj.y2)]
				rectIntersection = getRectanglesIntersection(mainIntersectionArea,objArea)
				if rectIntersection != None:
					# The obj we are looking at is behind the screenObj
					self.printPartialObj(obj,rectIntersection)

	def printPartialObj(self,obj,rectIntersection):
		print("Printing object " + str(obj.name) + " at rectIntersect : " + str(rectIntersection) + " with inversion status " + str(obj.isInverted))
		# We crop and print a par of the object
		# First, lets make a PILLOW object:
		img = Image.frombytes('L',(obj.w,obj.h),obj.imgData)
		# Then, lets crop it: 
		# TODO : There must be a way to crop the raw data directly, without pillow...
		print("Still TODO : crop raw_data without pillow")
		img = img.crop((rectIntersection[0][0]-obj.x, rectIntersection[0][1]-obj.y, rectIntersection[1][0]-obj.x, rectIntersection[1][1]-obj.y))
		# Then, lets print it:
		raw_data=img.tobytes("raw")
		mprint_raw(raw_data,rectIntersection[0][0], rectIntersection[0][1],img.width,img.height,isInverted=obj.isInverted)

	def addObj(self,screenObj):
		"""
		Adds object to the stack and prints it
		"""
		#TODO : distinguish between update and force print
		print("Still TODO : distinguish between update and force print")
		self.forceAddObj(screenObj)

	def forceAddObj(self,screenObj):
		"""
		Adds object to the stack and prints it
		"""
		self.stack.append(screenObj)
		screenObj.printObj()

	def updateObj(self,screenObj,newImg,xy1,xy2):
		"""
		Updates the object : updates the stack and prints the object and all the stack above it
		while keeping the stack position
		"""
		screenObj.updateImg(newImg,xy1,xy2)
		#Then we print the stack, but only the area where screenObj was
		self.printStack(areaFromObject=screenObj)
		return True

	def removeObj(self,screenObj):
		"""
		Removes the object from the stack and hides it from the screen
		"""
		# We print the stack, but only the area where screenObj was
		self.printStack(screenObj,screenObj)
		self.stack.remove(screenObj)

	def getStackLevel(self,screenObj):
		return self.stack.index(screenObject)

	def setStackLevel(self,screenObj,stackLevel="last"):
		"""
		Set the position of said object
		Then prints every object above it (including itself)
		"""
		if stackLevel=="last":
			stackLevel=len(self.stack)
		self.stack.insert(stackLevel,screenObject)
		self.printStack(areaFromObject=screenObj)
		return True

	def invertObj(self, screenObj,invertDuration):
		"""
		Shortcut (or longcut, it depends on the point of view) to invert the screen object
		"""
		screenObj.invert(invertDuration)
		self.printStack(skipObj=None,areaFromObject=screenObj)
		threading.Timer(invertDuration,self.printStack,[None,screenObj]).start()

	def invert(self):
		"""
		Inverts the whole screen
		"""
		self.isInverted = not self.isInverted
		do_screen_refresh(self.isInverted)
		return True

	def refresh(self):
		do_screen_refresh()

	def clear(self):
		do_screen_clear()

	def createCanvas(self,color=255):
		"""
		Creates a white object at the bottom of the stack, displays it while refreshing the screen
		"""
		img = Image.new('L', (screen_width,screen_height), color=255)
		background = pillowImgToScreenObject(img,0,0,name="Canvas")
		self.addObj(background)
		return True

	def startListenerThread(self):
		self.isInputThreadStarted = True
		threading.Thread(target=self.listenForTouch).start()


	def listenForTouch(self):
		print("lets do this")
		while True:
			try:
				(x, y, err) = self.inputObject.getInput()
			except:
				continue
			if not self.isInputThreadStarted:
				break
			if t.debounceAllow(x,y):
				n = len(self.stack)
				for i in range(n):
					j = n-1-i
					obj = self.stack[j]
					if coordsInArea(x,y,[obj.xy1,obj.xy2]):
						if obj.onclickInside != None:
							obj.onclickInside(x,y,obj.data)
							break 		# we quit the for loop
					elif obj.onclickOutside != None:
						obj.onclickOutside(x,y,obj.data)
						break 			# we quit the for loop


	def stopListenerThread(self):
		self.isInputThreadStarted = False
		print("input thread stopped")








## USAGE : 
# screen = ScreenStackManager('Main')
# screen.addObj(obj)
# screen.invertObj(obj,5)
# screen.setStackLevel(obj,-1)
# screen.removeObj(obj)


# IMPORTANT NOTE : 
# The stack list holds the objecs themselves and not a copy.
# Which means that if you update an object, it is updated on the stack at the same time
# Which means it will work well.