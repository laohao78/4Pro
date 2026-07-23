# SLAM

## 总览

| 方式 | 里程计 | 建图 | map→odom | 预置地图 | 状态 | 锐评 |
|------|:---:|:---:|:---:|:---:|------|------|
| **里程计/建图** | | | | | | |
| **FAST_LIO** | ✅ ~50Hz | ✅ PCD | — | — | 当前在用 | 实跑 10Hz（Mid360 帧率瓶颈） |
| Point_LIO | ✅ ~100Hz | ✅ PCD | — | — | 未集成 | 逐点更新，输入同受 LiDAR 帧率限制 |
| **定位 (基于 LiDAR)** | | | | | | |
| **FAST_LIO_LOCALIZATION** | ✅ 内置 LIO | ✅ PCD | ✅ ICP | PCD | **4pro 已有** | LIO + ICP 一体化 |
| ICP | — | — | ✅ | PCD | 有 scans.pcd | 无协方差，换 NDT |
| **NDT** | — | — | ✅ | PCD | **P1：未集成** | 精度高，出协方差 |
| AMCL | — | — | ✅ | PGM | 有 sand_table.pgm | 2D 降级 |
| **slam_toolbox mapping** | — | ✅ PGM | ✅ | 无 | 当前在用 | 边建图边定 |
| slam_toolbox localization | — | — | ✅ | .posegraph+.pgm | 需先 mapping | 依赖长 |
| **视觉** | | | | | | |
| ORB-SLAM3 | ✅ 视觉+IMU | ✅ KeyFrame+MapPoint (.osa) | ✅ Localization | 稀疏地图 | ✅ 已跑通 | 地图保存/加载正常，Stereo+IMU 可用 |
| VINS-Mono | ✅ 视觉 | ✅ 位姿图+稀疏点 | — | — | 未集成 | 纯里程计 |
| VINS-Fusion | ✅ 视觉+IMU | ✅ 位姿图+稀疏点 | ✅ 回环+位姿图 | 位姿图 | ✅ 已集成 | Stereo+IMU，IMU 已标定，外参固件读取，有 launch |

- slam_toolbox 不产生里程计，它依赖外部里程计（如 FAST_LIO）提供 odom→base，再用 /scan 修正 map→odom
- ORB_SLAM3 稀疏地图 = 几百个 KeyFrame（图像+位姿）+ 几千个 MapPoint（3D 点 + ORB 描述子），大小几十 MB
- ICP/NDT 包都已就绪：`FAST_LIO_LOCALIZATION`（4pro）+ `ndt_localizer`（00/FAST_LIO），NDT 优先

### ICP vs NDT

| | ICP | NDT |
|------|------|------|
| 原理 | 点到点/点到面距离最小化 | 体素高斯分布相似度最大化 |
| 对初值 | 敏感，需好初值 | 不敏感，收敛域更宽 |
| 精度 | 点到面很准 | 通常略优 |
| 协方差 | ❌ | ✅ (Hessian 逆) |
| 速度 | 快 | 稍慢（建网格开销） |
| 适用 | 结构清晰场景 | 噪声/遮挡场景 |
| 你的包 | `FAST_LIO_LOCALIZATION` (4pro) | `ndt_localizer` (00/FAST_LIO) |

NDT 优先：把地图切成体素算高斯分布，当前点云匹配概率最高处，比 ICP 抓最近点更鲁棒，且协方差直接可用。

## 优先级

| 优先级 | 事项 | 理由 |
|------|------|------|
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
| 沙盘效果 | ❌ 低速弱纹理 | 未测 |

视觉 SLAM vs LiDAR SLAM：

| | 视觉 (VIO) | LiDAR (LIO) |
|------|------|------|
| 特征来源 | 图像纹理 | 3D 几何结构 |
| 弱纹理/暗光 | 跟丢 | 不受影响 |
| 纯色地面 | 无特征 → 退化 | 地面平面 → 有用 |
| 低速运动 | IMU 初始化困难 | 正常工作 |
| 计算量 | 轻 | 中等 |
| 沙盘适用 | ❌ | ✅ |

沙盘窄+低速+弱纹理，视觉 SLAM 效果差但大场景可用。FAST_LIO 是沙盘首选，ORB_SLAM3 保留给走廊/室外。
