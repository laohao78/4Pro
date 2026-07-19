#!/usr/bin/env python3
"""测试: /cmd_vel 直走 → 左转 → 右转"""
import rospy, time
from geometry_msgs.msg import Twist

rospy.init_node("test")
pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1)
rate = rospy.Rate(20)

print("=== 直走 2s ===")
tw = Twist()
tw.linear.x = 0.10
for i in range(40):
    pub.publish(tw)
    rate.sleep()

print("=== 左转 3s ===")
tw.angular.z = 0.13
for i in range(60):
    pub.publish(tw)
    rate.sleep()

print("=== 右转 3s ===")
tw.angular.z = -0.13
for i in range(60):
    pub.publish(tw)
    rate.sleep()

print("=== 停 ===")
pub.publish(Twist())
print("done")
