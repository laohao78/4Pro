# FAST-Calib LiDAR-Camera 外参标定

## 0. 前置要求

- D435i RGB 相机内参已从固件读取
- 标定板已打印制作（0.5x scale，所有尺寸减半）
- 本篇使用离线 rosbag + 图像，标定时**不需要传感器在线**

---

## 1. 启动驱动录制 rosbag

```sh
cd /home/orin/Desktop/00/FAST_LIO
source devel/setup.bash

# 必须 xfer_format:=0 (PointCloud2)！FAST-Calib 不吃 CustomMsg
roslaunch livox_ros_driver2 rviz_MID360.launch xfer_format:=0
roslaunch realsense2_camera rs_camera.launch
```

三个角度各录 10 秒：

```sh
cd ~/Desktop/00/FAST_LIO/src/dependent/FAST-Calib

# 正面
rosbag record /livox/lidar /camera/color/image_raw -O calib_data/scene1.bag --duration=10

# 左侧
rosbag record /livox/lidar /camera/color/image_raw -O calib_data/scene2.bag --duration=10

# 右侧
rosbag record /livox/lidar /camera/color/image_raw -O calib_data/scene3.bag --duration=10
```

---

## 2. 从 bag 中抽图像

每个场景抽一帧中间时刻的图像：

```sh
cd ~/Desktop/00/FAST_LIO/src/dependent/FAST-Calib

python3 -c "
import rosbag, cv2
from cv_bridge import CvBridge
bridge = CvBridge()
for scene in ['scene1','scene2','scene3']:
    bag = rosbag.Bag(f'calib_data/{scene}.bag')
    imgs = [(t.to_sec(), m) for _, m, t in bag.read_messages(topics=['/camera/color/image_raw'])]
    mid = imgs[len(imgs)//2]
    cv2.imwrite(f'calib_data/{scene}.jpg', bridge.imgmsg_to_cv2(mid[1], 'bgr8'))
    bag.close()
    print(f'{scene}.jpg saved')
"
```

---

## 3. 配置 qr_params.yaml

### 3.1 相机内参

D435i RGB 640x480@30Hz 固件真值：

```yaml
  fx: 612.43
  fy: 611.03
  cx: 327.04
  cy: 252.74
  k1: 0.0
  k2: 0.0
  p1: 0.0
  p2: 0.0
```

### 3.2 标定板参数

0.5x scale：

```yaml
  marker_size: 0.10
  delta_width_qr_center: 0.275
  delta_height_qr_center: 0.175
  delta_width_circles: 0.25
  delta_height_circles: 0.2
  circle_radius: 0.06
```

### 3.3 距离滤波器阈值

每个场景的板子位置不同，**必须分别调**。

#### 叠加全帧点云（供 Open3D 选点）

```sh
cd ~/Desktop/00/FAST_LIO/src/dependent/FAST-Calib

python3 << 'EOF'
import rosbag
from sensor_msgs import point_cloud2 as pc2

for scene in ['scene1','scene2','scene3']:
    bag = rosbag.Bag(f'calib_data/{scene}.bag')
    pts = []
    for _, msg, _ in bag.read_messages(topics=['/livox/lidar']):
        for x, y, z, i in pc2.read_points(msg, field_names=['x','y','z','intensity'], skip_nans=True):
            if 1.0<x<6.0 and -4.0<y<4.0 and -1.0<z<2.0:  # 宽松粗过滤
                pts.append((x,y,z,i))
    bag.close()
    with open(f'calib_data/{scene}_all.pcd','w') as f:
        f.write(f"""# .PCD v0.7
VERSION 0.7
FIELDS x y z intensity
SIZE 4 4 4 4
TYPE F F F F
COUNT 1 1 1 1
WIDTH {len(pts)}
HEIGHT 1
POINTS {len(pts)}
DATA ascii
""")
        for x,y,z,i in pts: f.write(f"{x} {y} {z} {i}\n")
    print(f'{scene}: {len(pts)} 点')
EOF
```

#### Open3D 交互选点

```sh
python3 -c "
import open3d as o3d, numpy as np

pcd = o3d.io.read_point_cloud('calib_data/scene1_all.pcd')  # 改 scene2/scene3
vis = o3d.visualization.VisualizerWithEditing()
vis.create_window('Shift+左键选4点框住标定板 → Q')
vis.add_geometry(pcd)
vis.run(); vis.destroy_window()

idx = vis.get_picked_points()
if len(idx) >= 4:
    pts = np.asarray(pcd.points)[idx[:4]]
    lo, hi = pts.min(axis=0)-0.2, pts.max(axis=0)+0.2
    print(f'x_min:{lo[0]:.1f}  x_max:{hi[0]:.1f}')
    print(f'y_min:{lo[1]:.1f}  y_max:{hi[1]:.1f}')
    print(f'z_min:{lo[2]:.1f}  z_max:{hi[2]:.1f}')
"
```

把输出的值填进 `qr_params.yaml` 的 Distance filter 区。

---

## 4. 逐场景标定

每个场景跑一次 `calib.launch`，圆心追加写入 `circle_center_record.txt`：

```sh
cd /home/orin/Desktop/00/FAST_LIO
source devel/setup.bash

# scene1: 改 qr_params.yaml 的 bag_path + image_path 指向 scene1
roslaunch fast_calib calib.launch

# scene2: 改 qr_params.yaml 指向 scene2
roslaunch fast_calib calib.launch

# scene3: 改 qr_params.yaml 指向 scene3
roslaunch fast_calib calib.launch
```

每场景需检测到 4 个边缘簇 + 4 个圆心，否则 check 距离滤波器或标定板参数。

`single_calib_result.txt` 每次覆盖（仅看当前场景），`circle_center_record.txt` 追加写入。

---

## 5. 多场景联合求解

```sh
roslaunch fast_calib multi_calib.launch
```

读取 `output/circle_center_record.txt` 中最后 3 个 block（12 对圆心），输出 `output/multi_calib_result.txt`：

```
Rcl: [...]   # LiDAR → Camera 旋转
Pcl: [...]   # LiDAR → Camera 平移
```

直接拷贝进 FAST-LIVO2 的 `config/mid360_d435i.yaml` → `extrin_calib` 段。

---

## 6. 标定结果 (2026-07-28)

| 场景 | RMSE |
|------|------|
| scene1 (正面) | 1.7mm |
| scene2 (左侧) | 0.6mm |
| scene3 (右侧) | 1.7mm |
| **联合求解** | **6.7mm** |

```yaml
extrin_calib:
  Rcl: [-0.103501, -0.994620, -0.004300,
        -0.028254,  0.007261, -0.999574,
         0.994228, -0.103336, -0.028854]
  Pcl: [0.072124, -0.024821, -0.201867]
```
