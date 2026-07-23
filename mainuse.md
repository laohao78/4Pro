# 可运行例程

```sh
cd /home/orin/Desktop/00/FAST_LIO
source devel/setup.bash
```

---

## FAST-LIO

LiDAR+IMU 紧耦合 SLAM，基于 Livox MID360 雷达 + FAST-LIO 里程计 + TF。

### 纯建图

```sh
roslaunch nav_bringup fastlio_mapping.launch rviz:=true
```

### 边建图边导航

```sh
roslaunch nav_bringup fastlio_slamtoolbox_mapping_nav.launch rviz:=true
```

### 已知地图导航 (slam_toolbox)

```sh
roslaunch nav_bringup fastlio_slamtoolbox_nav.launch rviz:=true map_name:=my_map
```

### 已知地图导航 (AMCL)

```sh
roslaunch nav_bringup fastlio_amcl_nav.launch rviz:=true
```

### 底盘控制测试

```sh
roslaunch nav_bringup test_control.launch
```

---

## ORB-SLAM3

视觉/视觉惯性 SLAM，ORB 特征 + 全局 BA + 回环。

详见：[src/localization/ORB_SLAM3/mainuse.md](src/localization/ORB_SLAM3/mainuse.md)

```sh
# Stereo-Inertial 模式 (D435i)
cd src/localization/ORB_SLAM3
./Examples/Stereo-Inertial/stereo_inertial_realsense_D435i \
  Vocabulary/ORBvoc.txt \
  Examples/Stereo-Inertial/RealSense_D435i.yaml
```

---

## VINS-Fusion

视觉+IMU 紧耦合里程计 + BRIEF 回环检测 (D435i)。

详见：[src/localization/VINS-Fusion/mainuse.md](src/localization/VINS-Fusion/mainuse.md)

```sh
roslaunch vins vins_realsense_stereo_imu.launch rviz:=true
```

> **注意**：IMU 噪声参数必须标定，详见 VINS-Fusion 踩坑记录。
