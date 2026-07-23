# VINS-Fusion 踩坑记录

## 1. 编译错误：OpenCV 4.x API 不兼容

D435i + JetPack 5.x 自带 OpenCV 4.x，VINS-Fusion 源码大量使用 OpenCV 3.x 的 C 风格常量。

### 涉及的常量替换

| 旧 (OpenCV 3.x) | 新 (OpenCV 4.x) |
|---|---|
| `CV_GRAY2RGB` | `cv::COLOR_GRAY2RGB` |
| `CV_GRAY2BGR` | `cv::COLOR_GRAY2BGR` |
| `CV_BGR2GRAY` | `cv::COLOR_BGR2GRAY` |
| `CV_RGB2GRAY` | `cv::COLOR_RGB2GRAY` |
| `CV_AA` | `cv::LINE_AA` |
| `CV_CALIB_CB_ADAPTIVE_THRESH` | `cv::CALIB_CB_ADAPTIVE_THRESH` |
| `CV_CALIB_CB_NORMALIZE_IMAGE` | `cv::CALIB_CB_NORMALIZE_IMAGE` |
| `CV_CALIB_CB_FILTER_QUADS` | `cv::CALIB_CB_FILTER_QUADS` |
| `CV_CALIB_CB_FAST_CHECK` | `cv::CALIB_CB_FAST_CHECK` |
| `CV_ADAPTIVE_THRESH_MEAN_C` | `cv::ADAPTIVE_THRESH_MEAN_C` |
| `CV_THRESH_BINARY` | `cv::THRESH_BINARY` |
| `CV_THRESH_BINARY_INV` | `cv::THRESH_BINARY_INV` |
| `CV_SHAPE_CROSS` | `cv::MORPH_CROSS` |
| `CV_SHAPE_RECT` | `cv::MORPH_RECT` |
| `CV_TERMCRIT_EPS` | `cv::TermCriteria::EPS` |
| `CV_TERMCRIT_ITER` | `cv::TermCriteria::MAX_ITER` |
| `CV_RETR_CCOMP` | `cv::RETR_CCOMP` |
| `CV_CHAIN_APPROX_SIMPLE` | `cv::CHAIN_APPROX_SIMPLE` |
| `CV_INTER_LINEAR` | `cv::INTER_LINEAR` |
| `CV_LOAD_IMAGE_UNCHANGED` | `cv::IMREAD_UNCHANGED` |
| `CV_LOAD_IMAGE_GRAYSCALE` | `cv::IMREAD_GRAYSCALE` |
| `CV_FONT_HERSHEY_SIMPLEX` | `cv::FONT_HERSHEY_SIMPLEX` |
| `CV_FONT_HERSHEY_DUPLEX` | `cv::FONT_HERSHEY_DUPLEX` |
| `CV_MAT_DEPTH_MASK` | `cv::Mat::DEPTH_MASK` |

### 涉及文件

- `camera_models/src/calib/CameraCalibration.cc`
- `camera_models/src/chessboard/Chessboard.cc`
- `camera_models/src/intrinsic_calib.cc`
- `loop_fusion/src/ThirdParty/DVision/BRIEF.cpp`
- `loop_fusion/src/keyframe.cpp`
- `loop_fusion/src/pose_graph.cpp`
- `vins_estimator/src/featureTracker/feature_tracker.cpp`
- `FAST-LIVO2/src/vio.cpp`
- `FAST_LIO/include/matplotlibcpp.h`
- `ORB_SLAM3/src/LoopClosing.cc`

修复命令（一键替换所有残留常量）：

```sh
cd ~/Desktop/00/FAST_LIO/src/localization
find . -type f \( -name "*.cc" -o -name "*.cpp" -o -name "*.h" -o -name "*.hpp" \) -exec sed -i \
  -e 's/\bCV_GRAY2RGB\b/cv::COLOR_GRAY2RGB/g' \
  -e 's/\bCV_GRAY2BGR\b/cv::COLOR_GRAY2BGR/g' \
  -e 's/\bCV_BGR2GRAY\b/cv::COLOR_BGR2GRAY/g' \
  -e 's/\bCV_RGB2GRAY\b/cv::COLOR_RGB2GRAY/g' \
  -e 's/\bCV_AA\b/cv::LINE_AA/g' \
  -e 's/\bCV_CALIB_CB_ADAPTIVE_THRESH\b/cv::CALIB_CB_ADAPTIVE_THRESH/g' \
  -e 's/\bCV_CALIB_CB_NORMALIZE_IMAGE\b/cv::CALIB_CB_NORMALIZE_IMAGE/g' \
  -e 's/\bCV_CALIB_CB_FILTER_QUADS\b/cv::CALIB_CB_FILTER_QUADS/g' \
  -e 's/\bCV_CALIB_CB_FAST_CHECK\b/cv::CALIB_CB_FAST_CHECK/g' \
  -e 's/\bCV_ADAPTIVE_THRESH_MEAN_C\b/cv::ADAPTIVE_THRESH_MEAN_C/g' \
  -e 's/\bCV_THRESH_BINARY_INV\b/cv::THRESH_BINARY_INV/g' \
  -e 's/\bCV_THRESH_BINARY\b/cv::THRESH_BINARY/g' \
  -e 's/\bCV_SHAPE_CROSS\b/cv::MORPH_CROSS/g' \
  -e 's/\bCV_SHAPE_RECT\b/cv::MORPH_RECT/g' \
  -e 's/\bCV_TERMCRIT_EPS\b/cv::TermCriteria::EPS/g' \
  -e 's/\bCV_TERMCRIT_ITER\b/cv::TermCriteria::MAX_ITER/g' \
  -e 's/\bCV_RETR_CCOMP\b/cv::RETR_CCOMP/g' \
  -e 's/\bCV_CHAIN_APPROX_SIMPLE\b/cv::CHAIN_APPROX_SIMPLE/g' \
  -e 's/\bCV_INTER_LINEAR\b/cv::INTER_LINEAR/g' \
  -e 's/\bCV_LOAD_IMAGE_UNCHANGED\b/cv::IMREAD_UNCHANGED/g' \
  -e 's/\bCV_LOAD_IMAGE_GRAYSCALE\b/cv::IMREAD_GRAYSCALE/g' \
  -e 's/\bCV_FONT_HERSHEY_DUPLEX\b/cv::FONT_HERSHEY_DUPLEX/g' \
  -e 's/\bCV_FONT_HERSHEY_SIMPLEX\b/cv::FONT_HERSHEY_SIMPLEX/g' \
  -e 's/\bCV_MAT_DEPTH_MASK\b/cv::Mat::DEPTH_MASK/g' \
  {} +
```

---

## 2. 回环检测 match_image 无画面

### 现象

RViz 中 `loop_match_image` 窗口始终空白，但红色回环修正轨迹正常。

### 原因

`save_image: 0` 导致 `DEBUG_IMAGE=0`，match_image 的生成和发布代码被跳过。

### 修复

`config/realsense_d435i/realsense_stereo_imu_config.yaml` 中：

```yaml
# 改前
save_image: 0

# 改后
save_image: 1
```

**注意**：即使 match_image 没有画面，回环检测本身可能仍在工作（红色轨迹修正可验证）。

---

## 3. 绿色轨迹不闭合（IMU 参数不准）

### 现象

走一圈回到起点，VINS 的绿色 odometry 轨迹不重合，有明显漂移。

### 原因

VINS-Fusion 是视觉+IMU **紧耦合**，IMU 噪声参数决定了优化中 IMU 项的权重。默认参数是 D435i 的粗略值，不准确。

ORB-SLAM3 对同样数据跑得好是因为它以视觉为主（ORB 特征），IMU 仅辅助，对噪声参数不敏感。

### 修复

```sh
# 1. 录制 10 分钟静止 IMU 数据
rosbag record /camera/imu -O imu_static.bag --duration=600

# 2. 用脚本估算噪声参数
python3 dependent/imu_noise_calib.py dependent/imu_static.bag
```

### 实测标定结果

采集 600 秒 / 105951 条 / 176.6 Hz 静止 IMU 数据，脚本路径：`dependent/imu_noise_calib.py`

| 参数 | 默认值 | 实测值 | 变化 |
|---|---|---|---|
| `acc_n` | 0.2 | **0.0080** | ↓ 25x |
| `gyr_n` | 0.05 | **0.0019** | ↓ 26x |
| `acc_w` | 0.002 | **0.00214** | ≈ |
| `gyr_w` | 4.0e-5 | **1.51e-4** | ↑ 3.7x |
| `g_norm` | 9.805 | **9.345** | 实测 |

**效果**：写入标定值后轨迹闭合效果显著改善 ✅。

默认 `acc_n: 0.2` / `gyr_n: 0.05` 比真实噪声大了 ~25 倍，导致优化器不信任 IMU 测量，视觉惯性紧耦合退化为近似纯视觉。参数准确后 IMU 预积分权重正常，里程计精度大幅提升。

---

## 4. rosnode info 偶尔显示空订阅

### 现象

刚启动时 `rosnode info /loop_fusion | grep -i sub` 显示 `Subscriptions: ` 为空。

### 原因

节点初始化需要时间（加载 BRIEF 词汇文件 60MB），订阅在 `process()` 线程启动前尚未注册。

### 处理

等几秒后再查即可，实际不影响运行。

---

## 5. D435i IMU 重力方向

D435i 的 `camera_imu_optical_frame` 坐标系下，重力在 **Y 轴**（约 -9.34~-9.81 m/s²），而非常见的 Z 轴。配置中 `g_norm` 需要和实际读到的重力幅值一致。

---

## 6. 运行

```sh
cd /home/orin/Desktop/00/FAST_LIO && source devel/setup.bash

# 一键启动（相机 + VINS + 回环 + RViz）
roslaunch vins vins_realsense_stereo_imu.launch rviz:=true

# RViz 中查看追踪效果：Add → By topic → /vins_estimator/image_track

# 纯 RViz（已运行 VINS 后）
roslaunch vins vins_rviz.launch
```

### 初始化要求

VINS 需要**运动**才能初始化，静止不动会 crash（numerical unstable → Eigen assertion）。启动后保持相机平移+旋转移动，终端看到 `Initialization finish!` 即完成。

---

## 7. D435i 外参标定

IMU→相机外参（`body_T_cam0` / `body_T_cam1`）不能依赖 repo 默认值（差 6cm），必须从固件读取：

```sh
python3 scripts/read_d435i_calib.py
```

将输出粘贴到 YAML 中，并设置 `estimate_extrinsic: 0`。

---

## 8. 参数清单

| 参数 | 当前值 | 来源 |
|------|--------|------|
| `acc_n` | 0.0080 | imu_utils 标定 |
| `gyr_n` | 0.0019 | imu_utils 标定 |
| `acc_w` | 0.00214 | imu_utils 标定 |
| `gyr_w` | 1.51e-4 | imu_utils 标定 |
| `g_norm` | 9.345 | imu_utils 标定 |
| `body_T_cam0/1` | 固件真值 | `read_d435i_calib.py` |
| `estimate_extrinsic` | 0 | 信任固件 |
| `estimate_td` | 1 | 在线估计时间偏移 |
| `show_track` | 1 | 发布追踪图 |
| `save_image` | 1 | 发布回环匹配图 |
| `enable_sync` | false | 避免降帧率 |
