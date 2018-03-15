#!/usr/bin/env python
import os
import sys
from os import listdir
import time
from lib import measure
import RPi.GPIO as GPIO

from lib import gpio_open
from lib import gpio_close
from lib import motor
from lib import measure
from lib import measure2
from lib import leds

import logging
import shutil
import picamera
import picamera.array
import sys
import numpy
import io
from PIL import Image

##camera = picamera.PiCamera()
##camera.resolution=(1296, 972)
####camera.framerate=10

format_string = '%(levelname)8s:\t%(module)-10s \t%(funcName)s \t%(message)s'
logging.basicConfig(format=format_string, level=logging.DEBUG)
logging.info('Logging sys active')
old_power1=0.0
old_power2=0.0

count=0

last_dist=[]

def clear_images():
    '''Delete any images in folder'''
    dir_name = '/home/pi/pydev'
    folder = os.listdir(dir_name)
    for item in folder:
        if item.endswith('.jpg'):
            os.remove(os.path.join(dir_name, item))
    logging.info('removed files')

def dist_smooth(distance):
    '''Temporal smoothing of US sensor'''
    if len(last_dist) < 10:
        last_dist.append(distance)
    else:
        del last_dist[0]
        last_dist.append(distance)

    avg_dist = int(sum(last_dist) / len(last_dist))
    
    return avg_dist


def camera_capture():
    '''Capture and return an image'''
    stream = io.BytesIO()
    with picamera.PiCamera() as camera:
##        camera.start_preview()  #may be useful for debug
        camera.resolution=(1296, 972)
        time.sleep(2)
        camera.capture(stream, format='jpeg')
    stream.seek(0)
    image=Image.open(stream)
    return image

def image_to_array(im):
    '''Split into channels'''
    im=im.convert('RGB')
    r, g, b = im.split()
    return r, g, b

def scan():
    '''Rotate and record directions'''
    
    
def object_detection(safe):
    global count
    searching = True
    logging.info('searching')
    while searching:
        dist = measure()
        avg_dist = dist_smooth(dist)
        if avg_dist > safe:
            a=1
        else:
            logging.info('obj det')
            image = camera_capture()
            fn='obj_' + str(count) + '.jpg'
            count+=1
            try:
                image.save(fn)
            except:
                pass                
            image.show() # debug only
            time.sleep(0.01)


gpio_open()

logging.info('buggy autorun')
clear_images()
object_detection(20)
##image = camera_capture()
##image.show()
##print(type(image))
##image.save('a.jpg')
##r, g, b = image_to_array(image)
##r.show()
##g.show()
##b.show()
gpio_close()
