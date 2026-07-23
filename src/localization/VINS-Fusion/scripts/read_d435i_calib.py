#!/usr/bin/env python3
"""读取 D435i 出厂标定，输出 VINS-Fusion 格式的 body_T_cam0/1"""
import pyrealsense2 as rs
import numpy as np

ctx = rs.context()
devices = ctx.query_devices()
if len(devices) == 0:
    print("未检测到 RealSense 设备")
    exit(1)

dev = devices[0]
print(f"设备: {dev.get_info(rs.camera_info.name)} S/N: {dev.get_info(rs.camera_info.serial_number)}")

sensors = dev.query_sensors()

# 找到各 sensor
motion = None
stereo = None
for s in sensors:
    name = s.get_info(rs.camera_info.name)
    print(f"Sensor: {name}")
    if name == "Motion Module":
        motion = s
    elif name == "Stereo Module":
        stereo = s

if motion is None or stereo is None:
    print("未找到 Motion Module 或 Stereo Module")
    exit(1)

# 从 Motion Module 获取 Gyro stream profile（是 motion_stream_profile，不是 video）
gyro_profile = None
for p in motion.get_stream_profiles():
    if p.stream_name() == "Gyro":
        gyro_profile = p
        break

# 从 Stereo Module 获取 Infrared 的 stream profiles
infra1_profile = None
infra2_profile = None
for p in stereo.get_stream_profiles():
    pv = p.as_video_stream_profile()
    if p.stream_name() == "Infrared 1":
        infra1_profile = pv
    elif p.stream_name() == "Infrared 2":
        infra2_profile = pv

if gyro_profile is None:
    print("未找到 Gyro stream profile")
    exit(1)

def print_vins_matrix(label, extr):
    """输出 VINS YAML 格式的 4x4 矩阵"""
    R = np.array(extr.rotation).reshape(3, 3)
    T = np.array(extr.translation)
    row_major = np.concatenate([R[0], [T[0]], R[1], [T[1]], R[2], [T[2]]])
    data_str = ", ".join([f"{v:16.13e}" for v in row_major]) + ", 0., 0., 0., 1."
    print(f"{label}: !!opencv-matrix")
    print(f"   rows: 4\n   cols: 4\n   dt: d")
    print(f"   data: [{data_str}]")

# Gyro -> Infrared 1 (cam0) 和 Infrared 2 (cam1)
if infra1_profile:
    e1 = gyro_profile.get_extrinsics_to(infra1_profile)
    print(f"\n# Gyro -> Infrared 1 (body -> cam0)")
    print_vins_matrix("body_T_cam0", e1)

if infra2_profile:
    e2 = gyro_profile.get_extrinsics_to(infra2_profile)
    print(f"\n# Gyro -> Infrared 2 (body -> cam1)")
    print_vins_matrix("body_T_cam1", e2)

# 也输出左目到右目的 baseline
if infra1_profile and infra2_profile:
    try:
        elr = infra1_profile.get_extrinsics_to(infra2_profile)
        print(f"\n# Left IR -> Right IR baseline: {np.array(elr.translation)}")
    except:
        pass
