#!/usr/bin/env python3
"""从静止 IMU 录制数据估算噪声参数 (近似 Allan 方差)"""

import rosbag
import numpy as np
import sys

bag_path = sys.argv[1] if len(sys.argv) > 1 else "/home/orin/Desktop/00/FAST_LIO/dependent/imu_static.bag"

bag = rosbag.Bag(bag_path)
gyro_x, gyro_y, gyro_z = [], [], []
acc_x, acc_y, acc_z = [], [], []
timestamps = []

for topic, msg, t in bag.read_messages(topics=["/camera/imu"]):
    gyro_x.append(msg.angular_velocity.x)
    gyro_y.append(msg.angular_velocity.y)
    gyro_z.append(msg.angular_velocity.z)
    acc_x.append(msg.linear_acceleration.x)
    acc_y.append(msg.linear_acceleration.y)
    acc_z.append(msg.linear_acceleration.z)
    timestamps.append(msg.header.stamp.to_sec())

bag.close()

gyro = np.column_stack([gyro_x, gyro_y, gyro_z])
acc = np.column_stack([acc_x, acc_y, acc_z])
dt = np.mean(np.diff(timestamps))

print(f"===== 静止 IMU 分析 =====")
print(f"消息数: {len(timestamps)}")
print(f"采样间隔: {dt*1000:.2f} ms")
print(f"频率: {1.0/dt:.1f} Hz")
print()

# --- 角速度噪声 (gyr_n) ---
# 静止时角速度标准差 = 陀螺噪声密度
gyro_std = np.std(gyro, axis=0)
gyr_n = np.mean(gyro_std)
print(f"陀螺标准差 (rad/s): x={gyro_std[0]:.6f}, y={gyro_std[1]:.6f}, z={gyro_std[2]:.6f}")
print(f"gyr_n (均值): {gyr_n:.6f}")

# --- 加速度噪声 (acc_n) ---
acc_std = np.std(acc, axis=0)
acc_n = np.mean(acc_std)
print(f"\n加速度标准差 (m/s²): x={acc_std[0]:.6f}, y={acc_std[1]:.6f}, z={acc_std[2]:.6f}")
print(f"acc_n (均值): {acc_n:.6f}")

# --- 重力幅值 ---
g_norm = np.mean(np.linalg.norm(acc, axis=1))
print(f"\n重力幅值: {g_norm:.4f} m/s²")

# --- Bias 随机游走 (gyr_w, acc_w) ---
# 用 Allan 方差的简单近似: sigma(tau) ~ Q / sqrt(tau)
# 在 1s 间隔上计算 bias 方差来估算
cluster_size = int(1.0 / dt)  # 1 秒内样本数
n_clusters = len(gyro) // cluster_size

if n_clusters > 10:
    gyro_means = np.array([np.mean(gyro[i*cluster_size:(i+1)*cluster_size], axis=0) for i in range(n_clusters)])
    acc_means = np.array([np.mean(acc[i*cluster_size:(i+1)*cluster_size], axis=0) for i in range(n_clusters)])

    gyro_w = np.mean(np.std(gyro_means, axis=0))  # 1s 间隔的陀螺 bias 标准差 = gyr_w
    acc_w = np.mean(np.std(acc_means, axis=0))     # 1s 间隔的加速度 bias 标准差 = acc_w

    print(f"\nBias 随机游走 (1s 间隔):")
    print(f"gyr_w: {gyro_w:.2e}")
    print(f"acc_w: {acc_w:.2e}")
else:
    gyro_w = gyr_n * 0.01
    acc_w = acc_n * 0.01
    print(f"\n数据不足, 粗略估算:")
    print(f"gyr_w: {gyro_w:.2e}")
    print(f"acc_w: {acc_w:.2e}")

print(f"""
===== 建议填入 config 的值 =====
acc_n: {acc_n:.4f}
gyr_n: {gyr_n:.4f}
acc_w: {acc_w:.2e}
gyr_w: {gyro_w:.2e}
g_norm: {g_norm:.4f}
=================================
""")
