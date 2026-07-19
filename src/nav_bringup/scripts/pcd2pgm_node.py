#!/usr/bin/env python3
"""
PCD → 栅格地图 (.pgm + .yaml)
基于 LihanChen2004/pcd2pgm 的算法，适配 ROS1 Noetic

用法: python3 pcd2pgm_node.py <input.pcd> <output_prefix>
"""
import sys
import struct
import numpy as np
import os

# ---------- PCD 读取 ----------
def load_pcd(path):
    """读取 PCD (支持 binary 和 binary_compressed)，返回 (xyz, intensity)"""
    with open(path, 'rb') as f:
        header_lines = []
        for line in f:
            line = line.decode().strip()
            header_lines.append(line)
            if line.startswith('DATA'):
                data_type = line.split()[1]
                break
        offset = f.tell()
        raw = f.read()

    # 解析头部
    header = {}
    for line in header_lines:
        if line.startswith('FIELDS'):
            header['fields'] = line.split()[1:]
        elif line.startswith('SIZE'):
            header['size'] = [int(x) for x in line.split()[1:]]
        elif line.startswith('TYPE'):
            header['type'] = line.split()[1:]
        elif line.startswith('COUNT'):
            header['count'] = [int(x) for x in line.split()[1:]]
        elif line.startswith('WIDTH'):
            header['width'] = int(line.split()[1])
        elif line.startswith('HEIGHT'):
            header['height'] = int(line.split()[1])
        elif line.startswith('POINTS'):
            header['points'] = int(line.split()[1])

    n_points = header['points']
    fields = header['fields']
    types = header['type']
    sizes = header['size']

    # 计算每行字节
    row_size = sum(sizes)

    # 找 xyz 索引
    x_idx = fields.index('x')
    y_idx = fields.index('y')
    z_idx = fields.index('z')

    if data_type == 'ascii':
        data = np.loadtxt(path, skiprows=len(header_lines))
        xyz = data[:, [x_idx, y_idx, z_idx]]
    elif data_type == 'binary':
        dt = np.dtype([(f, np.float32) for f in fields])
        data = np.frombuffer(raw, dtype=dt, count=n_points)
        xyz = np.column_stack([data['x'], data['y'], data['z']])
    elif data_type == 'binary_compressed':
        # compressed_size (4 bytes) + uncompressed_size (4 bytes) + lzf data
        compressed_size = struct.unpack('I', raw[:4])[0]
        uncompressed_size = struct.unpack('I', raw[4:8])[0]
        compressed = raw[8:8 + compressed_size]

        try:
            import lzf
            decompressed = lzf.decompress(compressed, uncompressed_size)
        except ImportError:
            import subprocess
            # fallback: write compressed data and use pylzf command
            tmp_in = '/tmp/_pcd_lzf_in.bin'
            tmp_out = '/tmp/_pcd_lzf_out.bin'
            open(tmp_in, 'wb').write(compressed)
            subprocess.run(['python3', '-c',
                f'import lzf; d=lzf.decompress(open("{tmp_in}","rb").read(),{uncompressed_size}); open("{tmp_out}","wb").write(d)'],
                check=True)
            decompressed = open(tmp_out, 'rb').read()

        dt = np.dtype([(f, np.float32) for f in fields])
        data = np.frombuffer(decompressed, dtype=dt, count=n_points)
        xyz = np.column_stack([data['x'], data['y'], data['z']])

    return xyz

# ---------- PassThrough 高度滤波 ----------
def pass_through(xyz, z_min, z_max):
    """保留 z 在 [z_min, z_max] 之间的点"""
    mask = (xyz[:, 2] >= z_min) & (xyz[:, 2] <= z_max)
    return xyz[mask]

# ---------- RadiusOutlier 去噪 ----------
def radius_outlier(xyz, radius=0.1, min_neighbors=10):
    """去除孤立噪点：半径 radius 内邻居数 < min_neighbors 的点"""
    from scipy.spatial import cKDTree
    tree = cKDTree(xyz[:, :3])
    counts = tree.query_ball_point(xyz[:, :3], radius, return_length=True)
    return xyz[counts >= min_neighbors]

# ---------- 投影到栅格 ----------
def project_to_grid(xyz, resolution=0.05):
    """XY 投影为占据栅格，返回 (grid, x_origin, y_origin, width, height)"""
    x_min, x_max = xyz[:, 0].min(), xyz[:, 0].max()
    y_min, y_max = xyz[:, 1].min(), xyz[:, 1].max()

    width = int(np.ceil((x_max - x_min) / resolution))
    height = int(np.ceil((y_max - y_min) / resolution))

    grid = np.zeros((height, width), dtype=np.uint8)
    xi = np.floor((xyz[:, 0] - x_min) / resolution).astype(int)
    yi = np.floor((xyz[:, 1] - y_min) / resolution).astype(int)
    grid[yi, xi] = 100  # 占据

    return grid, x_min, y_min, width, height

# ---------- 保存 .pgm + .yaml ----------
def save_pgm_yaml(grid, x_origin, y_origin, resolution, out_prefix):
    """保存 PGM 和 YAML"""
    pgm_path = out_prefix + '.pgm'
    yaml_path = out_prefix + '.yaml'

    # 100=占据(黑), 0=空(白)
    img = np.full_like(grid, 254, dtype=np.uint8)  # 默认空
    img[grid == 100] = 0  # 占据=黑

    # 翻转: PGM row=0=图像顶部=世界Ymax, grid[0]=世界Ymin
    img = np.flipud(img)

    h, w = img.shape
    with open(pgm_path, 'wb') as f:
        f.write(f'P5\n{w} {h}\n255\n'.encode())
        f.write(img.tobytes())

    with open(yaml_path, 'w') as f:
        f.write(f'image: {os.path.basename(pgm_path)}\n')
        f.write(f'resolution: {resolution}\n')
        f.write(f'origin: [{x_origin}, {y_origin}, 0.0]\n')
        f.write('negate: 0\n')
        f.write('occupied_thresh: 0.45\n')
        f.write('free_thresh: 0.2\n')

    print(f'Grid: {w}x{h} ({w*resolution:.2f}m x {h*resolution:.2f}m)')
    print(f'Saved: {pgm_path}')
    print(f'       {yaml_path}')

# ---------- main ----------
if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(f'Usage: {sys.argv[0]} <input.pcd> <output_prefix> <z_min> <z_max>')
        print(f'  z_min/z_max: 高度过滤范围 (体坐标系)')
        print(f'Example: {sys.argv[0]} scans.pcd my_map -0.05 0.06')
        sys.exit(1)

    pcd_path = sys.argv[1]
    out_prefix = sys.argv[2]
    z_min = float(sys.argv[3])
    z_max = float(sys.argv[4])

    print(f'Loading: {pcd_path}')
    xyz = load_pcd(pcd_path)
    print(f'  Original: {len(xyz)} points')

    print(f'PassThrough z=[{z_min}, {z_max}]')
    xyz = pass_through(xyz, z_min, z_max)
    print(f'  After passthrough: {len(xyz)} points')

    # RadiusOutlier 可选，数据干净可以跳过
    try:
        from scipy.spatial import cKDTree
        print('RadiusOutlier r=0.1, min=10')
        xyz = radius_outlier(xyz, radius=0.1, min_neighbors=10)
        print(f'  After outlier: {len(xyz)} points')
    except ImportError:
        print('  (scipy not available, skip RadiusOutlier)')

    print(f'Projecting to grid res=0.02')
    grid, x_origin, y_origin, w, h = project_to_grid(xyz, resolution=0.02)
    save_pgm_yaml(grid, x_origin, y_origin, 0.02, out_prefix)
