#!/usr/bin/env python
import os
import sys
from os import listdir
import time
import RPi.GPIO as GPIO

from lib import gpio_open
from lib import gpio_close
from lib import motor
from lib import measure
from lib import measure2
#from lib import leds

import logging
import shutil
import picamera
import picamera.array
import numpy
import io
from PIL import Image

##camera = picamera.PiCamera()
##camera.resolution=(1296, 972)
####camera.framerate=10

format_string = '%(levelname)8s:\t%(module)-10s \t%(funcName)s \t%(message)s'
logging.basicConfig(format=format_string, level=logging.DEBUG)
logging.info('Logging sys active')
old_power1 = 0.0
old_power2 = 0.0

count = 0
critical = 10

last_dist = []

camera = picamera.PiCamera()

def clear_images():
    '''Delete any images in folder'''
    dir_name = '/home/pi/pydev'
    folder = os.listdir(dir_name)
    for item in folder:
        if item.endswith('.jpg'):
            os.remove(os.path.join(dir_name, item))
    logging.info('removed files')


def leds(pos):
    '''Set led output, takes boolean list'''
    pins = [26, 19, 13, 6]
    if len(pos) != 4:
        logging.error('Input the wrong size')
        return

    for i in range(0, len(pins)):
        GPIO.setup(pins[i], GPIO.OUT)

    for i in range(0, len(pins)):
        GPIO.output(pins[i], pos[i])
    logging.info('Led output')


def dist_smooth(distance):
    '''Temporal smoothing of US sensor'''
    if len(last_dist) < 10:
        last_dist.append(distance)
    else:
        del last_dist[0]
        last_dist.append(distance)

    avg_dist = int(sum(last_dist) / len(last_dist))

    return avg_dist


def motor_for_time(power1, power2, time_length):
    motor(power1, power2)
    logging.info('motor powered: ' + str(power1) + ',' + str(power2))
    logging.info('power for :' + str(time_length) + 's')
    time.sleep(time_length)
    motor(0, 0)


def camera_capture():
    '''Capture and return an image'''
    stream = io.BytesIO()
    global camera
##        camera.start_preview()  #may be useful for debug
    camera.resolution = (1296, 972)

    time.sleep(2)
    camera.capture(stream, format='jpeg')
    stream.seek(0)
    image = Image.open(stream)
    return image


def image_to_array(im):
    '''Split into channels'''
    im = im.convert('RGB')
    r, g, b = im.split()
    return r, g, b


def scan(safe, critical):
    '''Rotate and record directions'''
    polar_array = []  # idea for dev
    motor_for_time(-50, 0, 1)
    rotate = True
    while rotate:
        dist = measure()
        avg_dist = dist_smooth(dist)
        if avg_dist < safe:
            motor_for_time(100, 0, 0.5)
            logging.info('Not safe')
        elif avg_dist < critical:
            motor_for_time(-100, -100, 1)
            logging.info('Critical Distance')
        else:
            logging.info('Safe')
            rotate = False

def paper_check(threshold):
    global camera
    global shutter_speed
    global awb_gains
    stream = io.BytesIO()
    camera.shutter_speed = shutter_speed
    camera.awb_gains = awb_gains
    camera.resolution = (1296, 972)
    camera.capture(stream, format='jpeg')
    stream.seek(0)
    im = Image.open(stream)
    im = im.point(lambda p: p > threshold and 255)
#    if sum(im)


def camera_init():
    global camera
    camera.iso = 200
    time.sleep(2)  # allow agc to settle
    camera.shutter_speed = camera.exposure_speed
    camera.exposure_mode = 'off'
    g = camera.awb_gains
    camera.awb_mode = 'off'
    camera.awb_gains = g
    return camera.shutter_speed, camera.awb_gains


def object_detection(safe):
    '''General Navigation'''
    global count
    global critical
    searching = True
    logging.info('searching')
    while searching:
        dist = measure()
        avg_dist = dist_smooth(dist)
        if avg_dist < safe:
            logging.info('Object detected')
            image = camera_capture()
            fn = 'obj_' + str(count) + '.jpg'
            count += 1
            try:
                image.save(fn)
            except:
                pass
            image.show()  # debug only
#            time.sleep(0.01)
            ####scan###
            scan(safe,critical)
        elif avg_dist > safe:
            #####drive###
            logging.info('Drive forward')
            motor_for_time(100, 100, 1)
        #### check for white paper###




gpio_open()
shutter_speed, awb_gains = camera_init()
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
