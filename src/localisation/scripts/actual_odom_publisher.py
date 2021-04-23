#!/usr/bin/env python

import rospy
import tf2_ros
import tf2_geometry_msgs
from geometry_msgs.msg import TransformStamped


def callback(msg):
    global transform
    transform = msg


def update_time(t):
    """
    Take an existing transform and update the time in the header stamp

    :param t: TransformStamped with time = now
    :return:
    """
    t.header.stamp = rospy.Time.now()
    return t


print('Starting...')
rospy.init_node('actual_odom_publisher')
tf_buf = tf2_ros.Buffer()
tf_lstn = tf2_ros.TransformListener(tf_buf)
br = tf2_ros.TransformBroadcaster()
pose_sub = rospy.Subscriber('/kf/output', TransformStamped, callback)
tf_timeout = rospy.get_param('~tf_timeout', 0.1)
transform = None
print('Ready')


def main():
    rate = rospy.Rate(40)  # Hz
    while not rospy.is_shutdown():
        if transform:
            br.sendTransform(update_time(transform))
        rate.sleep()


if __name__ == '__main__':
    main()
