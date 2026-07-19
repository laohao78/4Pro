# 一、项目概述
- 项目名称：chasis_control
- 项目简介：底盘控制功能包，包含上位机和底盘的通信接口，底盘控制算法等。

## 版本
- 版本：1.0.0
- 日期：2024.06

# 二、软件构架
- ubuntu 18.04/20.04
- ROS melodic/noetic
- Python 3.8

# 三、硬件传感器
- 单片机
- 编码器
- 电调
- 电机
- 舵机

# 四、安装教程
1. 将功能包下载到系统中，解压后复制到 `your_workspace`/src 目录下
2. 给python脚本文件添加执行权限。
```shell
$ sudo chmod + x *.py
```
3. 在`your_workspace`目录下打开终端，输入：catkin_make 进行工作空间编译


# 五、使用说明
## 5.1 运行脚本
1、`ROSPY_Orin_chasis_control_202406v1.py`
- 作用：将ROS系统中接收的上位机底盘指令转换为实际控制信号，并通过单片机控制底盘执行上位机指令。
```shell
$ rosrun chasis_control ROSPY_Orin_chasis_control_202406v1.py
```

2、`ROSPY_NX_KeyboardControl_20230601.py`
- 作用：实现键盘遥控底盘
```shell
$ rosrun chasis_control ROSPY_NX_KeyboardControl_20230601.py
```

3、`ROSPY_Moto_PID_202404v1.py`
- 作用：实现电机转速的PID控制
```shell
$ rosrun chasis_control ROSPY_Moto_PID_202404v1.py
```

## 5.2运行launch文件
1、`Ros_Orin_Nx_Keyboardcontrol.launch`
- 作用：键盘控制launch文件
```shell
$ roslaunch chasis_control Ros_Orin_Nx_Keyboardcontrol.launch
```

2、`ROSPY_Orin_Nx_PIDcontrol.launch`
- 作用：PID电机控制launch文件
```shell
$ roslaunch chasis_control ROSPY_Orin_Nx_PIDcontrol.launch
```

# 六、接口文档
##  ROS 接口
1. ROS
   节点名称(脚本文件)： `chasis_control_node` (ROSPY_Orin_chasis_control_202406v1.py)
                     `keyboard_control` (ROSPY_NX_KeyboardControl_20230601.py) 
                     `PID` (ROSPY_Moto_PID_202404v1.py)

   | 话题 | 话题类型 | 话题数据类型 | 说明 |
   `电机`话题
   | `/motor_write_duty` | 订阅 | Float64 | 使用duty（占空比）控制电机 | 
   | `/motor_write_rpm` | 订阅 | Int32 | 使用rpm（转速）控制电机 |
   | `/motor_write_velocity` | 订阅 | Float64 | 使用速度控制电机，单位m/s |
   | `/motor_read_rpm` | 发布 | Int32 | 发布电机当前转速 |
   | `/motor_read_velocity` | 发布 | Float64 | 发布电机当前速度 |

   `舵机`话题
   | /servo_write_position | 订阅 | Int32 | 使用position（转角位置）控制舵机 |
   | /servo_write_delta | 订阅 | Float64 | 使用delta（前轮转角）控制舵机 |
   | /servo_read_position | 发布 | Int32 | 发布舵机角度位置 |
   | /servo_read_delta | 发布 | Float64 | 发布前轮转角 |


# 许可证
说明项目的许可证类型。