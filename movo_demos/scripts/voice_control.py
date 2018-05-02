#!/usr/bin/env python
"""--------------------------------------------------------------------
Copyright (c) 2017, Kinova Robotics inc.

All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.
    * Neither the name of the copyright holder nor the names of its contributors
      may be used to endorse or promote products derived from this software
      without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

 \file   voice_control

 \Author Longfei Zhao

 \Platform: Linux/ROS Indigo
--------------------------------------------------------------------"""
import threading
import numpy

import roslib;

roslib.load_manifest('pocketsphinx')
import rospy

from geometry_msgs.msg import Twist
from std_msgs.msg import String


class voice_control:

    def __init__(self):
        rospy.on_shutdown(self._shutdown)

        self._movo_base_cmd_vel = Twist()
        # motion speed
        self._movo_base_maxVx = 0.2
        self._movo_base_maxVy = 0.2
        self._movo_base_maxRz = numpy.radians(30.0)
        self._movo_base_Vx = self._movo_base_maxVx
        self._movo_base_Vy = self._movo_base_maxVy
        self._movo_base_Rz = self._movo_base_maxRz
        # motion direction: linear translation along x, y; rotation along z.
        self._movo_base_ux = 0.0
        self._movo_base_uy = 0.0
        self._movo_base_uz = 0.0

        # subscriber
        self._speech_sub = rospy.Subscriber('recognizer/output', String, self._speechCb)

        # publisher
        self._movo_base_cmd_pub = rospy.Publisher('/movo/base/voice_control/cmd_vel', Twist, queue_size=1)

        # publisher thread
        self._movo_base_cmd_mutex = threading.Lock()
        self._movo_base_cmd_thread = threading.Thread(target=self._thread_run)
        self._movo_base_cmd_thread.start()

        rospy.loginfo('Voice control initialized')
        rospy.spin()


    def _speechCb(self, msg):
        rospy.loginfo(msg.data)

        with self._movo_base_cmd_mutex:
            # set speed of movo base motion
            if msg.data.find("full speed") > -1:
                self._movo_base_Vx = self._movo_base_maxVx
                self._movo_base_Vy = self._movo_base_maxVy
                self._movo_base_Rz = self._movo_base_maxRz
            elif msg.data.find("half speed") > -1:
                self._movo_base_Vx = self._movo_base_maxVx / 2.0
                self._movo_base_Vy = self._movo_base_maxVy / 2.0
                self._movo_base_Rz = self._movo_base_maxRz / 2.0

            # set direction of movo base motion
            if msg.data.find("move forward") > -1:
                self._movo_base_ux = 1.0
                self._movo_base_uy = 0.0
            elif msg.data.find("move backward") > -1:
                self._movo_base_ux = -1.0
                self._movo_base_uy = 0.0
            elif msg.data.find("move left") > -1:
                self._movo_base_ux = 0.0
                self._movo_base_uy = 1.0
            elif msg.data.find("move right") > -1:
                self._movo_base_ux = 0.0
                self._movo_base_uy = -1.0
            elif msg.data.find("stop") > -1 or msg.data.find("halt") > -1:
                self._movo_base_ux = 0.0
                self._movo_base_uy = 0.0
            else:
                pass



    def _thread_run(self):
        rospy.loginfo('voice control movo base command publisher thread is running')
        rate = rospy.Rate(10)
        while not rospy.is_shutdown():
            with self._movo_base_cmd_mutex:
                self._movo_base_cmd_vel.linear.x = self._movo_base_ux * self._movo_base_Vx
                self._movo_base_cmd_vel.linear.y = self._movo_base_uy * self._movo_base_Vy
                self._movo_base_cmd_pub.publish(self._movo_base_cmd_vel)
                rate.sleep()

    def _shutdown(self):
        # stop the robot!
        self._movo_base_cmd_vel.linear.x = 0.0
        self._movo_base_cmd_vel.linear.y = 0.0
        self._movo_base_cmd_pub.publish(self._movo_base_cmd_vel)
        pass


if __name__ == "__main__":
    rospy.init_node('voice_control')
    try:
        rospy.loginfo('Initializing voice control')
        voice_control()
    except:
        rospy.logerr("voice control initialized failed")
        pass
