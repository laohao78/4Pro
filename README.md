# 4Pro小车 SLAM算法实战

Jetson Orin NX + Ubuntu 20.04 + ROS1 Noetic，前轮转向 Ackermann 车辆，Livox Mid360 雷达 + RealSense D435i。

## 文档结构

```
FAST_LIO/
├── README.md          ← 你在这里（入口）
├── mainuse.md         ← 所有 launch 命令
├── md/
│   ├── 导航搭建流程.md
│   ├── mid360.md
│   ├── d435i.md
│   ├── 标定-同步-初始化.md
│   ├── TF架构.md
│   ├── SLAM.md
│   ├── 全局与局部规划器.md
│   ├── 怎么得到栅格地图.md
│   └── 导航踩坑记录.md
├── map/
│   └── README.md         ← PGM 地图文件清单
└── src/localization/
    ├── FAST_LIO/mainuse.md
    ├── ndt_localizer/mainuse.md
    ├── ORB_SLAM3/mainuse.md
    └── VINS-Fusion/mainuse.md
```

## 文档导航

### 快速开始

| 文件 | 内容 |
|------|------|
| [mainuse.md](mainuse.md) | 所有 launch 命令（cheat sheet） |

### FAST-LIO / 导航

| 文件 | 内容 |
|------|------|
| [md/导航搭建流程.md](md/导航搭建流程.md) | 从零搭建导航的完整步骤 |
| [src/localization/FAST_LIO/mainuse.md](src/localization/FAST_LIO/mainuse.md) | FAST-LIO 原理、参数、TF 改动、时间同步、标定 |
| [md/mid360.md](md/mid360.md) | Livox MID360 雷达驱动配置 |
| [md/标定-同步-初始化.md](md/标定-同步-初始化.md) | 标定哪些需要/不需要 + 时间同步 + 各方案初始化对比 |
| [md/TF架构.md](md/TF架构.md) | odom→livox_frame→base_link→base_footprint |
| [md/SLAM.md](md/SLAM.md) | SLAM 方案对比表 |
| [md/全局与局部规划器.md](md/全局与局部规划器.md) | TEB / DWA 原理与配置 |
| [md/怎么得到栅格地图.md](md/怎么得到栅格地图.md) | PCD 离线转 PGM |
| [md/d435i.md](md/d435i.md) | RealSense D435i 硬件与视觉 SLAM 调用方式 |
| [md/ssh.md](md/ssh.md) | Jetson 远程连接方式汇总 |
| [md/导航踩坑记录.md](md/导航踩坑记录.md) | 导航调试中遇到的问题与解决 |
| [map/README.md](map/README.md) | PGM 栅格地图文件清单（v3/sand_table 等） |

### LiDAR 定位

| 文件 | 内容 |
|------|------|
| [src/localization/ndt_localizer/mainuse.md](src/localization/ndt_localizer/mainuse.md) | NDT 点云定位，自动初始化，精度远超 AMCL |

### 视觉 SLAM

| 文件 | 内容 |
|------|------|
| [src/localization/ORB_SLAM3/mainuse.md](src/localization/ORB_SLAM3/mainuse.md) | 编译、YAML 配置、地图保存/加载、已修复 bug |
| [src/localization/VINS-Fusion/mainuse.md](src/localization/VINS-Fusion/mainuse.md) | OpenCV 兼容、IMU 标定、回环、外参读取 |

## 硬件

| 组件 | 型号 |
|------|------|
| 计算平台 | Jetson Orin NX |
| 雷达 | Livox Mid360 |
| 相机 | Intel RealSense D435i |
| 底盘 | 前轮转向 Ackermann |

## 核心依赖

```sh
sudo apt install ros-noetic-move-base ros-noetic-map-server ros-noetic-global-planner \
  ros-noetic-teb-local-planner ros-noetic-pointcloud-to-laserscan \
  ros-noetic-pcl-ros ros-noetic-costmap-2d ros-noetic-slam-toolbox ros-noetic-amcl
```

导航从零搭建的完整流程见 [md/导航搭建流程.md](md/导航搭建流程.md)。

## TF 架构

```
map ──(slam/定位)──▶ odom ──(FAST_LIO)──▶ livox_frame
                                               │  (+0.13, 0, -0.15)
                                               ▼
                                          base_link
                                               │  (0, 0, -0.03)
                                               ▼
                                          base_footprint
```

静态 TF 已在各 launch 中通过 `static_transform_publisher` 定义。FAST_LIO 源码已改为直接输出 `odom → livox_frame`。

## 定位 & SLAM 方案

| 方案 | 类型 | 定位 | 状态 |
|------|------|:--:|:----:|
| **FAST-LIO** | LiDAR+IMU 紧耦合 | — | ✅ 主力里程计 |
| **NDT** | 点云匹配静态 PCD | ✅ 自动初始化 | ✅ 已集成导航 |
| **slam_toolbox** | 激光 Karto SLAM | ✅ posegraph | ✅ 可存可载 |
| **ICP** | 点面多假设 ICP | 需手动 2D Pose | ✅ 已集成导航 |
| **AMCL** | 粒子滤波 PGM | 需手动 2D Pose | ✅ 可用 |
| **ORB-SLAM3** | 视觉+IMU，ORB 特征 | ✅ Localization | ✅ 已跑通 |
| **VINS-Fusion** | 视觉+IMU 紧耦合 + 回环 | ✅ 回环 | ✅ 标定+跑通 |

### 待完成

| 方案 | 说明 |
|------|------|
| **Point_LIO** | 逐点卡尔曼，100Hz，高速机动用 |
| **FAST-LIVO2** | LiDAR+Camera+IMU 紧耦合，需外参标定 |

### 已评估未集成

| 方案 | 说明 |
|------|------|
| **FAST_LIO_LOCALIZATION**（4pro） | LIO + ICP 一体化，Python Open3D，不如 NDT/ICP 已覆盖 |
