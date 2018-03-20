#!/usr/bin/env python
import os
import sys
#from os import listdir
import time
import RPi.GPIO as GPIO

#from lib import leds

import logging
#import shutil
import picamera
import picamera.array
#import numpy
import io

from PIL import Image
from PIL import ImageOps
from PIL import ImageStat

##camera = picamera.PiCamera()
##camera.resolution=(1296, 972)
####camera.framerate=10

format_string = '%(levelname)8s:\t%(module)-8s \t%(funcName)15s \t%(message)s'
logging.basicConfig(format=format_string, level=logging.DEBUG)
logging.info('Logging sys active')
old_power1 = 0.0
old_power2 = 0.0

count = 0
critical = 15
safe = 30

last_dist = []

##threshold = 150

pwm1=None
pwm2=None
TRIG = 27
ECHO = 17

TRIG2 = 9
ECHO2 = 11

pins = [26, 19, 13, 6, 5, 11, 12, 9, 10, 22]


camera = picamera.PiCamera()
def calibrate_threshold():
    global camera
    global shutter_speed
    stream = io.BytesIO()
    camera.shutter_speed = shutter_speed
    camera.resolution = (1296, 972)
    camera.capture(stream, format='jpeg')
    stream.seek(0)
    im = Image.open(stream)
##    im.show()  # Debug only
    width = im.size[0]
    centre = width/2
    height = im.size[1]
    crop = im.crop((centre - 100, height - 400, centre + 100, height))
    gray = ImageOps.grayscale(crop)
    gray_mean = ImageStat.Stat(gray).mean[0]
    if gray_mean + 20 < 200:
        threshold = gray_mean + 20
        leds([False, False, True, True, True, False, False, False, False, False])
    else:
        threshold = 200
        leds([False, False, True, True, False, True, True, False, True, True])
    return threshold


def gpio_open():
    '''Initialise GPIO'''
    global TRIG
    global ECHO
    global TRIG2
    global ECHO2
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(TRIG,GPIO.OUT)
    GPIO.setup(ECHO,GPIO.IN)
    GPIO.setup(TRIG2,GPIO.OUT)
    GPIO.setup(ECHO2,GPIO.IN)
    pins=[26,19,13,6,5,11,12,9,10,22]
    GPIO.setup(pins, GPIO.OUT)


def gpio_close():
		GPIO.cleanup()


def startup():
    '''Display a sequence to check leds all working'''
    leds([True, True, True, True, True, True, True, True, True, True])
    time.sleep(0.5)
    leds([True, True, True, True, True, True, True, True, True, False])
    time.sleep(0.5)
    leds([True, True, True, True, True, True, True, True, False, False])
    time.sleep(0.5)
    leds([True, True, True, True, True, True, True, False, False, False])
    time.sleep(0.5)
    leds([True, True, True, True, True, True, False, False, False, False])
    time.sleep(0.5)
    leds([True, True, True, True, True, False, False, False, False, False])
    time.sleep(0.5)
    leds([True, True, True, True, False, False, False, False, False, False])
    time.sleep(0.5)
    leds([True, True, True, False, False, False, False, False, False, False])
    time.sleep(0.5)
    leds([True, True, False, False, False, False, False, False, False, False])
    time.sleep(0.5)
    leds([True, False, False, False, False, False, False, False, False, False])
    time.sleep(0.5)
    leds([False, False, False, False, False, False, False, False, False, False])
    time.sleep(0.5)


def motor_init():
    global pwm1
    global pwm2
    motor1A = 23	  # Input A
    motor1B = 24	  # Input B
    motor1E = 18	  # PWM

    motor2A = 16
    motor2B = 20
    motor2E = 21

    GPIO.setup(motor1A, GPIO.OUT)
    GPIO.setup(motor1B, GPIO.OUT)
    GPIO.setup(motor1E, GPIO.OUT)

    GPIO.setup(motor2A, GPIO.OUT)
    GPIO.setup(motor2B, GPIO.OUT)
    GPIO.setup(motor2E, GPIO.OUT)


def motor(power1, power2):
    global pwm1
    global pwm2
    motor1A = 23	  # Input A
    motor1B = 24	  # Input B
    motor1E = 18	  # PWM

    motor2A = 16
    motor2B = 20
    motor2E = 21

    fd1 = True
    fd0 = False
    fd1 = False

    if power1 > 0:
        fd0 = True

    if power2 > 0:
        fd1 = True

    # setup pins
#    GPIO.setup(motor1A, GPIO.OUT)
#    GPIO.setup(motor1B, GPIO.OUT)
#    GPIO.setup(motor1E, GPIO.OUT)
#
#    GPIO.setup(motor2A, GPIO.OUT)
#    GPIO.setup(motor2B, GPIO.OUT)
#    GPIO.setup(motor2E, GPIO.OUT)

	#motor0

    pwm1 = GPIO.PWM(motor1E, 100)

    if fd0 is True:
        GPIO.output(motor1A, GPIO.HIGH)
        GPIO.output(motor1B, GPIO.LOW)
        GPIO.output(motor1E, GPIO.HIGH)
    else:
        GPIO.output(motor1A, GPIO.LOW)
        GPIO.output(motor1B, GPIO.HIGH)
        GPIO.output(motor1E, GPIO.HIGH)


	#motor1


    pwm2 = GPIO.PWM(motor2E, 100)

    fd1 = not fd1
    if fd1 is True:
        GPIO.output(motor2A, GPIO.HIGH)
        GPIO.output(motor2B, GPIO.LOW)
        GPIO.output(motor2E, GPIO.HIGH)
    else:
        GPIO.output(motor2A, GPIO.LOW)
        GPIO.output(motor2B, GPIO.HIGH)
        GPIO.output(motor2E, GPIO.HIGH)

    pwm1.start(abs(power1))
    pwm2.start(abs(power2))


def measure():
    '''US sensor'''
    global TRIG
    global ECHO

    GPIO.output(TRIG, False)

    time.sleep(0.1)

    GPIO.output(TRIG,True)
    time.sleep(0.00001)
    GPIO.output(TRIG,False)


    count=0
    pulse_start = time.time()
    while GPIO.input(ECHO)==0:
        pulse_start = time.time()
        count = count+1
        if count > 500:
            return 500

    count = 0
    pulse_end = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        count = count+1
        if count > 500:
            return 500


    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150

    distance = round(distance, 2)

    return distance


def clear_images():
    '''Delete any images in folder'''
    dir_name = '/home/pi/pydev'
    folder = os.listdir(dir_name)
    for item in folder:
        if item.endswith('.jpg'):
            os.remove(os.path.join(dir_name, item))
    logging.info('removed files')


#def led_setup():
#    global pins
#
#    for i in range(0, len(pins)):
#        GPIO.setup(pins[i], GPIO.OUT)


def leds(pos):
    '''Set led output, takes boolean list'''
    global pins
    if len(pos) != len(pins):
        logging.error('Input the wrong size')
        return

    for i in range(0, len(pins)):
        GPIO.output(pins[i], pos[i])
    logging.info('Led output')


def dist_smooth():
    '''Temporal smoothing of US sensor'''
    distance_array = []
    for i in range(10):
        distance = measure()
        distance_array.append(distance)
#    else:
#        del last_dist[0]
#        last_dist.append(distance)

    avg_dist = int(sum(distance_array) / len(distance_array))

    return avg_dist


def motor_for_time(power1, power2, time_length):
    motor(power1, power2)
    logging.info('Motor power: ' + str(power1) + ',' + str(power2))
    logging.info('For: ' + str(time_length) + 's')
    time.sleep(time_length)
    motor(0, 0)
    time.sleep(0.5)
    logging.info('Cycle ended')


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
#    polar_array = []  # idea for dev
#    motor_for_time(-100, 0, 0.25)
    rotate = True
    time.sleep(1)
    while rotate is True:
        dist = dist_smooth()
        logging.info('Distance = ' + str(dist))
        if dist < safe:
            motor_for_time(100, -100, 0.2)
            logging.info('Not safe')
            time.sleep(0.2)
            leds([False, False, False, False, False, False, False, True, True, False])
            rotate = True
        elif dist < critical:
            motor_for_time(-100, -100, 0.2)
            logging.info('Critical Distance')
            time.sleep(0.2)
            leds([False, False, False, False, False, False, True, True, True, False])
            rotate = True
        else:
            logging.info('Safe')
            time.sleep(0.2)
            leds([True, True, False, False, False, False, False, False, False, False])
            rotate = False


def paper_check(threshold):
    global camera
    global shutter_speed
    tic = 0
    stream = io.BytesIO()
    camera.shutter_speed = shutter_speed
    camera.resolution = (1296, 972)
    camera.capture(stream, format='jpeg')
    stream.seek(0)
    im = Image.open(stream)
##    im.show()  # Debug only
    width = im.size[0]
    centre = width/2
    height = im.size[1]
    crop = im.crop((centre - 100, height - 400, centre + 100, height))
    gray = ImageOps.grayscale(crop)
    gray_mean = ImageStat.Stat(gray).mean[0]
    logging.info('Brightness value = ' + str(int(gray_mean)))  # Debug only
##    gray.show()  # Debug only
    if int(gray_mean) > int(threshold):
        logging.info('FOUND IT')
        leds([True, False, True, False, True, False, True, False, True, False])
        image = camera_capture()
        fn = 'hit' + '.jpg'
        try:
            image.save(fn)
        except Exception as E:
            logging.info(E)
        if tic < 10:
            leds([False, True, False, True, False, True, False, True, False, True])
            time.sleep(0.2)
            leds([True, False, True, False, True, False, True, False, True, False])
            time.sleep(0.2)
            tic += 1
        logging.info('Continue Searching? y/n')
        rep = input().strip()
        if rep == 'y':
            logging.info('Search resumed')
            return
        elif rep == 'n':
            logging.info('Quiting')
            sys.exit()


def camera_init():
    global camera
##    camera.iso = 200
    time.sleep(2)  # allow agc to settle
    shutter_speed = camera.exposure_speed
    logging.info('Camera init')
    return shutter_speed


def object_detection(safe, threshold):
    '''General Navigation'''
    global count
    global critical
    searching = True
    logging.info('Navigation started')
    while searching:
        dist = dist_smooth()
##        avg_dist = dist_smooth(dist)
        if dist < safe:
            logging.info('Object detected at: ' + str(dist))
            leds([False, False, False, False, False, False, False, True, False, False])
            image = camera_capture()
            fn = 'obj_' + str(count) + '.jpg'
            logging.info('Image saved')
            count += 1
            try:
                image.save(fn)
            except Exception as E:
                logging.info(E)
##            image.show()  # debug only
            ####scan###
            scan(safe, critical)
        elif dist > safe:
            #####drive###
            leds([True, True, True, True, True, True, True, False, False, False])
            logging.info('Distance = ' + str(dist))
            motor_for_time(-100, -100, 0.25)
        #### check for white paper###
        paper_check(threshold)
        time.sleep(1)  # decrease for smoother travel




gpio_open()
motor_init()
#led_setup()
logging.info('Buggy system running')
startup()
shutter_speed = camera_init()
threshold = calibrate_threshold()
logging.info('Threshold set to: ' + str(int(threshold)))
logging.info('Shutter speed set to:' + str(shutter_speed))
clear_images()
logging.info('Safe Distance set to: ' + str(safe))
logging.info('Critical Distance set to: ' + str(critical))
object_detection(safe, threshold)

##paper_check(10)
##image = camera_capture()
##image.show()
##print(type(image))
##image.save('a.jpg')
##r, g, b = image_to_array(image)
##r.show()
##g.show()
##b.show()
gpio_close()
