# 地图文件记录

## 坐标系

z=0 = livox_frame 高度 ≈ 18cm 离地，ground ≈ -0.18

## 生成工具

`src/nav_bringup/scripts/pcd2pgm_node.py`，已修复 Y 轴翻转。

```sh
pcl_convert_pcd_ascii_binary input.pcd /tmp/uncompressed.pcd 0
python3 src/nav_bringup/scripts/pcd2pgm_node.py /tmp/uncompressed.pcd output z_min z_max
```

## 文件清单

| 文件 | z_min | z_max | 说明 |
|------|-------|-------|------|
| `v1.pgm` | -0.05 | 0.06 | 测试 |
| `v3.pgm` | -0.08 | 0.08 | ⭐ 最佳效果 |
| `v4.pgm` | -0.10 | 0.10 | 测试 |
| `v5.pgm` | -0.03 | 0.03 | 最窄测试 |
| `sand_table.pgm` | -0.08 | 0.08 | **生产用**（围栏层，精修后） |
| `sand_table_v2.pgm` | -0.20 | -0.08 | 错误参数，几乎空白 |
| `sand_table_z4065.pgm` | -0.40 | 0.65 | 宽范围，基本全量 |
| `my_map.pgm` | — | — | slam_toolbox 在线建图 |
| `my_map1.pgm` | — | — | slam_toolbox 在线建图 |
| `0725.*` | -0.08 | 0.08 | **slam_toolbox 定位用**（.posegraph + .data + .pgm + .yaml） |

## NDT 定位 PCD

| 文件 | 大小 | 说明 |
|------|------|------|
| `../src/localization/ndt_localizer/map/scans.pcd` | 309MB | NDT 当前用 |
| `../src/localization/FAST_LIO/myPCD/scans.pcd` | — | 完整原始 PCD |
| `../src/localization/FAST_LIO/myPCD/scans-RGB-segmented2.pcd` | — | 沙盘分离 PCD（PGM 由此生成） |

## PGM 像素含义

- 黑 (0) = 占据（不可通行）
- 白 (254) = 空闲（可通行）
- 灰 (205) = 未知
