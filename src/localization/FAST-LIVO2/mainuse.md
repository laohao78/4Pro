# FAST-LIVO2 复现记录

## 运行

```sh
cd ~/Desktop/00/FAST_LIO
source devel/setup.bash
roslaunch fast_livo mapping_mid360_d435i.launch rviz:=true
```

> 首次使用需先用 [FAST-Calib](https://github.com/hku-mars/FAST-Calib) 标定 LiDAR-Camera 外参，填入 `config/mid360_d435i.yaml` 的 `Rcl` 和 `Pcl`。

---

## 踩坑记录

### 1. CATKIN_IGNORE 阻止编译

源码目录 `FAST-LIVO2/` 自带 `CATKIN_IGNORE` 文件，catkin 会跳过该包。

**修复**：删除该文件
```sh
rm src/localization/FAST-LIVO2/CATKIN_IGNORE
```

### 2. Sophus 安装

FAST-LIVO2 依赖 Sophus（`a621ff` 版本），Ubuntu 软件源无此包，需手动编译。

```sh
git clone https://github.com/strasdat/Sophus.git
cd Sophus && git checkout a621ff
mkdir build && cd build && cmake .. && make -j$(nproc)
sudo make install
```

#### 2.1 Eigen 3.4 兼容问题

`so2.cpp:32` 报错 `lvalue required as left operand`：
```cpp
// 错误 (Eigen 3.4+ 中 .real()/.imag() 返回右值)
unit_complex_.real() = 1.;
unit_complex_.imag() = 0.;

// 修复
unit_complex_ = Complexd(1, 0);
```

#### 2.2 Sophus CMake 不导出 Sophus_LIBRARIES

Sophus 的 `make install` 不安装 CMake config，导致 `FIND_PACKAGE(Sophus)` 后 `${Sophus_LIBRARIES}` 为空，vikit 链接时 undefined reference。

**修复**：`vikit_common/CMakeLists.txt` 和 `vikit_ros/CMakeLists.txt` 中显式添加：
```cmake
TARGET_LINK_LIBRARIES(${PROJECT_NAME}
  ${OpenCV_LIBS}
  ${Sophus_LIBRARIES}
  /usr/local/lib/libSophus.so    # 显式链接
  ${catkin_LIBRARIES})
```

### 3. vikit test 链接失败

vikit 的 test 可执行文件即使 `CATKIN_ENABLE_TESTING=OFF` 也会被编译，且之前因 Sophus 链接问题失败。

**修复**：修复 Sophus 链接后自动解决。

### 4. OpenCV 4.x 编译错误

与 VINS-Fusion 相同的 OpenCV 3.x → 4.x API 问题，已在之前的批量修复中处理。详见 [VINS-Fusion/mainuse.md](../VINS-Fusion/mainuse.md)。

---

## 配置文件

| 文件 | 说明 |
|---|---|
| `config/mid360_d435i.yaml` | MID360 LiDAR + D435i Camera 主配置（新建） |
| `config/camera_d435i.yaml` | D435i 相机内参（新建） |
| `launch/mapping_mid360_d435i.launch` | 启动文件（新建） |

---

## LiDAR-Camera 外参标定

配置中 `Rcl` / `Pcl` 当前为占位值，**正式使用前必须标定**：

```yaml
# config/mid360_d435i.yaml
extrin_calib:
  Rcl: [0, -1, 0, -1, 0, 0, 0, 0, -1]   # ← 需 FAST-Calib 标定
  Pcl: [0.13, 0.0, -0.05]                # ← 需 FAST-Calib 标定
```

使用 [FAST-Calib](https://github.com/hku-mars/FAST-Calib) 一键标定。

---

## 工作流程

```sh
# 终端1: 启动 FAST-LIVO2
roslaunch fast_livo mapping_mid360_d435i.launch rviz:=true

# 终端2: 启动 LiDAR 驱动 (如果没自动启动)
roslaunch livox_ros_driver2 msg_MID360.launch

# 终端3: 启动 D435i 驱动 (如果没自动启动)
roslaunch realsense2_camera rs_camera.launch \
  enable_color:=false enable_depth:=false \
  enable_infra1:=true enable_infra2:=true \
  enable_gyro:=true enable_accel:=true
```
