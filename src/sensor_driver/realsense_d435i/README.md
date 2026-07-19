# 一、项目概述
- 项目名称：realsense D435i 
- 项目简介：
## 版本
- 版本：1.0.0
- 日期：2024.07

# 二、软件构架
- ubuntu 18.04/20.04
- ROS melodic/noetic
- Python 3.6/3.8

# 三、硬件传感器
- 深度摄像头（intel realsense d435i）

# 四、安装教程
- 指导手册：“ `./RTRC_PRO深度摄像头配置202402v1.pdf` “ 

1. 详细环境配置手册参见指导手册 “ `./RTRC_PRO深度摄像头配置202402v1.pdf` “ 


# 五、使用说明
## 5.1 运行官方示例
1、`realsense-viewer`（官方SDK可视化界面）
- 作用：启动IMU并发布数据到ros话题
```shell
$ realsense-viewer
```
## 5.2 launch文件
1、`rs_camera.launch`（启动摄像头ros话题）
- 作用：启动深度摄像头（realsense d435i）并发布数据到ros话题
```shell
$ roslaunch realsense2_camera rs_camera.launch
```

# 六、接口文档
##  ROS 接口
### 1. ROS
-------------------------------------------------------------------------------------------
   节点名称(脚本文件)： `imu` (wit_normal_ros.py)

   | 话题 | 话题类型 | 话题数据类型 | 说明 |
   `imu`话题
   | `//wit/cali` | 接收 | String | 接收数据 | 
   | `/imu` | 发布 | Imu | 发布imu测量数据 | 
   | `/wit/mag` | 发布 | MagneticField | 发布磁力计测量数据 | 


### 2. ROS参数服务器参数（launch文件中设置）
- 具体参见（`./realsense2-ros/realsense2_camera/realsense_d435i启动参数注释.launch`）
-------------------------------------------------------------------------------------------
  <!-- 设备序列号 -->
  <arg name="serial_no"           default=""/>
  <!-- USB端口ID -->
  <arg name="usb_port_id"         default=""/>
  <!-- 设备类型 -->
  <arg name="device_type"         default=""/>
  <!-- JSON配置文件路径 -->
  <arg name="json_file_path"      default=""/>
  <!-- 相机命名空间 -->
  <arg name="camera"              default="camera"/>
  <!-- TF前缀 -->
  <arg name="tf_prefix"           default="$(arg camera)"/>
  <!-- 是否使用外部管理器 -->
  <arg name="external_manager"    default="false"/>
  <!-- 管理器名称 -->
  <arg name="manager"             default="realsense2_camera_manager"/>
  <!-- 输出目标（屏幕或日志文件） -->
  <arg name="output"              default="screen"/>
  <!-- 是否启用节点重启 -->
  <arg name="respawn"              default="false"/>

  <!-- 鱼眼摄像头分辨率宽度 -->
  <arg name="fisheye_width"       default="-1"/>
  <!-- 鱼眼摄像头分辨率高度 -->
  <arg name="fisheye_height"      default="-1"/>
  <!-- 是否启用鱼眼摄像头 -->
  <arg name="enable_fisheye"      default="false"/>

  <!-- 深度摄像头分辨率宽度 -->
  <arg name="depth_width"         default="-1"/>
  <!-- 深度摄像头分辨率高度 -->
  <arg name="depth_height"        default="-1"/>
  <!-- 是否启用深度摄像头 -->
  <arg name="enable_depth"        default="true"/>

  <!-- 置信度图像分辨率宽度 -->
  <arg name="confidence_width"    default="-1"/>
  <!-- 置信度图像分辨率高度 -->
  <arg name="confidence_height"   default="-1"/>
  <!-- 是否启用置信度图像 -->
  <arg name="enable_confidence"   default="true"/>
  <!-- 置信度图像帧率 -->
  <arg name="confidence_fps"      default="-1"/>

  <!-- 红外摄像头分辨率宽度 -->
  <arg name="infra_width"         default="848"/>
  <!-- 红外摄像头分辨率高度 -->
  <arg name="infra_height"        default="480"/>
  <!-- 是否启用红外摄像头 -->
  <arg name="enable_infra"        default="false"/>
  <!-- 是否启用红外摄像头1 -->
  <arg name="enable_infra1"       default="false"/>
  <!-- 是否启用红外摄像头2 -->
  <arg name="enable_infra2"       default="false"/>
  <!-- 是否将红外图像转换为RGB -->
  <arg name="infra_rgb"           default="false"/>

  <!-- 彩色摄像头分辨率宽度 -->
  <arg name="color_width"         default="-1"/>
  <!-- 彩色摄像头分辨率高度 -->
  <arg name="color_height"        default="-1"/>
  <!-- 是否启用彩色摄像头 -->
  <arg name="enable_color"        default="true"/>

  <!-- 鱼眼摄像头帧率 -->
  <arg name="fisheye_fps"         default="-1"/>
  <!-- 深度摄像头帧率 -->
  <arg name="depth_fps"           default="-1"/>
  <!-- 红外摄像头帧率 -->
  <arg name="infra_fps"           default="30"/>
  <!-- 彩色摄像头帧率 -->
  <arg name="color_fps"           default="-1"/>
  <!-- 陀螺仪帧率 -->
  <arg name="gyro_fps"            default="-1"/>
  <!-- 加速度计帧率 -->
  <arg name="accel_fps"           default="-1"/>
  <!-- 是否启用陀螺仪 -->
  <arg name="enable_gyro"         default="false"/>
  <!-- 是否启用加速度计 -->
  <arg name="enable_accel"        default="false"/>

  <!-- 是否启用点云生成 -->
  <arg name="enable_pointcloud"         default="false"/>
  <!-- 点云纹理流类型 -->
  <arg name="pointcloud_texture_stream" default="RS2_STREAM_COLOR"/>
  <!-- 点云纹理索引 -->
  <arg name="pointcloud_texture_index"  default="0"/>
  <!-- 是否允许无纹理点 -->
  <arg name="allow_no_texture_points"   default="false"/>
  <!-- 是否有序点云 -->
  <arg name="ordered_pc"                default="false"/>

  <!-- 是否启用同步 -->
  <arg name="enable_sync"               default="false"/>
  <!-- 是否对齐深度图像 -->
  <arg name="align_depth"               default="false"/>

  <!-- 是否发布TF变换 -->
  <arg name="publish_tf"                default="true"/>
  <!-- TF发布速率 -->
  <arg name="tf_publish_rate"           default="0"/>

  <!-- 过滤器列表 -->
  <arg name="filters"                   default=""/>
  <!-- 裁剪距离 -->
  <arg name="clip_distance"             default="-2"/>
  <!-- 线性加速度协方差 -->
  <arg name="linear_accel_cov"          default="0.01"/>
  <!-- 初始重置 -->
  <arg name="initial_reset"             default="false"/>
  <!-- 重连超时时间 -->
  <arg name="reconnect_timeout"         default="6.0"/>
  <!-- 等待设备超时时间 -->
  <arg name="wait_for_device_timeout"   default="-1.0"/>
  <!-- IMU数据合并方法 -->
  <arg name="unite_imu_method"          default=""/>
  <!-- 外部里程计话题名称 -->
  <arg name="topic_odom_in"             default="odom_in"/>
  <!-- 里程计校准文件路径 -->
  <arg name="calib_odom_file"           default=""/>
  <!-- 是否发布里程计TF变换 -->
  <arg name="publish_odom_tf"           default="true"/>

  <!-- 红外摄像头曝光值1 -->
  <arg name="stereo_module/exposure/1"  default="7500"/>
  <!-- 红外摄像头增益值1 -->
  <arg name="stereo_module/gain/1"      default="16"/>
  <!-- 红外摄像头曝光值2 -->
  <arg name="stereo_module/exposure/2"  default="1"/>
  <!-- 红外摄像头增益值2 -->
  <arg name="stereo_module/gain/2"      default="16"/>
-------------------------------------------------------------------------------------------

# 许可证
说明项目的许可证类型。