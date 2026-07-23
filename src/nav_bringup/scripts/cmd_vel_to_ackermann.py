#!/usr/bin/env python3
"""move_base Twist → 速度(占空比)+舵机位置"""
import rospy, math
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64, Int32

class CmdVelToAckermann:
    def __init__(self):
        self.max_vel = rospy.get_param("~max_vel", 0.3)
        self.max_duty = rospy.get_param("~max_duty", 0.15)
        self.min_duty = rospy.get_param("~min_duty", 0.06)
        self.max_omega = rospy.get_param("~max_omega", 0.5)
        self.steer_gain = rospy.get_param("~steer_gain", 200)  # 转向增益
        timeout = rospy.get_param("~timeout", 1.0)

        self.vel_pub = rospy.Publisher("/motor_write_duty", Float64, queue_size=1)
        self.steer_pub = rospy.Publisher("/servo_write_position", Int32, queue_size=1)
        rospy.Subscriber("/cmd_vel", Twist, self.cmd_cb)

        self.last_time = rospy.Time.now()
        self.timeout = rospy.Duration(timeout)
        self.timer = rospy.Timer(rospy.Duration(0.1), self.check_timeout)

    def cmd_cb(self, msg):
        v = msg.linear.x
        omega = msg.angular.z

        # 动态读参, 支持 rosparam set 实时调
        sg = rospy.get_param("~steer_gain", 200)
        md = rospy.get_param("~min_duty", 0.05)
        xd = rospy.get_param("~max_duty", 0.20)
        mv = rospy.get_param("~max_vel", 0.3)
        mo = rospy.get_param("~max_omega", 0.5)

        position = int(1500 - omega / mo * sg)
        position = max(800, min(2200, position))

        dir = 1 if v >= 0 else -1
        duty = abs(v) / mv * xd
        if v != 0:
            duty += abs(omega) / mo * 0.10
            duty = max(duty, md)
        duty = min(duty, xd) * dir

        self.vel_pub.publish(Float64(duty))
        self.steer_pub.publish(Int32(position))
        self.last_time = rospy.Time.now()

    def check_timeout(self, event):
        if rospy.Time.now() - self.last_time > self.timeout:
            self.vel_pub.publish(Float64(0.0))
            self.steer_pub.publish(Int32(1500))

if __name__ == "__main__":
    rospy.init_node("cmd_vel_to_ackermann")
    CmdVelToAckermann()
    rospy.spin()
