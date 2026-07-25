#include "icp_localizer/icp_registration.hpp"
#include <pcl/features/normal_3d.h>
#include <chrono>

namespace icp {

IcpNode::IcpNode(ros::NodeHandle &nh, ros::NodeHandle &pnh)
    : nh_(nh), pnh_(pnh), rough_iter_(10), refine_iter_(5), first_scan_(true) {
  is_ready_ = false;
  cloud_in_ = PointCloudXYZI::Ptr(new PointCloudXYZI);

  double rough_leaf_size = pnh_.param("rough_leaf_size", 0.4);
  double refine_leaf_size = pnh_.param("refine_leaf_size", 0.1);
  voxel_rough_filter_.setLeafSize(rough_leaf_size, rough_leaf_size, rough_leaf_size);
  voxel_refine_filter_.setLeafSize(refine_leaf_size, refine_leaf_size, refine_leaf_size);

  pcd_path_ = pnh_.param<std::string>("pcd_path", "");
  if (!std::filesystem::exists(pcd_path_)) {
    ROS_ERROR("Invalid pcd_path: %s", pcd_path_.c_str());
    throw std::runtime_error("Invalid pcd path");
  }

  PointCloudXYZI::Ptr cloud(new PointCloudXYZI);
  pcl::PCDReader reader; reader.read(pcd_path_, *cloud);
  voxel_refine_filter_.setInputCloud(cloud); voxel_refine_filter_.filter(*cloud);
  refine_map_ = addNorm(cloud);
  PointCloudXYZI::Ptr pt_rough(new PointCloudXYZI), pt_filtered(new PointCloudXYZI);
  pcl::copyPointCloud(*refine_map_, *pt_rough);
  voxel_rough_filter_.setInputCloud(pt_rough); voxel_rough_filter_.filter(*pt_filtered);
  rough_map_ = addNorm(pt_filtered);

  icp_rough_.setMaximumIterations(rough_iter_); icp_rough_.setInputTarget(rough_map_);
  icp_refine_.setMaximumIterations(refine_iter_); icp_refine_.setInputTarget(refine_map_);
  ROS_INFO("PCD loaded: refine=%ld rough=%ld", refine_map_->size(), rough_map_->size());

  map_frame_id_ = pnh_.param<std::string>("map_frame_id", "map");
  odom_frame_id_ = pnh_.param<std::string>("odom_frame_id", "odom");
  range_odom_frame_id_ = pnh_.param<std::string>("range_odom_frame_id", "odom");
  laser_frame_id_ = pnh_.param<std::string>("laser_frame_id", "livox_frame");

  thresh_ = pnh_.param("thresh", 0.15);
  xy_offset_ = pnh_.param("xy_offset", 2.0);
  yaw_offset_ = pnh_.param("yaw_offset", 180.0) * M_PI / 180.0;
  yaw_resolution_ = pnh_.param("yaw_resolution", 30.0) * M_PI / 180.0;

  std::vector<double> init_vec;
  pnh_.param("initial_pose", init_vec, std::vector<double>{0,0,0,0,0,0});
  initial_pose_.position.x = init_vec[0]; initial_pose_.position.y = init_vec[1]; initial_pose_.position.z = init_vec[2];
  tf2::Quaternion q; q.setRPY(init_vec[3], init_vec[4], init_vec[5]);
  initial_pose_.orientation = tf2::toMsg(q);

  std::string pt_topic = pnh_.param<std::string>("pointcloud_topic", "/cloud_registered_body");
  pointcloud_sub_ = nh_.subscribe(pt_topic, 10, &IcpNode::pointcloudCallback, this);
  initial_pose_sub_ = nh_.subscribe("/initialpose", 10, &IcpNode::initialPoseCallback, this);

  tf_broadcaster_ = std::make_shared<tf2_ros::TransformBroadcaster>();
  tf_buffer_ = std::make_shared<tf2_ros::Buffer>();
  tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);

  tf_publisher_thread_ = std::make_unique<std::thread>([this]() {
    ros::Rate rate(100);
    while (ros::ok()) {
      { std::lock_guard<std::mutex> lock(mutex_);
        if (is_ready_) {
          map_to_odom_.header.stamp = ros::Time::now();
          map_to_odom_.header.frame_id = map_frame_id_;
          map_to_odom_.child_frame_id = odom_frame_id_;
          tf_broadcaster_->sendTransform(map_to_odom_);
        }
      }
      rate.sleep();
    }
  });
  ROS_INFO("icp_localizer ready");
}

IcpNode::~IcpNode() { if (tf_publisher_thread_->joinable()) tf_publisher_thread_->join(); }

void IcpNode::pointcloudCallback(const sensor_msgs::PointCloud2::ConstPtr &msg) {
  pcl::fromROSMsg(*msg, *cloud_in_);
  if (first_scan_) {
    auto pose_msg = boost::make_shared<geometry_msgs::PoseWithCovarianceStamped>();
    pose_msg->header = msg->header; pose_msg->pose.pose = initial_pose_;
    initialPoseCallback(pose_msg); first_scan_ = false;
  }
}

void IcpNode::initialPoseCallback(const geometry_msgs::PoseWithCovarianceStamped::ConstPtr &msg) {
  Eigen::Vector3d pos(msg->pose.pose.position.x, msg->pose.pose.position.y, msg->pose.pose.position.z);
  Eigen::Quaterniond quat(msg->pose.pose.orientation.w, msg->pose.pose.orientation.x, msg->pose.pose.orientation.y, msg->pose.pose.orientation.z);
  Eigen::Matrix4d init_guess; init_guess.block<3,3>(0,0)=quat.toRotationMatrix(); init_guess.block<3,1>(0,3)=pos; init_guess(3,3)=1;

  ROS_INFO("ICP aligning...");
  Eigen::Matrix4d m2l = multiAlignSync(cloud_in_, init_guess);
  if (!success_) { m2l = init_guess; ROS_ERROR("ICP failed, using initial guess"); }

  Eigen::Matrix4d l2o = Eigen::Matrix4d::Identity();
  try {
    auto tf = tf_buffer_->lookupTransform(laser_frame_id_, range_odom_frame_id_, msg->header.stamp, ros::Duration(10.0));
    Eigen::Vector3d t(tf.transform.translation.x, tf.transform.translation.y, tf.transform.translation.z);
    Eigen::Quaterniond qi(tf.transform.rotation.w, tf.transform.rotation.x, tf.transform.rotation.y, tf.transform.rotation.z);
    l2o.block<3,3>(0,0)=qi.toRotationMatrix(); l2o.block<3,1>(0,3)=t;
  } catch (tf2::TransformException &ex) {
    std::lock_guard<std::mutex> lock(mutex_); ROS_ERROR("%s", ex.what()); is_ready_=false; return;
  }

  Eigen::Matrix4d result = m2l * l2o.matrix().cast<double>();
  { std::lock_guard<std::mutex> lock(mutex_);
    map_to_odom_.transform.translation.x=result(0,3); map_to_odom_.transform.translation.y=result(1,3); map_to_odom_.transform.translation.z=result(2,3);
    Eigen::Matrix3d rot = result.block<3,3>(0,0); Eigen::Quaterniond qo(rot);
    map_to_odom_.transform.rotation.w=qo.w(); map_to_odom_.transform.rotation.x=qo.x(); map_to_odom_.transform.rotation.y=qo.y(); map_to_odom_.transform.rotation.z=qo.z();
    is_ready_=true;
  }
}

Eigen::Matrix4d IcpNode::multiAlignSync(PointCloudXYZI::Ptr source, const Eigen::Matrix4d &init_guess) {
  auto r2rpy = [](Eigen::Matrix3d &rot) -> Eigen::Vector3d {
    return Eigen::Vector3d(std::atan2(rot(2,1),rot(2,2)), asin(-rot(2,0)), std::atan2(rot(1,0),rot(0,0)));
  };
  success_=false;
  Eigen::Vector3d xyz = init_guess.block<3,1>(0,3);
  Eigen::Matrix3d rotation = init_guess.block<3,3>(0,0);
  Eigen::Vector3d rpy = r2rpy(rotation);
  Eigen::AngleAxisf rollA(rpy(0),Eigen::Vector3f::UnitX()), pitchA(rpy(1),Eigen::Vector3f::UnitY());

  std::vector<Eigen::Matrix4f> cands; Eigen::Matrix4f tmp;
  int yc = static_cast<int>(yaw_offset_/yaw_resolution_);
  for (int i=-1;i<=1;i++)
    for (int j=-1;j<=1;j++)
      for (int k=-yc;k<=yc;k++) {
        Eigen::Vector3f pp(xyz(0)+i*xy_offset_,xyz(1)+j*xy_offset_,xyz(2));
        Eigen::AngleAxisf yawA(rpy(2)+k*yaw_resolution_,Eigen::Vector3f::UnitZ());
        tmp.setIdentity(); tmp.block<3,3>(0,0)=(rollA*pitchA*yawA).toRotationMatrix(); tmp.block<3,1>(0,3)=pp;
        cands.push_back(tmp);
      }

  PointCloudXYZI::Ptr rs(new PointCloudXYZI), refs(new PointCloudXYZI);
  voxel_rough_filter_.setInputCloud(source); voxel_rough_filter_.filter(*rs);
  voxel_refine_filter_.setInputCloud(source); voxel_refine_filter_.filter(*refs);
  PointCloudXYZIN::Ptr rsn=addNorm(rs), refsn=addNorm(refs), ap(new PointCloudXYZIN);

  Eigen::Matrix4f best_rt; double best_rs=10.0; bool rc=false;
  auto tic=std::chrono::system_clock::now();
  for (Eigen::Matrix4f &ip : cands) {
    icp_rough_.setInputSource(rsn); icp_rough_.align(*ap, ip);
    if (!icp_rough_.hasConverged()) continue;
    double s=icp_rough_.getFitnessScore(); if (s>2*thresh_) continue;
    if (s<best_rs) { best_rs=s; rc=true; best_rt=icp_rough_.getFinalTransformation(); }
  }
  if (!rc) return Eigen::Matrix4d::Zero();

  icp_refine_.setInputSource(refsn); icp_refine_.align(*ap, best_rt);
  score_=icp_refine_.getFitnessScore();
  if (!icp_refine_.hasConverged() || score_>thresh_) return Eigen::Matrix4d::Zero();

  success_=true;
  auto toc=std::chrono::system_clock::now();
  ROS_INFO("ICP done: %ldms score=%.4f", std::chrono::duration_cast<std::chrono::milliseconds>(toc-tic).count(), score_);
  return icp_refine_.getFinalTransformation().cast<double>();
}

PointCloudXYZIN::Ptr IcpNode::addNorm(PointCloudXYZI::Ptr cloud) {
  pcl::PointCloud<pcl::Normal>::Ptr normals(new pcl::PointCloud<pcl::Normal>);
  pcl::search::KdTree<pcl::PointXYZI>::Ptr tree(new pcl::search::KdTree<pcl::PointXYZI>);
  tree->setInputCloud(cloud);
  pcl::NormalEstimation<pcl::PointXYZI,pcl::Normal> ne; ne.setInputCloud(cloud); ne.setSearchMethod(tree); ne.setKSearch(15); ne.compute(*normals);
  PointCloudXYZIN::Ptr out(new PointCloudXYZIN); pcl::concatenateFields(*cloud,*normals,*out);
  return out;
}

} // namespace icp
