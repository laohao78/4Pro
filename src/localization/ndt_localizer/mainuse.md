# NDT Localizer — 点云定位

## 原理

预建 PCD 地图 → NDT 体素网格 → 当前帧点云匹配 → 输出 map→base_link 位姿。

比 ICP 鲁棒：用体素高斯分布做匹配，不依赖最近邻点，对噪声和遮挡容忍度高，自带协方差。

## 数据流

```
/cloud_registered_body ──▶ voxel_grid_filter(0.5m) ──▶ /filtered_points
                                                                  │
/points_map (预载 PCD)                                           │
         │                                                        │
         ▼                                                        ▼
    ndt_localizer_node ──▶ /ndt_pose (map→base_link)
                         ──▶ /ndt_pose_with_covariance
```

## 运行

### 一键启动（推荐）

```sh
roslaunch nav_bringup fastlio_ndt_nav.launch
```

自动启动雷达 + FAST_LIO + TF + NDT。

### 分步启动（调试用）

```sh
# 终端 1: 雷达
roslaunch livox_ros_driver2 msg_MID360.launch

# 终端 2: FAST_LIO
roslaunch fast_lio mapping_mid360.launch rviz:=false

# 终端 3: NDT
roslaunch ndt_localizer ndt_localizer.launch
```

### 初始化

NDT 默认从 (0,0,0) 牛顿搜索，通常能自动收敛。离原点远或在对称环境中，可以手动给 **2D Pose Estimate** 缩小搜索范围，匹配更快更稳。

终端看到 `align_time: xx ms` + `trans_prob: 4.x` 就说明匹配成功。没反应说明 `/cloud_registered_body` 没到 — 检查 FAST_LIO 是否已输出点云（`rostopic hz /cloud_registered_body`）。

## 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `resolution` | 1.5 | NDT 体素分辨率 (m)，越小精度越高但计算量越大 |
| `max_iterations` | 45 | 牛顿法最大迭代次数 |
| `trans_epsilon` | 0.00001 | 收敛判断：连续两次变换差小于此值即停止 |
| `step_size` | 0.1 | 牛顿线搜索最大步长 |
| `leaf_size` | 0.5 | VoxelGrid 降采样叶子尺寸 (m) |

## 接口

| Topic | 类型 | 方向 | 说明 |
|-------|------|:--:|------|
| `/ndt_pose` | `geometry_msgs/PoseStamped` | 输出 | 定位位姿 |
| `/ndt_pose_with_covariance` | `geometry_msgs/PoseWithCovarianceStamped` | 输出 | 带 6×6 协方差的位姿 |
| `/filtered_points` | `sensor_msgs/PointCloud2` | 输入 | 降采样后的当前帧点云 |
| `/points_map` | `sensor_msgs/PointCloud2` | 输入 | 预载的 PCD 地图 |
| `/ekf_pose_with_covariance` | `geometry_msgs/PoseWithCovarianceStamped` | 输入 | 初始位姿猜测 |

## 与 FAST_LIO 的对比

| | FAST_LIO | NDT Localizer |
|------|-----------|----------------|
| 输入 | LiDAR 原始帧 + IMU | 点云 + 静态 PCD |
| 输出 | odom→livox_frame（里程计） | map→base_link（绝对定位） |
| 漂移 | 累计漂移 | 不漂（匹配固定地图） |
| 需要地图 | 否 | 是（预建 PCD） |
| 速度 | 10Hz | 依赖 PCD 大小和分辨率 |
| 用途 | 里程计 / 建图 | 修正漂移 / 全局定位 |
