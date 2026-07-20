# SLAM

## 总览

| 方式 | 里程计 | 建图 | map→odom | 预置地图 | 状态 | 锐评 |
|------|:---:|:---:|:---:|:---:|------|------|
| FAST_LIO | ✅ ~10Hz | ✅ PCD | — | — | 当前在用 | 频率瓶颈，优先升级 |
| **FAST_LIO2** | ✅ ~50Hz | ✅ PCD | — | — | **P0：未集成** | 低迁移成本，高收益 |
| Point_LIO | ✅ 100+Hz | ✅ PCD | — | — | 未集成 | 高速场景备选 |
| ICP | — | — | ✅ | PCD | 有 scans.pcd | 无协方差，建议换 NDT |
| **NDT** | — | — | ✅ | PCD | **P1：未集成** | 精度更高，出协方差 |
| AMCL | — | — | ✅ | PGM | 有 sand_table.pgm | 2D 降级方案 |
| slam_toolbox localization | — | — | ✅ | .posegraph + .pgm | 需先 mapping | 依赖链太长 |
| **slam_toolbox mapping** | — | ✅ PGM | ✅ | 无 | 当前在用 | 3D 雷达做 2D 建图浪费 |
| ORB-SLAM3 | ✅ 视觉 | ✅ KeyFrame+MapPoint | ✅ Localization | 稀疏地图 | 沙盘不可用 | 视觉线放弃 |
| VINS-Mono | ✅ 视觉 | — | — | — | 未集成 | 纯里程计，无定位 |

- slam_toolbox 不产生里程计，它依赖外部里程计（如 FAST_LIO）提供 odom→base，再用 /scan 修正 map→odom
- ORB_SLAM3 稀疏地图 = 几百个 KeyFrame（图像+位姿）+ 几千个 MapPoint（3D 点 + ORB 描述子），大小几十 MB

## 优先级

| 优先级 | 事项 | 理由 |
|------|------|------|
| **P0** | FAST_LIO2 | 同源码改帧名+D435i YAML，LIO 频率 10→50Hz |
| **P1** | NDT 定位 | 现有 PCD 直接可用，出协方差，比 ICP 更稳 |
| P2 | Point_LIO | 高速机动时用，日常不必要 |

## FAST_LIO 系列对比

同一个实验室（HKU Mars Lab），Wei Xu 等。

| | FAST_LIO | FAST_LIO2 | Point_LIO |
|------|------|------|------|
| 年份 | 2020 | 2022 | 2022 |
| 输入 | LiDAR + IMU | LiDAR + IMU | LiDAR + IMU |
| 原理 | IEKF + 特征 | 直接法 + IEKF | 逐点卡尔曼 |
| 数据结构 | ikd-Tree | ikd-Tree (升级) | ikd-Tree |
| 频率 | ~10 Hz | ~50 Hz | 100+ Hz |
| CPU | 低 | 中 | 高 |
| 多雷达 | 不支持 | 支持 | 不支持 |
| 适用 | 通用 | 通用/低延迟 | 高速高动态 |

FAST_LIO 按帧处理，FAST_LIO2 跳过特征提取直接点迭代，更快还更准。Jetson 上 FAST_LIO2 是 FPS/CPU 的甜点。

## 视觉 SLAM

| | ORB-SLAM3 | VINS-Mono |
|------|------|------|
| 年份 | 2021 | 2017 |
| 实验室 | UZ (Zaragoza) | HKUST (Shen) |
| 传感器 | Mono/Stereo/RGB-D + IMU | Mono + IMU |
| 特征 | ORB (描述子匹配) | KLT 光流 |
| 建图密度 | 稀疏 KeyFrame+MapPoint | 稀疏 landmark |
| 回环检测 | ✅ | ✅ |
| 重定位 | ✅ (Localization Mode) | ❌ |
| 多地图 | ✅ (Atlas) | ❌ |
| 初始化条件 | 需加速+平移视差 | 需加速+平移视差 |
| 沙盘效果 | ❌ IMU 反复 reset | 未测 |

视觉 SLAM vs LiDAR SLAM：

| | 视觉 (VIO) | LiDAR (LIO) |
|------|------|------|
| 特征来源 | 图像纹理 | 3D 几何结构 |
| 弱纹理/暗光 | 跟丢 | 不受影响 |
| 纯色地面 | 无特征 → 退化 | 地面平面 → 有用 |
| 低速运动 | IMU 初始化困难 | 正常工作 |
| 计算量 | 轻 | 中等 |
| 沙盘适用 | ❌ | ✅ |

沙盘窄+低速+弱纹理，视觉 SLAM 不可用。FAST_LIO 是正确选择。
