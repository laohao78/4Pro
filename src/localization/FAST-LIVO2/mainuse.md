# FAST-LIVO2 复现记录

## 运行

一键启动（驱动 + D435i + sync_node + FAST-LIVO2 + RViz）：

```sh
cd ~/Desktop/00/FAST_LIO
source devel/setup.bash
roslaunch fast_livo mapping_mid360_d435i.launch rviz:=true
```

> 外参已通过 FAST-Calib 标定完成（2026-07-28，3 场景联合 RMSE 6.7mm），直接可用。

---

## 标定状态

| 项目 | 值 | 来源 | 状态 |
|------|-----|------|:--:|
| IMU→LiDAR | T=[-0.011, -0.02329, 0.04412] R=I | Livox 出厂 | ✅ |
| RGB 相机内参 | fx=612.43 fy=611.03 cx=327.04 cy=252.74 | D435i 固件 | ✅ |
| LiDAR→Camera | Rcl/Pcl 见下 | FAST-Calib | ✅ |

```yaml
extrin_calib:
  extrinsic_T: [-0.011, -0.02329, 0.04412]
  extrinsic_R: [1, 0, 0, 0, 1, 0, 0, 0, 1]
  Rcl: [-0.103501, -0.994620, -0.004300,
        -0.028254,  0.007261, -0.999574,
         0.994228, -0.103336, -0.028854]
  Pcl: [0.072124, -0.024821, -0.201867]
```

## 软同步机制

```
LiDAR 驱动 → /livox/lidar (CustomMsg, 10Hz) ──┐
               /livox/imu  (200Hz)              │
                                                ├─ sync_node (10Hz timer)
D435i RGB  → /camera/color/image_raw (30Hz) ────┘
                                                │
                                    缓存最新帧，定时器触发
                                    图像时间戳 ← LiDAR 时间戳
                                                │
                                   ┌────────────┘
                                   ▼
                             /synced_image
                             /synced_lidar
                                   │
                                   ▼
                             FAST-LIVO2
```

`synchronized_node` 从 `livox_camera_sync` 包（ZhifangFu/livox_ros_driver2 精简而来），**独立于官方驱动**。核心逻辑：

```cpp
// 10Hz 定时器：用 LiDAR 时间戳盖掉图像时间戳
sync_stamp = last_lidar_msg.header.stamp;
last_image_msg.header.stamp = sync_stamp;
publish /synced_image, /synced_lidar;
```

实际有几十 ms 误差，但直接法光度优化能容忍。D435i 无法硬同步是硬伤，长期需换相机。

---

## 配置文件

| 文件 | 说明 |
|------|------|
| `config/mid360_d435i.yaml` | 唯一配置（已合并：主参数 + 相机内参） |
| `launch/mapping_mid360_d435i.launch` | 一键启动：LiDAR驱动+D435i+sync+FAST-LIVO2+RViz |

---

## LiDAR-Camera 外参标定

标定流程详见 [FAST-Calib/mainuse.md](../../dependent/FAST-Calib/mainuse.md)。

### 结果 (2026-07-28)

| 场景 | RMSE |
|------|------|
| scene1 (正面) | 1.7mm |
| scene2 (左侧) | 0.6mm |
| scene3 (右侧) | 1.7mm |
| **联合求解** | **6.7mm** |

---

## B站复现经验

来源：[ZhifangFu](https://github.com/ZhifangFu/livox_ros_driver2) 的 B站视频评论区

### 1. 硬件

手持式装置：Mid360 + D435i + Orin NX。

> **不要买 D435i**——D435i 无法硬件同步，建议选支持硬触发曝光的相机。

### 2. 软同步驱动

原方案用 ZhifangFu/livox_ros_driver2 代替官方驱动。我们已将其精简为独立包 `livox_camera_sync`：
- 官方驱动 `livox_ros_driver2` 保持纯净，不受影响
- 软同步作为独立节点运行，按需使用

### 3. OpenCV 版本

报错 `process has died` 大概率是 OpenCV 版本太高，**换成 4.2.0**。

### 4. 效果糊 ≈ 没有硬同步

已排除标定原因，最终判断是软同步的锅——LiDAR 点和图像不是同一时刻采集的，投影像素有偏差，导致光度误差项不可靠，重建发糊。

---

## 踩坑记录

### 1. CATKIN_IGNORE 阻止编译

FAST-LIVO2 源码自带 `CATKIN_IGNORE`，catkin 跳过该包。删除之：

```sh
rm src/localization/FAST-LIVO2/CATKIN_IGNORE
```

### 2. Sophus 安装

依赖 Sophus `a621ff` 版本：

```sh
git clone https://github.com/strasdat/Sophus.git
cd Sophus && git checkout a621ff
mkdir build && cd build && cmake .. && make -j$(nproc)
sudo make install
```

#### 2.1 Eigen 3.4 兼容

`so2.cpp:32` — `.real()/.imag()` 返回右值：

```cpp
// 错误
unit_complex_.real() = 1.;
// 修复
unit_complex_ = Complexd(1, 0);
```

#### 2.2 Sophus_LIBRARIES 为空

Sophus 不安装 CMake config，vikit 需显式链接：

```cmake
TARGET_LINK_LIBRARIES(${PROJECT_NAME} /usr/local/lib/libSophus.so)
```

### 3. OpenCV 4.x

与 VINS-Fusion 相同的 API 兼容问题，已批量修复。

### 4. launch 配置加载

`nh.param()` 用全局 handle，vikit 的 `loadFromRosNs` 查私有命名空间。同一 YAML 需加载两次：

```xml
<rosparam command="load" file="..." />   <!-- 全局 -->
<node ...>
    <rosparam file="..." />              <!-- 私有 -->
</node>
```
