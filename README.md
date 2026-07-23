# 1.Livox-MID360 环境配置

# 2.RealSense_d435i 环境配置

# 3.FAST-LIO 环境配置

# 4.导航依赖

- **move-base** — 核心导航框架
- **map-server** — 加载/保存 2D 栅格地图 (.pgm + .yaml)
- **global-planner** — A*/Dijkstra 全局路径规划
- **teb-local-planner** — TEB 局部轨迹优化
- **pointcloud-to-laserscan** — Mid360 PointCloud2 转 2D /scan
- **pcl-ros** — PCL 点云库 ROS 桥接
- **costmap-2d** — 2D 代价地图
- **slam-toolbox** — 在线栅格建图

```sh
sudo apt install ros-noetic-move-base ros-noetic-map-server ros-noetic-global-planner \
  ros-noetic-teb-local-planner ros-noetic-pointcloud-to-laserscan \
  ros-noetic-pcl-ros ros-noetic-costmap-2d ros-noetic-slam-toolbox ros-noetic-amcl
```

# 5.TF 树搭建

## 实车测量

雷达偏移 (base_link → livox_frame)：(-13cm, 0, 15cm)，无旋转
底盘投影 (base_link → base_footprint)：(0, 0, -3cm)，无旋转

## TF 架构

FAST_LIO 源码已改（`camera_init` → `odom`, `body` → `base_link`），直接输出标准 TF。

```
map ──(slam/定位)──▶ odom ──(FAST_LIO)──▶ base_link
                                            ├── livox_frame      x=-0.13 y=0 z=0.15
                                            └── base_footprint   x=0 y=0 z=-0.03
```

`src/nav_bringup/` — 导航启动包。TF 放在各 launch 里（`tf_base_to_livox` + `tf_base_to_footprint`）。

# 6.栅格地图生成

PCD 离线转栅格，见 [怎么得到栅格地图](md/怎么得到栅格地图.md)。最佳参数 `z=-0.08 ~ 0.08`（雷达系，z=0 = 雷达高度 ≈ 18cm 离地）。

# 7.定位

边建图边导航模式：slam_toolbox 同时出 /map + map→odom TF，不需要单独的 AMCL。
静态地图模式：map_server + AMCL（TODO）。

# 8.move_base + TEB

TEB 差速模式（`cmd_angle_instead_rotvel: false`），`max_samples: 100` 适配 Jetson。
配置：[teb_local_planner.yaml](src/nav_bringup/config/teb_local_planner.yaml)
SLAM 模式 costmap 用 `global_frame: odom`（避免启动时 map 帧未就绪）。

# 9.cmd_vel → 底盘控制

`cmd_vel_to_ackermann.py`：速度线性映射为占空比，ω 映射为舵机 position。四轮异向模式。
- `/motor_write_duty` (Float64)
- `/servo_write_position` (Int32, 1500=中位)

# 10.launch 文件

| Launch | 用途 |
|--------|------|
| `fastlio_mapping.launch` | 纯建图（雷达 + FAST_LIO + TF） |
| `fastlio_slamtoolbox_nav.launch` | slam_toolbox 已知地图导航 |
| `fastlio_slamtoolbox_mapping_nav.launch` | **边建图边导航**（全链路） |
| `fastlio_amcl_nav.launch` | 静态地图导航（AMCL + map_server） |
| `test_control.launch` | 底盘控制链测试 |
| `fastlio_ndt_nav.launch` | NDT 定位导航 (TODO) |
