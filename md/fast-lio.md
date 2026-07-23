# FAST-LIO MID360 建图

## 环境

| 组件 | 信息 |
|------|------|
| 平台 | Jetson Orin NX / aarch64 |
| ROS | Noetic (Ubuntu 20.04) |
| LiDAR | Livox Mid360 |
| 驱动 | livox_ros_driver2 |
| 工作空间 | `/home/orin/Desktop/00/FAST_LIO` |

## 源码修改

相比原版 FAST_LIO，做了以下适配：

| 修改 | 文件 | 说明 |
|------|------|------|
| `camera_init` → `odom` | `laserMapping.cpp` | 让 FAST_LIO 直接发导航标准 TF 名 |
| `body` → `livox_frame` | `laserMapping.cpp` | 同上 |
| `livox_ros_driver` → `livox_ros_driver2` | `CMakeLists.txt`, `package.xml`, `*.cpp`, `*.h` | 适配新驱动 |
| `path_en: true` | `config/mid360.yaml` | 开启轨迹话题 |

**不再需要 tf_relay 转发 TF。**

## 0. 编译

首次或修改源码后需要重新编译。

```sh
cd /home/orin/Desktop/00/FAST_LIO

# 单编 fast_lio（改完源码后推荐）
catkin_make --pkg fast_lio

# 全量编译
catkin_make
```

编译报错参考 → 底部「编译报错」表格。

## 1. 启动

**新开两个终端**，都要先 source：

```sh
source /home/orin/Desktop/00/FAST_LIO/devel/setup.bash
```

### 终端 1：雷达驱动

```sh
roslaunch livox_ros_driver2 msg_MID360.launch
```

**关键**：`msg_MID360.launch` 的 `xfer_format=1`（CustomMsg），FAST_LIO 只认这个。

验证：

```sh
rostopic type /livox/lidar
# 必须输出: livox_ros_driver2/CustomMsg
```

### 终端 2：建图

```sh
# 无 RViz（Jetson 上推荐）
roslaunch fast_lio mapping_mid360.launch rviz:=false

# 带 RViz
roslaunch fast_lio mapping_mid360.launch
```

## 2. 可视化

用 Foxglove 或 RViz 远程连接。

| 参数 | 值 |
|------|-----|
| Fixed Frame | `odom` |

| Topic | 类型 | 说明 |
|-------|------|------|
| `/cloud_registered` | PointCloud2 | 当前帧去畸变点云（world 系） |
| `/cloud_registered_body` | PointCloud2 | 当前帧点云（base_link 系） |
| `/Laser_map` | PointCloud2 | 全局累积地图（ikd-Tree 展平） |
| `/Odometry` | Odometry | 里程计（odom → base_link） |
| `/path` | Path | 轨迹路径（需 `path_en: true`） |

CustomMsg 是驱动→FAST_LIO 内部格式，Foxglove 看 LIO 输出的 PointCloud2 话题即可。

### /Odometry 详解

```cpp
odomAftMapped.header.frame_id = "odom";          // world 系
odomAftMapped.child_frame_id  = "livox_frame";   // LiDAR/IMU 本体
// 位置 + 姿态 + 6x6 协方差
// twist 字段为空（不输出速度）
// 同时发 TF: odom → livox_frame
```

| 属性 | 值 |
|------|-----|
| `header.frame_id` | `odom` |
| `child_frame_id` | `livox_frame` |
| `pose.pose` | 位置 + 姿态 |
| `twist` | 空（导航需另外获取速度） |

## 3. 保存 PCD 地图

编辑 `config/mid360.yaml`：

```yaml
pcd_save:
    pcd_save_en: true
    interval: 500      # 每 500 帧存一个 PCD（-1 = 全堆一个文件）
```

`Ctrl+C` 退出时自动保存到 `PCD/scans*.pcd`。

## 4. 录制/重放 rosbag

```sh
rosbag record -a                # 录制
rosbag play xxx.bag --clock      # 重放
```

## 5. 常见问题

### 看不到点云

```sh
rostopic type /livox/lidar
# 必须是 livox_ros_driver2/CustomMsg
```

### 建图漂移

1. 启动后**原地静止 2-3 秒**
2. 检查外参（`extrinsic_T` / `extrinsic_R`）
3. 检查时间同步（`time_sync_en` / `time_offset_lidar_to_imu`）

### 编译报错

| 错误 | 解决 |
|------|------|
| `Could NOT find livox_ros_driver` | 全局替换 `livox_ros_driver` → `livox_ros_driver2` |
| `ikd_Tree.cpp not found` | `cd src/localization/FAST_LIO && git submodule update --init` |
| `livox_ros_driver/CustomMsg.h` not found | 全局替换 `livox_ros_driver::` → `livox_ros_driver2::` |
| `duplicate target ..._generate_messages` | package.xml 加 `<build_depend>livox_ros_driver2</build_depend>` |
