#pragma once
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl/registration/icp.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl/io/pcd_io.h>
#include <pcl_conversions/pcl_conversions.h>
#include <ros/ros.h>
#include <sensor_msgs/PointCloud2.h>
#include <geometry_msgs/PoseWithCovarianceStamped.h>
#include <geometry_msgs/TransformStamped.h>
#include <tf2_ros/transform_broadcaster.h>
#include <tf2_ros/transform_listener.h>
#include <tf2_ros/buffer.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.h>
#include <Eigen/Geometry>
#include <string>
#include <memory>
#include <thread>
#include <mutex>
#include <filesystem>

namespace icp {
using PointCloudXYZI = pcl::PointCloud<pcl::PointXYZI>;
using PointCloudXYZIN = pcl::PointCloud<pcl::PointXYZINormal>;

class IcpNode {
public:
  IcpNode(ros::NodeHandle &nh, ros::NodeHandle &pnh);
  ~IcpNode();
private:
  void pointcloudCallback(const sensor_msgs::PointCloud2::ConstPtr &msg);
  void initialPoseCallback(const geometry_msgs::PoseWithCovarianceStamped::ConstPtr &msg);
  Eigen::Matrix4d multiAlignSync(PointCloudXYZI::Ptr source, const Eigen::Matrix4d &init_guess);
  PointCloudXYZIN::Ptr addNorm(PointCloudXYZI::Ptr cloud);

  ros::NodeHandle nh_, pnh_;
  ros::Subscriber pointcloud_sub_, initial_pose_sub_;
  std::shared_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
  std::shared_ptr<tf2_ros::Buffer> tf_buffer_;
  std::shared_ptr<tf2_ros::TransformListener> tf_listener_;
  std::unique_ptr<std::thread> tf_publisher_thread_;

  pcl::PointCloud<pcl::PointXYZI>::Ptr cloud_in_;
  pcl::VoxelGrid<pcl::PointXYZI> voxel_rough_filter_, voxel_refine_filter_;
  PointCloudXYZIN::Ptr rough_map_, refine_map_;
  pcl::IterativeClosestPointWithNormals<pcl::PointXYZINormal, pcl::PointXYZINormal> icp_rough_, icp_refine_;

  bool first_scan_, is_ready_, success_;
  double score_, thresh_, xy_offset_, yaw_offset_, yaw_resolution_;
  int rough_iter_, refine_iter_;
  std::string pcd_path_, map_frame_id_, odom_frame_id_, range_odom_frame_id_, laser_frame_id_;
  geometry_msgs::Pose initial_pose_;
  geometry_msgs::TransformStamped map_to_odom_;
  std::mutex mutex_;
};
}
