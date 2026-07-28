#include <ros/ros.h>
#include <sensor_msgs/Image.h>
#include <livox_ros_driver2/CustomMsg.h>

using namespace sensor_msgs;
using namespace livox_ros_driver2;

class SyncNode {
public:
    SyncNode(ros::NodeHandle& nh) {
        std::string image_topic, lidar_topic, synced_image_topic, synced_lidar_topic;
        double publish_rate;

        nh.param<std::string>("image_topic", image_topic, "/camera/color/image_raw");
        nh.param<std::string>("lidar_topic", lidar_topic, "/livox/lidar");
        nh.param<std::string>("synced_image_topic", synced_image_topic, "/synced_image");
        nh.param<std::string>("synced_lidar_topic", synced_lidar_topic, "/synced_lidar");
        nh.param<double>("publish_rate", publish_rate, 10.0);

        image_sub = nh.subscribe(image_topic, 10, &SyncNode::image_cbk, this);
        lidar_sub = nh.subscribe(lidar_topic, 10, &SyncNode::lidar_cbk, this);

        image_pub = nh.advertise<Image>(synced_image_topic, 10);
        lidar_pub = nh.advertise<CustomMsg>(synced_lidar_topic, 10);

        ros::Duration period(1.0 / publish_rate);
        timer = nh.createTimer(period, &SyncNode::timerCallback, this);

        ROS_INFO("sync_node: %s+%s → %s+%s @%.1fHz (timer-based)",
                 image_topic.c_str(), lidar_topic.c_str(),
                 synced_image_topic.c_str(), synced_lidar_topic.c_str(), publish_rate);
    }

private:
    ros::Subscriber image_sub;
    ros::Subscriber lidar_sub;
    ros::Publisher image_pub;
    ros::Publisher lidar_pub;
    ros::Timer timer;

    Image last_image_msg;
    CustomMsg last_lidar_msg;
    bool new_image_received = false;
    bool new_lidar_received = false;

    void image_cbk(const ImageConstPtr& msg) {
        last_image_msg = *msg;
        new_image_received = true;
    }

    void lidar_cbk(const CustomMsgConstPtr& msg) {
        last_lidar_msg = *msg;
        new_lidar_received = true;
    }

    void timerCallback(const ros::TimerEvent& event) {
        if (new_image_received && new_lidar_received) {
            ros::Time sync_stamp = last_lidar_msg.header.stamp;
            last_image_msg.header.stamp = sync_stamp;
            image_pub.publish(last_image_msg);
            lidar_pub.publish(last_lidar_msg);
            new_image_received = false;
            new_lidar_received = false;
        }
    }
};

int main(int argc, char** argv) {
    ros::init(argc, argv, "sync_node");
    ros::NodeHandle nh("~");
    SyncNode node(nh);
    ros::spin();
    return 0;
}
