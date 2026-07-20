# 一、项目概述
- 项目名称：ndt_localizer
- 项目简介：基于livox_mid_360激光雷达数据，ndt点云配准算法，获取RTRC车辆的位姿信息。

## 版本
- 版本：1.0.0
- 日期：2024.07

# 二、软件构架
- ubuntu 20.04
- ROS noetic

# 三、硬件传感器
- livox mid-360激光雷达

# 四、安装教程
1. 将功能包下载到系统中，解压后复制到 `your_workspace`/src 目录下
2. 在`your_workspace`目录下打开终端，输入：catkin_make 进行工作空间编译


# 五、使用说明
具体使用说明参见：
- `./NDT_localizer.pdf`
## 5.1 雷达连接配置
1. 运行ndt_localizer节点,获取定位话题
- 具体参见 `NDT_localizer.pdf` 
```shell
# 打开一个 roscore
$ roscore
# 在其他终端
$ cd catkin_ws
$ source devel/setup.bash
# 启动 ndt_localizer 节点
$ roslaunch ndt_localizer ndt_localizer.launch
```

# 六、接口文档
具体接口及参数配置说明参见：
- `./Livox_ROS_Driver 2.pdf`

## 6.1 ROS 接口
-------------------------------------------------------------------------------------------
   节点名称(脚本文件)： `ndt_localizer` 
   | 话题 | 话题类型 | 话题数据类型 | 说明 |
   | `/ndt_pose` | 发布 | localization | 发布车辆的位姿信息 | 

-------------------------------------------------------------------------------------------

## 6.2 ndt_localizer 定位器参数

```xml
<arg name="trans_epsilon" default="0.05" doc="两次连续变换之间的最大差异，以考虑收敛" />
<arg name="step_size" default="0.1" doc="牛顿线搜索最大步长" />
<arg name="resolution" default="2.0" doc="ND 体素网格分辨率" />
<arg name="max_iterations" default="30.0" doc="计算对齐所需的迭代次数" />
<arg name="converged_param_transform_probability" default="3.0" doc="" />
```

这些默认参数适用于 64 和 32 线 LiDAR。

# 许可证
说明项目的许可证类型。