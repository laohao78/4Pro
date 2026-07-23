# ORB-SLAM3 使用

## 编译

```sh
cd build && cmake .. && make -j$(nproc)
```

已知修复：`monotonic_clock`→`steady_clock`、`AUTO_EXPOSURE_LIMIT` try-catch、Ctrl+C 退出。

## 运行

### Monocular-Inertial

```sh
cd /home/orin/Desktop/00/FAST_LIO/src/localization/ORB_SLAM3

# 建图
./Examples/Monocular-Inertial/mono_inertial_realsense_D435i \
  Vocabulary/ORBvoc.txt \
  Examples/Monocular-Inertial/RealSense_D435i.yaml \
  map/my_map

# 加载地图纯定位
./Examples/Monocular-Inertial/mono_inertial_realsense_D435i \
  Vocabulary/ORBvoc.txt \
  Examples/Monocular-Inertial/RealSense_D435i.yaml \
  map/my_map
```

- 第四个参数是地图名，加就保存/加载，不加就跑不存
- `my_map.osa` 是 Atlas 文件，包含 KeyFrame、MapPoint、共视图，几十 MB
- 存在同名文件→自动加载进 Localization Mode（只定不建）

### Stereo-Inertial

```sh
./Examples/Stereo-Inertial/stereo_inertial_realsense_D435i \
  Vocabulary/ORBvoc.txt \
  Examples/Stereo-Inertial/RealSense_D435i.yaml \
  map/my_map
```

双目已知基线，不需要平移视差，比单目更容易初始化。D435i 当前 segfault 待排查。

## 已知问题

- 沙盘低速+弱纹理→IMU 反复 reset，不适合
- 车装摄像头加速度不够→初始化困难，建议手持初始化后装车
- 双目版可能管线冲突，单目版已确认可用
