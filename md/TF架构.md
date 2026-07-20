# TF 架构

## 当前结构

```
odom ──(FAST_LIO)──▶ livox_frame (传感器, z=0=雷达)
                         │  (+0.13, 0, -0.15)
                         ▼
                    base_link (底盘中心, z=-0.15)
                         │  (0, 0, -0.03)
                         ▼
                    base_footprint (地面, z=-0.18)
```

各帧职责：

| 帧 | 用途 | 谁用 |
|----|------|------|
| `odom` | 世界原点（第一帧 LiDAR 位姿） | FAST_LIO |
| `livox_frame` | 传感器位置，/scan 的 frame_id | costmap 障碍物层 |
| `base_link` | 底盘中心，路径规划的旋转中心 | move_base 全局路径 |
| `base_footprint` | 底盘中心 XY + 地面 Z，costmap/AMCL 的参考点 | costmap 膨胀层, AMCL |

## 为什么 base_link 不能省

`robot_base_frame` 是 move_base 跟踪的"车体参考点"。如果这个点在 livox_frame（传感器 XY）而非 base_footprint（底盘中心 XY）：

- **转弯偏了**：move_base 把传感器 XY 当作旋转中心，车绕传感器转弯 vs 绕底盘中心转弯，轨迹不同
- **撞了不知道**：footprint 多边形中心贴在传感器 XY 处而非车体 XY 中心，碰撞检测差了一个 LiDAR→底盘的偏移量
- **AMCL 跟错了**：粒子跟踪的是 `robot_base_frame` 在 odom 下的运动。传感器 XY 和底盘中心 XY 的里程不同步，用传感器位置让粒子收敛偏了

核心问题都是 **XY 中心不一致**，跟 Z 高度无关。

## 帧名对照

| 原 FAST_LIO | 现在 | 说明 |
|-------------|------|------|
| `camera_init` | `odom` | 世界原点 |
| `body` | `livox_frame` | IMU/LiDAR 一体 |

## FAST_LIO 源码改动

`laserMapping.cpp`：

```cpp
odomAftMapped.header.frame_id = "odom";
odomAftMapped.child_frame_id  = "livox_frame";
```

## 实测偏移

| 变换 | x | y | z |
|------|---|---|---|
| `livox_frame → base_link` | +0.13 | 0 | -0.15 |
| `base_link → base_footprint` | 0 | 0 | -0.03 |

## 历史弯路

| 版本 | TF 链 | 问题 |
|------|-------|------|
| v1 | `camera_init → body` (原版) | 非标准命名 |
| v2 | `odom → base_link` + tf_relay | relay 节点名冲突 |
| v3 | `odom → base_link → livox_frame` | base_link 实际是 IMU，z 错 |
| v4 | `odom → livox_frame` | 缺底盘帧，路径规划歪 |
| **v5** | `odom → livox_frame → base_link → base_footprint` | 当前，正确 |
