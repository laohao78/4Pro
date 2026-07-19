# 一、项目概述
- 项目名称：livox_ros_driver2
- 项目简介：livox激光雷达驱动程序

## 版本
- 版本：1.0.0
- 日期：2024.06

# 二、软件构架
- ubuntu 20.04
- ROS noetic


# 三、硬件传感器
- livox mid-360激光雷达

# 四、安装教程
1. 将功能包下载到系统中，解压后复制到 `your_workspace`/src 目录下
2. 在`your_workspace`目录下打开终端，输入：catkin_make 进行工作空间编译


# 五、使用说明
## 5.1 雷达连接配置
1. 连接雷达网口线到设备上，并配置网关IP地址(具体参见 `livox-mid-360用户手册` )

## 5.2 运行Lidar
1. ROS 运行激光雷达驱动程序
```shell
$ source ../../devel/setup.sh
$ roslaunch livox_ros_driver2 msg_MID360.launch
```


# 六、接口文档
## 1. 启动文件和 livox_ros_driver2 内部参数配置说明
具体参数配置说明请参考：
- `./Livox_ROS_Driver 2.pdf`

# 许可证
说明项目的许可证类型。