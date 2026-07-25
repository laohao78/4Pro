#!/usr/bin/env python3
"""NDT map→livox_frame + FAST_LIO odom→livox_frame → TF map→odom"""
import rospy
import tf2_ros
import tf.transformations as tft
import numpy as np
from geometry_msgs.msg import PoseStamped, TransformStamped

class NdtOdomBridge:
    def __init__(self):
        rospy.init_node('ndt_odom_bridge')

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster()

        self.sub = rospy.Subscriber('/ndt_pose', PoseStamped, self.callback)
        rospy.loginfo("ndt_odom_bridge: map->odom ready")

    def callback(self, msg):
        # msg = map_T_livox
        map_T_livox = tft.quaternion_matrix([
            msg.pose.orientation.x, msg.pose.orientation.y,
            msg.pose.orientation.z, msg.pose.orientation.w])
        map_T_livox[0, 3] = msg.pose.position.x
        map_T_livox[1, 3] = msg.pose.position.y
        map_T_livox[2, 3] = msg.pose.position.z

        # Get odom_T_livox from FAST_LIO
        try:
            tf = self.tf_buffer.lookup_transform(
                'odom', 'livox_frame', rospy.Time(0), rospy.Duration(0.1))
        except:
            return

        odom_T_livox = tft.quaternion_matrix([
            tf.transform.rotation.x, tf.transform.rotation.y,
            tf.transform.rotation.z, tf.transform.rotation.w])
        odom_T_livox[0, 3] = tf.transform.translation.x
        odom_T_livox[1, 3] = tf.transform.translation.y
        odom_T_livox[2, 3] = tf.transform.translation.z

        # map_T_odom = map_T_livox × inverse(odom_T_livox)
        map_T_odom = np.dot(map_T_livox, tft.inverse_matrix(odom_T_livox))

        q = tft.quaternion_from_matrix(map_T_odom)
        t = tft.translation_from_matrix(map_T_odom)

        ts = TransformStamped()
        ts.header.stamp = msg.header.stamp
        ts.header.frame_id = 'map'
        ts.child_frame_id = 'odom'
        ts.transform.translation.x = t[0]
        ts.transform.translation.y = t[1]
        ts.transform.translation.z = t[2]
        ts.transform.rotation.x = q[0]
        ts.transform.rotation.y = q[1]
        ts.transform.rotation.z = q[2]
        ts.transform.rotation.w = q[3]

        self.tf_broadcaster.sendTransform(ts)

if __name__ == '__main__':
    NdtOdomBridge()
    rospy.spin()
