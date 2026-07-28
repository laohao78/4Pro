# SLAM

## 总览

| 方式 | 里程计 | 建图 | map→odom | 预置地图 | 状态 | 锐评 |
|------|:---:|:---:|:---:|:---:|------|------|
| **里程计/建图** | | | | | | |
| **FAST_LIO** | ✅ ~50Hz | ✅ PCD | — | — | 当前在用 | 实跑 10Hz（Mid360 帧率瓶颈） |
| Point_LIO | ✅ ~100Hz | ✅ PCD | — | — | 未集成 | 逐点更新，输入同受 LiDAR 帧率限制 |
| **定位 (基于 LiDAR)** | | | | | | |
| **FAST_LIO_LOCALIZATION** | ✅ 内置 LIO | ✅ PCD | ✅ ICP | PCD | **4pro 已有** | LIO + ICP 一体化 |
| **ICP (icp_localizer)** | — | — | ✅ | PCD | ✅ 已集成+导航 | 多假设+点面ICP（pb_rm ROS2移植） |
| **NDT** | — | — | ✅ | PCD | ✅ 已集成+导航 | 自动初始化，精度远超 AMCL |
| AMCL | — | — | ✅ | PGM | 有 sand_table.pgm | 2D 降级 |
| **slam_toolbox mapping** | — | ✅ PGM | ✅ | 无 | 当前在用 | 边建图边定 |
| slam_toolbox localization | — | — | ✅ | .posegraph+.pgm | ✅ 已跑通 | 需先 mapping 存 posegraph |
| **视觉** | | | | | | |
| ORB-SLAM3 | ✅ 视觉+IMU | ✅ KeyFrame+MapPoint (.osa) | ✅ Localization | 稀疏地图 | ✅ 已跑通 | 地图保存/加载正常，Stereo+IMU 可用 |
| VINS-Fusion | ✅ 视觉+IMU | ✅ 位姿图+稀疏点 | ✅ 回环+位姿图 | 位姿图 | ✅ 已集成 | Stereo+IMU，IMU 已标定，外参固件读取 |
| **视觉-LiDAR 融合** | | | | | | |
| **FAST-LIVO2** | ✅ LiDAR+视觉+IMU | ✅ PCD+视觉纹理 | — | — | ✅ 标定+跑通 | 3 场景联合 RMSE 6.7mm，软同步 |

- slam_toolbox 不产生里程计，它依赖外部里程计（如 FAST_LIO）提供 odom→base，再用 /scan 修正 map→odom
- ORB_SLAM3 稀疏地图 = 几百个 KeyFrame（图像+位姿）+ 几千个 MapPoint（3D 点 + ORB 描述子），大小几十 MB
- 三个 PCD 定位包都已就绪：`icp_localizer` + `ndt_localizer` + `FAST_LIO_LOCALIZATION`（4pro），NDT 优先

### ICP vs NDT

| | ICP | NDT |
|------|------|------|
| 原理 | 点到点/点到面距离最小化 | 体素高斯分布相似度最大化 |
| 对初值 | 敏感，需好初值 | 不敏感，收敛域更宽 |
| 精度 | 点到面很准 | 通常略优 |
| 协方差 | ❌ | ✅ (Hessian 逆) |
| 速度 | 快 | 稍慢（建网格开销） |
| 适用 | 结构清晰场景 | 噪声/遮挡场景 |
| 你的包 | `icp_localizer` (00/FAST_LIO) | `ndt_localizer` (00/FAST_LIO) |

NDT 优先：自动初始化 + 更快更鲁棒。ICP 备选。

### 两个 ICP 方案对比

| | icp_localizer（已集成） | FAST_LIO_LOCALIZATION（4pro，不集成） |
|------|------|------|
| 语言 | C++ (PCL) | Python (Open3D) |
| ICP 类型 | **点面** + 法向量 | 简单点对点 |
| 多假设搜索 | ✅ 网格 9×N | ❌ |
| 两级精炼 | ✅ rough+refine | ❌ |
| 初值 | 网格自动搜 | 必需给准 |
| 速度 | 快 | 慢 |
| 来源 | pb_rm ROS2 移植 | 4pro 原始方案 |

4pro 版用 Python Open3D 跑简单点对点 ICP，没有多假设也没有两级精炼，初值差一点就跑飞。我们已用 C++ PCL 重写，完全覆盖。

## 优先级

| 优先级 | 事项 | 理由 |
|------|------|------|
| ~~P1~~ ✅ | NDT 定位 | 已完成，全链路跑通，自动初始化，精度远超 AMCL |
| ~~P1~~ ✅ | FAST-LIVO2 | 标定+跑通，LiDAR-视觉-IMU 紧耦合 |
| P2 | Point_LIO | 高速机动时用，日常不必要 |

## FAST_LIO 系列对比

| | FAST_LIO | FAST_LIO2 | Point_LIO | **FAST-LIVO2** |
|------|------|------|------|------|
| 年份 | 2020 | 2022 | 2022 | **2024** |
| 输入 | LiDAR + IMU | LiDAR + IMU | LiDAR + IMU | **LiDAR + 视觉 + IMU** |
| 原理 | IEKF + 特征 | 直接法 + IEKF | 逐点卡尔曼 | **直接法 LIO + 稀疏直接法 VIO** |
| 数据结构 | ikd-Tree | ikd-Tree (升级) | ikd-Tree | **iVox + 视觉子图** |
| 频率 | ~10 Hz | ~50 Hz | 100+ Hz | ~10Hz (LiDAR帧率) |
| CPU | 低 | 中 | 高 | 中-高 |
| 退化场景 | 几何退化 | 几何退化 | 几何退化 | **视觉补充，抗退化** |

## 视觉 SLAM

| | ORB-SLAM3 | VINS-Fusion | **FAST-LIVO2** |
|------|------|------|------|
| 年份 | 2021 | 2017 | **2024** |
| 实验室 | UZ (Zaragoza) | HKUST (Shen) | **HKU Mars** |
| 传感器 | Mono/Stereo/RGB-D + IMU | Mono/Stereo + IMU | **LiDAR + Mono + IMU** |
| 特征 | ORB (描述子匹配) | KLT 光流 | **直接法（光度误差）** |
| 建图密度 | 稀疏 KeyFrame+MapPoint | 稀疏 landmark | **PCD + 视觉纹理** |
| 回环检测 | ✅ | ✅ | ❌ |
| 重定位 | ✅ (Localization Mode) | ❌ | ❌ |
| 多地图 | ✅ (Atlas) | ❌ | ❌ |
| 初始化 | 需加速+平移视差 | 需加速+平移视差 | **静止即可（IMU bias收敛）** |
| 沙盘 | ❌ 低速弱纹理 | 未测 | ⚠️ 视觉纹理依赖 |

视觉 SLAM vs LiDAR SLAM：

| | 视觉 (VIO) | LiDAR (LIO) | **LiDAR-视觉 (LIVO)** |
|------|------|------|------|
| 特征来源 | 图像纹理 | 3D 几何结构 | **两者互补** |
| 弱纹理/暗光 | 跟丢 | 不受影响 | **LiDAR 兜底** |
| 纯色地面 | 无特征 → 退化 | 地面平面 → 有用 | **LiDAR 兜底** |
| 几何退化（长廊/开阔） | 好 | 退化 | **视觉补充** |
| 低速运动 | IMU 初始化困难 | 正常工作 | **静止初始化** |
| 计算量 | 轻 | 中等 | 中-高 |
| 沙盘适用 | ❌ | ✅ | ⚠️ 部分适用 |
