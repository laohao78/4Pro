#!/usr/bin/env python3
"""TF 转发：把 FAST_LIO 的 camera_init→body 映射为 odom→base_link"""
import rospy
import tf2_ros

class TfRelay:
    def __init__(self):
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster()
        self.last_stamp = None
        self.rate = rospy.Rate(10)  # FAST_LIO 约 10Hz

    def run(self):
        while not rospy.is_shutdown():
            try:
                t = self.tf_buffer.lookup_transform(
                    "camera_init", "body", rospy.Time(0), rospy.Duration(0.1))

                # 去重：相同时间戳不发第二次
                if self.last_stamp == t.header.stamp:
                    self.rate.sleep()
                    continue
                self.last_stamp = t.header.stamp

                t.header.frame_id = "odom"
                t.child_frame_id = "base_link"
                self.tf_broadcaster.sendTransform(t)

            except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                    tf2_ros.ExtrapolationException):
                pass
            self.rate.sleep()

if __name__ == "__main__":
    rospy.init_node("tf_relay")
    TfRelay().run()
