# ORB-SLAM3 使用

## 编译

```sh
cd /home/orin/Desktop/00/FAST_LIO/src/localization/ORB_SLAM3
cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(nproc)
```

## 运行

### Stereo-Inertial（推荐，当前使用）

```sh
cd /home/orin/Desktop/00/FAST_LIO/src/localization/ORB_SLAM3

# 新建图
./Examples/Stereo-Inertial/stereo_inertial_realsense_D435i \
  Vocabulary/ORBvoc.txt \
  Examples/Stereo-Inertial/RealSense_D435i.yaml

# 加载已有地图 → 在 YAML 里取消注释 LoadAtlasFromFile
# System.LoadAtlasFromFile: "map/0723"
```

- **第四个参数是轨迹文件名前缀**，不是地图路径
- **地图加载/保存靠 YAML** 里的 `System.LoadAtlasFromFile` / `System.SaveAtlasToFile`
- 保存格式：Boost 二进制序列化 `.osa`（Atlas = 所有 Map + KeyFrame + MapPoint）
- 加载后直接定位，不需要重新初始化。如需纯定位不建新 KF，调用 `ActivateLocalizationMode()`
- Viewer 里点 Stop → 自动保存地图 + 轨迹 → 退出

### Monocular-Inertial

```sh
./Examples/Monocular-Inertial/mono_inertial_realsense_D435i \
  Vocabulary/ORBvoc.txt \
  Examples/Monocular-Inertial/RealSense_D435i.yaml
```

同上，地图路径在对应 YAML 里配置。

## 相机传感器

Mono 和 Stereo 都用的 **红外摄像头**，不走 ROS topic，直接用 librealsense2 SDK 开硬件流：

| 模式 | 传感器 | 分辨率 | 帧率 |
|------|--------|--------|------|
| Mono-Inertial | `RS2_STREAM_INFRARED, 1`（左红外） + ACCEL + GYRO | 640×480 | 30 |
| Stereo-Inertial | `RS2_STREAM_INFRARED, 1` + `, 2`（左右红外） + ACCEL + GYRO | 640×480 | 30 |

D435i 的 RGB 摄像头全程没用，ORB 特征提取跑灰度图，红外够用。

## YAML 关键配置

```yaml
# 加载已有地图（注释掉 = 从头建图）
# System.LoadAtlasFromFile: "map/0723"

# 保存路径（Shutdown 时自动保存）
System.SaveAtlasToFile: "map/last_map"

# 双目基线×焦距（50mm × 382.6）
Camera.bf: 19.13

# 左到右外参
Stereo.T_c1_c2: !!opencv-matrix
   data: [1,0,0,0.0503, 0,1,0,0, 0,0,1,0, 0,0,0,1]
```

## 地图文件

- `.osa` — Atlas 二进制文件，含 KeyFrame、MapPoint、共视图，通常几 MB~几十 MB
- 存在 `./map/` 目录下，路径相对于可执行文件运行目录
- 同名文件会被覆盖（Shutdown 时 SaveAtlas 先 `std::remove` 再写）

## 已修复问题

| 问题 | 文件 | 修复 |
|------|------|------|
| PreSave 迭代器失效 segfault | `MapPoint.cc` | 先收集待删除再 erase |
| Shutdown 后 LocalMapper 不退出 | `System.cc` | 加 `RequestStop()` |
| Viewer 线程未通知退出 | `System.cc` | 加 `mpViewer->RequestFinish()` |
| 双目 YAML 缺 Camera2/bf/T_c1_c2 | `RealSense_D435i.yaml` | 补全双目参数 |
| 加载地图失败直接 exit(-1) | `System.cc` | 改为创建新 Atlas |
| Sophus -Werror 编译失败 | `Sophus/CMakeLists.txt` | 移除 -Werror |
| monotonic_clock 编译错误 | 全局 | sed 替换为 steady_clock |

## 已知限制

- 沙盘低速+弱纹理 → IMU 初始化困难，建议手持初始化后装车
- D435i 红外图分辨率 640×480，ORB 特征 1250，够用但不富余
- Qt/Pangolin 退出时有 `QObject::~QObject` warning，不影响地图保存
- 大场景需要更多 KF，`.osa` 文件会显著增大
