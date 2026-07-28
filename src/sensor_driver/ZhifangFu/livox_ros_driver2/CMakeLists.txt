cmake_minimum_required(VERSION 3.0)
project(livox_camera_sync)

find_package(catkin REQUIRED COMPONENTS
  roscpp
  sensor_msgs
  livox_ros_driver2
)

catkin_package()

include_directories(${catkin_INCLUDE_DIRS})

add_executable(sync_node src/sync_node.cpp)
target_link_libraries(sync_node ${catkin_LIBRARIES})

install(TARGETS sync_node
  ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
  LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
  RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch_ROS1/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)
