## 可以运行的例程

```sh
cd /home/orin/Desktop/00/FAST_LIO
source devel/setup.bash
```

### 纯建图

```sh
roslaunch nav_bringup fastlio_mapping.launch
```

### 边建图边导航

```sh
roslaunch nav_bringup fastlio_slamtoolbox_mapping_nav.launch rviz:=true
```

### slam_toolbox 已知地图导航

```sh
roslaunch nav_bringup fastlio_slamtoolbox_nav.launch rviz:=true map_name:=my_map
```

### AMCL 静态地图导航

```sh
roslaunch nav_bringup fastlio_amcl_nav.launch rviz:=true
```

### 底盘控制测试

```sh
roslaunch nav_bringup test_control.launch
```

### ORB-SLAM3

见 `src/localization/ORB_SLAM3/mainuse.md`
