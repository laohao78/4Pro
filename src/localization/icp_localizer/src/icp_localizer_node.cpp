#include "icp_localizer/icp_registration.hpp"
int main(int argc, char **argv) {
  ros::init(argc, argv, "icp_localizer");
  ros::NodeHandle nh, pnh("~");
  try { icp::IcpNode node(nh, pnh); ros::spin(); }
  catch (const std::exception &e) { ROS_ERROR("Failed: %s", e.what()); return 1; }
  return 0;
}
