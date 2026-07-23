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
│   ├── fast-lio.md
│   ├── TF架构.md
│   ├── SLAM.md
│   ├── 全局与局部规划器.md
│   ├── 怎么得到栅格地图.md
│   └── 导航踩坑记录.md
└── src/localization/
    ├── ORB_SLAM3/mainuse.md
    └── VINS-Fusion/mainuse.md
```

## 文档导航

### 快速开始

| 文件 | 内容 |
|------|------|
| [mainuse.md](mainuse.md) | 所有 launch 命令快速参考 |
| [md/导航搭建流程.md](md/导航搭建流程.md) | 从零搭建导航的完整步骤 |

### FAST-LIO / 导航

| 文件 | 内容 |
|------|------|
| [md/mid360.md](md/mid360.md) | Livox MID360 雷达驱动配置 |
| [md/fast-lio.md](md/fast-lio.md) | FAST-LIO 原理、参数、TF 改动 |
| [md/TF架构.md](md/TF架构.md) | odom→livox_frame→base_link→base_footprint |
| [md/SLAM.md](md/SLAM.md) | SLAM 方案对比表 |
| [md/全局与局部规划器.md](md/全局与局部规划器.md) | TEB / DWA 原理与配置 |
| [md/怎么得到栅格地图.md](md/怎么得到栅格地图.md) | PCD 离线转 PGM |
| [md/d435i.md](md/d435i.md) | RealSense D435i 硬件与视觉 SLAM 调用方式 |
| [md/导航踩坑记录.md](md/导航踩坑记录.md) | 导航调试中遇到的问题与解决 |

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

## SLAM 方案

| 方案 | 类型 | 状态 |
|------|------|:----:|
| **FAST-LIO** | LiDAR+IMU 紧耦合 | ✅ 主力 |
| **ORB-SLAM3** | 视觉+IMU，ORB 特征 | ✅ 已跑通 |
| **VINS-Fusion** | 视觉+IMU 紧耦合 + 回环 | ✅ 标定+跑通 |
