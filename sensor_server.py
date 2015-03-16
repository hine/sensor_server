#!/usr/bin/python

import smbus
import math
import json

import threading

import time
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.ioloop import PeriodicCallback
from tornado.options import define, options, parse_command_line

# sensor device
class MPU6050:
    #I2C adress
    _address = 0x68
    # Power management registers
    _power_mgmt_1 = 0x6b
    _power_mgmt_2 = 0x6c

    def __init__(self):
        self.bus = smbus.SMBus(1) # or bus = smbus.SMBus(1) for Revision 2 boards
        # Now wake the 6050 up as it starts in sleep mode
        self.bus.write_byte_data(self._address, self._power_mgmt_1, 0)
        self.get_all_data();

    def read_byte(self, adr):
        return self.bus.read_byte_data(self._address, adr)

    def read_word(self, adr):
        high = self.bus.read_byte_data(self._address, adr)
        low = self.bus.read_byte_data(self._address, adr+1)
        val = (high << 8) + low
        return val

    def read_word_2c(self, adr):
        val = self.read_word(adr)
        if (val >= 0x8000):
            return -((65535 - val) + 1)
        else:
            return val

    def dist(self, a,b):
        return math.sqrt((a*a)+(b*b))

    def get_y_rotation(self, x,y,z):
        radians = math.atan2(x, self.dist(y,z))
        return -math.degrees(radians)

    def get_x_rotation(self, x,y,z):
        radians = math.atan2(y, self.dist(x,z))
        return math.degrees(radians)

    def get_all_data(self):
	temperature_raw = self.read_word_2c(0x41);
        gyro_xout = self.read_word_2c(0x43)
        gyro_yout = self.read_word_2c(0x45)
        gyro_zout = self.read_word_2c(0x47)
        accel_xout = self.read_word_2c(0x3b)
        accel_yout = self.read_word_2c(0x3d)
        accel_zout = self.read_word_2c(0x3f)
	temperature = temperature_raw / 340.00 + 36.53
        accel_xout_scaled = accel_xout / 16384.0
        accel_yout_scaled = accel_yout / 16384.0
        accel_zout_scaled = accel_zout / 16384.0

        new_json_data = {}
	new_json_data["temperature"] = temperature
        new_json_data["gyro"] = {}
        new_json_data["gyro"]["x"] = gyro_xout
        new_json_data["gyro"]["y"] = gyro_yout
        new_json_data["gyro"]["z"] = gyro_zout
        new_json_data["accelerometer"] = {}
        new_json_data["accelerometer"]["x"] = accel_xout
        new_json_data["accelerometer"]["y"] = accel_yout
        new_json_data["accelerometer"]["z"] = accel_zout
        new_json_data["rotation"] = {}
        new_json_data["rotation"]["x"] = self.get_x_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled)
        new_json_data["rotation"]["y"] = self.get_y_rotation(accel_xout_scaled, accel_yout_scaled, accel_zout_scaled)

        self.json_data = new_json_data

    def refresh_data(self):
        self.get_all_data()
        t=threading.Timer(0.05, self.refresh_data)
        t.start()

    def get_json_data(self):
        return json.dumps(self.json_data)

# device init
sensor = MPU6050()

# sensor data refresh thread
t=threading.Thread(target = sensor.refresh_data)
t.start()

# WebSocket Server
define("port", default = 8080, help = "run on the given port", type = int)

class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render("index.html")

class SendWebSocket(tornado.websocket.WebSocketHandler):
    #on_message -> receive data
    #write_message -> send data

    def open(self):
        self.i = 0
        self.callback = PeriodicCallback(self._send_message, 50)
        self.callback.start()
        print "WebSocket opened"

    # origin check disabled
    def check_origin(self, origin):
        return True

    def on_message(self, message):
        print message

    def _send_message(self):
        self.write_message(sensor.get_json_data())

    def on_close(self):
        self.callback.stop()
        print "WebSocket closed"

app = tornado.web.Application([
    (r"/", IndexHandler),
    (r"/ws", SendWebSocket),
])

if __name__ == "__main__":
    parse_command_line()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
