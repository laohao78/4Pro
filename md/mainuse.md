# 前轮转向小车 Mid360 导航方案

## 一、现状分析

| 项目 | 当前状态 |
|------|----------|
| 平台 | Jetson Xavier NX / Ubuntu 20.04 / ROS1 Noetic |
| 底盘 | 前轮转向 (Ackermann)，串口通信，接收 `/motor_write_velocity` + `/servo_write_delta` |
| 雷达 | Livox Mid360，驱动 `livox_ros_driver2`，输出 `/livox/lidar` |
| 里程计/SLAM | FAST_LIO，输出 LiDAR Odometry |
| 定位 | FAST_LIO_LOCALIZATION (PCD 配准) / NDT Localizer |
| 已有控制 | PID 速度闭环、纯追踪路径跟踪 (pure pursuit)、车道保持 (LKS)、预碰撞安全 (PCS) |
| 传感器 | GPS (`gps_data`)、IMU (`wit_ros_imu`)、激光测距 (`laserranging_data`) |

**底盘接口（关键）：**
- `/motor_write_velocity` (Float64) — 电机速度控制
- `/servo_write_delta` (Float64) — 舵机转向角度，范围 ±20° (弧度制)
- 轴距 L = 0.264m，最大转向角 = 20°

## 二、导航架构总览

```
┌──────────────┐     ┌───────────────┐     ┌──────────────────┐
│   Mid360     │────▶│   FAST_LIO    │────▶│  /Odometry        │
│  /livox/lidar│     │   (建图/里程计) │     │  (里程计消息)      │
└──────────────┘     └───────────────┘     └────────┬─────────┘
                                                    │
                   ┌───────────────┐                 │ TF
                   │ FAST_LIO_LOC  │◀────────────────┤
                   │ / NDT Localizer│                 │
                   │ (全局重定位)    │                 │
                   └───────┬───────┘                 │
                           │                         │
              map→odom TF  │                         │
                           ▼                         ▼
┌──────────────┐     ┌──────────────────────────────────────────┐
│  map_server  │────▶│              move_base                    │
│  (栅格地图)   │     │  ┌─────────────┐  ┌──────────────────┐   │
│  .pgm + .yaml│     │  │ global_planner│  │ teb_local_planner│   │
└──────────────┘     │  │  (A*/Dijkstra)│  │  (Ackermann 兼容) │   │
                     │  └─────────────┘  └────────┬─────────┘   │
                     │  ┌──────────────────────────┘             │
                     │  │  costmap_2d (全局 + 局部代价地图)        │
                     │  └──────────────────────────────────────────┘
                     └──────────────┬───────────────────────────┘
                                    │ /cmd_vel  (geometry_msgs/Twist)
                                    ▼
                     ┌──────────────────────────────┐
                     │   cmd_vel_to_ackermann       │
                     │   Twist → 速度 + 转向角       │
                     │   (自己写的转换节点)           │
                     └──────────────┬───────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               │
            /motor_write_   /servo_write_          │
            velocity        delta                  │
                    │               │               │
                    ▼               ▼               │
            ┌───────────────────────────────┐      │
            │        PID 速度闭环            │      │
            └───────────────┬───────────────┘      │
                            │                      │
                            ▼                      ▼
                    ┌──────────────────────────────────┐
                    │         底盘串口 (Mcu)             │
                    │  电机 duty + 舵机 position 指令     │
                    └──────────────────────────────────┘
```

## 三、需要安装的 ROS 包

```bash
# 1. 导航核心
sudo apt install ros-noetic-move-base
sudo apt install ros-noetic-map-server
sudo apt install ros-noetic-global-planner

# 2. TEB 局部规划器 (支持 Ackermann)
sudo apt install ros-noetic-teb-local-planner

# 3. 点云处理相关
sudo apt install ros-noetic-pointcloud-to-laserscan
sudo apt install ros-noetic-pcl-ros
sudo apt install ros-noetic-costmap-2d
```

## 四、实施步骤

### 步骤 1：搭建 TF 树

需要发布的静态/动态 TF：

```
map → odom → base_footprint → base_link → [mid360, imu, gps]
```

| TF | 类型 | 说明 |
|----|------|------|
| map → odom | 动态 | FAST_LIO_LOCALIZATION / NDT 提供 |
| odom → base_footprint | 动态 | FAST_LIO 里程计提供 |
| base_footprint → base_link | 静态 | z 轴偏移 (雷达离地高度) |
| base_link → mid360 | 静态 | 雷达相对 base_link 的 x,y,z 偏移 |

**关键参数（需实车测量）：**

```yaml
# 雷达相对于底盘中心的偏移 (单位: 米)
lidar_offset_x: ???   # 前后方向
lidar_offset_y: ???   # 左右方向
lidar_offset_z: ???   # 高度

# 雷达相对于地面的高度
sensor_height: ???    # 影响地面分割
```

### 步骤 2：生成栅格地图

**方法 A：用 FAST_LIO 建图后转换**
```bash
# 1. 启动 mapping 模式，遥控车走一圈
# 2. 保存 PCD 点云
# 3. 用 pcd2pgm 工具将 PCD 转成栅格地图 (需要安装 octomap)
sudo apt install ros-noetic-octomap-server
# 或用 pcl_ros 工具手动转换
```

**方法 B：用 slam_toolbox / gmapping**
```bash
# 先将 Mid360 点云转为 2D laser scan
sudo apt install ros-noetic-slam-toolbox
# 或用 pointcloud_to_laserscan 转换后喂给 gmapping
```

### 步骤 3：配置 move_base + TEB

TEB 是唯一原生支持 Ackermann (car-like) 的 ROS1 局部规划器。关键配置：

```yaml
# teb_local_planner_params.yaml

TebLocalPlannerROS:

  # ===== 机器人模型 =====
  cmd_angle_instead_rotvel: true          # 输出转向角而非角速度
  wheelbase: 0.264                        # 轴距 (米)
  max_vel_x: 1.0                          # 最大前进速度
  max_vel_x_backwards: 0.3                # 最大后退速度
  max_vel_theta: 0.5                      # 最大角速度
  acc_lim_x: 0.5                          # 线加速度
  acc_lim_theta: 1.0                      # 角加速度
  min_turning_radius: 0.72                # 最小转弯半径 = wheelbase / tan(20°) ≈ 0.264 / 0.364 ≈ 0.725m

  # ===== 轨迹优化 =====
  min_obstacle_dist: 0.3                  # 最小障碍物距离
  inflation_dist: 0.5                     # 膨胀距离
  include_costmap_obstacles: true
  costmap_obstacles_behind_robots_dist: 1.0

  # ===== 前向约束 (Ackermann 不能原地转) =====
  feasibility_check_no_poses: 4           # 检查轨迹可行性
  exact_arc_length: true                  # 精确弧长计算
```

**move_base 全局配置：**

```yaml
# move_base_params.yaml

# 控制器频率
controller_frequency: 10.0
planner_frequency: 1.0

# 代价地图
global_costmap:
  global_frame: map
  robot_base_frame: base_footprint
  update_frequency: 2.0
  publish_frequency: 1.0
  static_map: true
  rolling_window: false

local_costmap:
  global_frame: odom
  robot_base_frame: base_footprint
  update_frequency: 5.0
  publish_frequency: 2.0
  static_map: false
  rolling_window: true
  width: 10.0
  height: 10.0
  resolution: 0.05
```

### 步骤 4：写 cmd_vel → Ackermann 转换节点 ⚠️ 核心工作

`move_base` 输出 `geometry_msgs/Twist`，需要转换为你的底盘接口。

**新建 ROS 包：**

```python
#!/usr/bin/env python3
# node: cmd_vel_to_ackermann.py

import rospy
import math
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64

class CmdVelToAckermann:
    def __init__(self):
        self.wheelbase = rospy.get_param("~wheelbase", 0.264)  # 轴距
        self.max_steering_angle = rospy.get_param("~max_steering_angle", math.radians(20))  # 最大转角
        
        self.vel_pub = rospy.Publisher("/motor_write_velocity", Float64, queue_size=1)
        self.steer_pub = rospy.Publisher("/servo_write_delta", Float64, queue_size=1)
        self.cmd_sub = rospy.Subscriber("/cmd_vel", Twist, self.cmd_cb)
        
        self.timeout = rospy.get_param("~timeout", 0.5)
        self.last_cmd_time = rospy.Time.now()
        
        # 超时检测定时器
        rospy.Timer(rospy.Duration(0.1), self.check_timeout)
    
    def cmd_cb(self, msg):
        # 提取线速度和角速度
        v = msg.linear.x
        omega = msg.angular.z
        
        if abs(v) < 0.01:
            steering_angle = 0.0
        else:
            # Ackermann: tan(δ) = L * ω / v
            steering_angle = math.atan2(self.wheelbase * omega, v)
        
        # 限幅
        steering_angle = max(-self.max_steering_angle, min(self.max_steering_angle, steering_angle))
        
        self.vel_pub.publish(Float64(v))
        self.steer_pub.publish(Float64(steering_angle))
        self.last_cmd_time = rospy.Time.now()
    
    def check_timeout(self, event):
        if (rospy.Time.now() - self.last_cmd_time).to_sec() > self.timeout:
            self.vel_pub.publish(Float64(0.0))
            self.steer_pub.publish(Float64(0.0))
```

### 步骤 5：编写 launch 文件

```xml
<!-- bringup_nav.launch -->
<launch>
    <!-- ===== 全局定位 ===== -->
    <include file="$(find fast_lio_localization)/launch/mid360_localization.launch">
        <arg name="map" value="$(find my_nav)/map/my_map.pcd"/>
    </include>

    <!-- ===== 栅格地图 ===== -->
    <node pkg="map_server" type="map_server" name="map_server"
          args="$(find my_nav)/map/my_map.yaml"/>

    <!-- ===== move_base ===== -->
    <node pkg="move_base" type="move_base" name="move_base" output="screen">
        <rosparam file="$(find my_nav)/config/costmap_common.yaml" command="load"/>
        <rosparam file="$(find my_nav)/config/global_costmap.yaml" command="load"/>
        <rosparam file="$(find my_nav)/config/local_costmap.yaml" command="load"/>
        <rosparam file="$(find my_nav)/config/move_base_params.yaml" command="load"/>
        <rosparam file="$(find my_nav)/config/teb_local_planner_params.yaml" command="load"/>
    </node>

    <!-- ===== cmd_vel → Ackermann 转换 ===== -->
    <node pkg="my_nav" type="cmd_vel_to_ackermann.py" name="cmd_vel_converter" output="screen">
        <param name="wheelbase" value="0.264"/>
        <param name="max_steering_angle" value="0.349"/>  <!-- 20° -->
        <param name="timeout" value="0.5"/>
    </node>

    <!-- ===== PID 速度闭环 ===== -->
    <node pkg="PID" type="ROSPY_Moto_PID_202404v1.py" name="PID_controller"/>
</launch>
```

### 步骤 6：Mid360 点云转 laser scan

move_base 的 costmap 默认用 2D laser scan，需要转换：

```bash
sudo apt install ros-noetic-pointcloud-to-laserscan
```

```xml
<node pkg="pointcloud_to_laserscan" type="pointcloud_to_laserscan_node" name="pointcloud_to_laserscan">
    <remap from="cloud_in" to="/livox/lidar/pointcloud"/>
    <remap from="scan" to="/scan"/>
    <param name="target_frame" value="base_link"/>
    <param name="angle_min" value="-3.14159"/>
    <param name="angle_max" value="3.14159"/>
    <param name="range_min" value="0.3"/>
    <param name="range_max" value="40.0"/>
    <param name="min_height" value="-0.3"/>   <!-- 过滤地面以下 -->
    <param name="max_height" value="0.5"/>    <!-- 过滤过高点 -->
    <param name="concurrency_level" value="2"/>
</node>
```

## 五、待测量参数清单 ⚠️

实车部署前必须确认：

| 参数 | 符号 | 当前值 | 说明 |
|------|------|--------|------|
| 轴距 | L | 0.264m | 前轮轴到后轮轴距离 |
| 最大转向角 | δ_max | ±20° | 舵机物理限幅 |
| 最小转弯半径 | R_min | ~0.73m | L / tan(δ_max) |
| 雷达 x 偏移 | lidar_x | ? | 雷达到底盘中心前后偏移 |
| 雷达 y 偏移 | lidar_y | ? | 雷达到底盘中心左右偏移 |
| 雷达高度 | sensor_height | ? | 雷达离地高度 |
| 车体半径 | robot_radius | ? | 用于 costmap 膨胀 |

## 六、调试流程建议

1. **先调 TF** — `rosrun tf view_frames` 看 TF 树是否完整
2. **先跑定位** — 确保 map→odom→base_link 连通
3. **先用纯遥控** — 遥控车走一圈，录 bag，离线调 costmap 参数
4. **先开 global planner** — 只发目标点，看全局路径对不对
5. **再开 TEB** — 低速>高速逐步调
6. **最后上实车** — 先在空旷场地低速测试

## 七、文件结构规划

```
src/my_nav/
├── CMakeLists.txt
├── package.xml
├── config/
│   ├── costmap_common.yaml
│   ├── global_costmap.yaml
│   ├── local_costmap.yaml
│   ├── move_base_params.yaml
│   └── teb_local_planner_params.yaml
├── launch/
│   └── bringup_nav.launch
├── map/
│   ├── my_map.pgm
│   └── my_map.yaml
└── scripts/
    └── cmd_vel_to_ackermann.py
```
