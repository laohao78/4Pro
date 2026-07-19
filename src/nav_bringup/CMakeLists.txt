cmake_minimum_required(VERSION 2.8.3)
project(nav_bringup)

find_package(catkin REQUIRED)
catkin_package()

# 只装脚本和 launch 文件
catkin_install_python(PROGRAMS
  scripts/cmd_vel_to_ackermann.py
  scripts/pcd2pgm_node.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch)
install(DIRECTORY config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/config)
install(DIRECTORY rviz/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/rviz)
