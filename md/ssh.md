# 远程连接方式

Jetson Orin NX 多种连接方式，按场景选。

## 1. VSCode-SSH（日常开发推荐）

代码编辑 + 命令行一体。

```sh
ssh orin@<jetson_ip>
```

## 2. VSCode-WSL ROS 节点共享

Windows WSL 和 Jetson 跑同一个 ROS master，节点互通。

```sh
export ROS_MASTER_URI=http://<jetson_ip>:11311
export ROS_IP=<wsl_ip>
```

## 3. MobaXterm-SSH + X Server

SSH 命令行 + X11 图形转发（RViz 等 GUI 回传 Windows 显示）。

```sh
ssh -X orin@<jetson_ip>
```

## 4. MobaXterm-Serial

USB 串口直连，最轻量，不需要网络。拨码开关或系统崩溃时救命用。

```
波特率: 115200, 设备: /dev/ttyUSB0
```

## 5. 显示屏 HDMI/DP

直接插显示器，最原始但最可靠。

## 6. RealVNC

SSH 隧道 + VNC 远程桌面。

```sh
# Jetson 上启动
vncserver :1
# 本地连接 <jetson_ip>:5901
```

## 7. Foxglove-SSH

浏览器可视化，WebSocket 连接 Jetson ROS master。最推荐 — 不消耗 Jetson GPU 渲染。

```sh
# Jetson 上启动 rosbridge
roslaunch rosbridge_server rosbridge_websocket.launch
# Foxglove 里填 ws://<jetson_ip>:9090
```
