# nav_bringup — 导航启动包

## 文件结构

```
nav_bringup/
├── README.md
├── CMakeLists.txt
├── package.xml
├── config/
│   ├── amcl_params.yaml              # AMCL 定位参数
│   ├── costmap_common.yaml           # 代价地图公共配置
│   ├── costmap_slam.yaml             # SLAM 模式代价地图
│   ├── global_costmap.yaml           # 全局代价地图
│   ├── local_costmap.yaml            # 局部代价地图
│   ├── move_base.yaml                # move_base 框架参数
│   ├── slam_toolbox_mapping.yaml     # slam_toolbox 建图参数
│   └── teb_local_planner.yaml        # TEB 轻量配置 (Jetson)
├── launch/
│   ├── fastlio_mapping.launch        # 纯建图: 雷达 + FAST_LIO + TF
│   ├── fastlio_slamtoolbox_mapping.launch   # 建图: + slam_toolbox
│   ├── fastlio_slamtoolbox_mapping_nav.launch       # 边建图边导航 (全链路)
│   ├── fastlio_amcl_nav.launch            # 静态地图导航 (map_server + AMCL)
│   └── test_control.launch           # 底盘控制链测试
├── rviz/
│   └── nav.rviz                      # 导航 RViz 配置
└── scripts/
    ├── cmd_vel_to_ackermann.py       # Twist → 速度(占空比) + 舵机位置
    ├── pcd2pgm_node.py               # PCD 离线转栅格
    └── test_control_chain.py         # 控制链测试
```

## Launch 文件

| 文件 | 用途 | 包含 |
|------|------|------|
| `fastlio_mapping.launch` | 纯建图 | 雷达 + FAST_LIO + TF |
| `fastlio_slamtoolbox_mapping.launch` | 建栅格 | + pointcloud_to_laserscan + slam_toolbox |
| `fastlio_slamtoolbox_mapping_nav.launch` | **边建图边导航** | 上面 + TEB + move_base + 底盘控制 |
| `fastlio_amcl_nav.launch` | 静态地图导航 | + map_server + AMCL |
| `test_control.launch` | 底盘测试 | chassis_control + converter + test_control |

## TF 架构

FAST_LIO 源码已改为直接发 `odom → livox_frame`。

```
map ──(slam_toolbox)──▶ odom ──(FAST_LIO)──▶ livox_frame
                                                 │  (+0.13, 0, -0.15)
                                                 ▼
                                            base_link
                                                 │  (0, 0, -0.03)
                                                 ▼
                                            base_footprint
```

## cmd_vel → 底盘控制

`cmd_vel_to_ackermann.py`：速度线性映射为占空比，ω 映射为舵机 position。支持 `rosparam set` 动态调参。

```sh
rosparam set /cmd_vel_converter/steer_gain 400
rosparam set /cmd_vel_converter/min_duty 0.07
```

## pcd2pgm_node.py

基于 [LihanChen2004/pcd2pgm](https://github.com/LihanChen2004/pcd2pgm)。

```sh
pcl_convert_pcd_ascii_binary input.pcd /tmp/uncompressed.pcd 0
python3 pcd2pgm_node.py /tmp/uncompressed.pcd output_prefix z_min z_max
```
