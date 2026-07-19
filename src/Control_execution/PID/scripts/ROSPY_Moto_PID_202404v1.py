#!/usr/bin/env python3
#coding=UTF-8

import rospy
from std_msgs.msg import Int32, Float64, String
from simple_pid import PID

RPM_NOW = 0
Target_Rpm = 500
duty_init = 0.03  # 设置初始占空比
previous_z = 0  # 初始化 previous_z
current_x = 0  # 全局变量 current_x
current_y = 0  # 全局变量 current_y
current_z = 0  # 全局变量 current_z，z轴的变化为0-0.4，当前的z值大于上一个z值，说明上坡，目标转速为650，否则下坡，目标转速为100

pid = PID(0.8, 0.1, 0.02, setpoint=0) #设置PID参数，Kp=1.8, Ki=0.1, Kd=0.02, 输出限幅为-4000~4000
pid.output_limits = (-Target_Rpm * 4.0, Target_Rpm * 4.0)   # 设置输出限幅

def calculate_pid(current_z):
    global duty_init, Target_Rpm, previous_z, RPM_NOW
    # 根据 current_z 重置 Target_Rpm
    if current_z ==0 or current_z == 0.4:  # z 不变，转数为 500
        Target_Rpm = 250
    else:
        if previous_z < current_z:  # z > 前一个 z 值，说明上坡
            Target_Rpm = 325
            print("target=",Target_Rpm)  # 打印目标转速
        else:  # 否则下坡
            Target_Rpm = 50
            print("target=",Target_Rpm)

    print("Target_Rpm set to:", Target_Rpm)
    previous_z = current_z  # 更新 previous_z
    RPM_ERR = abs(RPM_NOW) - Target_Rpm  # 计算实际转速与目标转速的误差
    RPM_PID = pid(RPM_ERR) + RPM_NOW  # PID 控制
    duty_init = RPM_PID / 8250 + 0.02546  # 将 PID 控制的转速转换为修正后的占空比
    print ("duty_init=",duty_init)
def sub_read_rpm(rpm_now):
    global RPM_NOW
    if isinstance(rpm_now, Int32):
        RPM_NOW = rpm_now.data
        calculate_pid(current_z)  # 使用当前的 current_z
        pub_duty.publish(duty_init) 
    else:
        print("Unexpected message type received.")

def sub_read_xy(msg):
    global current_x, current_y, current_z
    xy_current_str = msg.data
    print("Received message:", xy_current_str)

    # 正则表达式提取数值
    values = xy_current_str.strip('()').split(',')
    print("values:", values)
    try:
        current_x = float(values[0].strip())
        current_y = float(values[1].strip())
        # 直接提取当前 z 的值
        if len(values) > 2:
            current_z = float(values[2].strip())
            calculate_pid(current_z)  # 计算 PID
        else:
            print("未找到 z 值。")
    except (IndexError, ValueError) as e:
        print("转化失败！", e)

if __name__ == "__main__":
    rospy.init_node("PID")  # 初始化 ROS 节点
    rospy.Subscriber("/motor_code_rpm", Int32, sub_read_rpm, queue_size=10)  # 订阅 /motor_code_rpm 话题
    rospy.Subscriber("/xy_current", String, sub_read_xy, queue_size=10)      # 订阅 /xy_current 话题
    pub_duty = rospy.Publisher("/motor_write_duty", Float64, queue_size=10)  # 发布 /motor_write_duty 话题
    while not rospy.is_shutdown():
        pub_duty.publish(duty_init)  # 发布初始占空比
        rospy.sleep(0.1)  # 控制发布频率，避免过于频繁
    rospy.spin()

    from sklearn.metrics import classification_report
 
    y_pred = model.predict(X_test)
    y_pred_classes = np.argmax(y_pred, axis=1)
    print(classification_report(y_test_bin, y_pred_classes, target_names=label_binarizer.classes_))




    model = myModel()
    print(model.summary())
    history = model.fit(X_train, y_train, batch_size=batch_size_val, epochs=epochs_val, validation_data=(X_validation,y_validation))


    #AUGMENTATAION OF IMAGES: TO MAKEIT MORE GENERIC
    dataGen= ImageDataGenerator(width_shift_range=0.1,   # 0.1 = 10%     IF MORE THAN 1 E.G 10 THEN IT REFFERS TO NO. OF  PIXELS EG 10 PIXELS
                            height_shift_range=0.1,
                            zoom_range=0.2,  # 0.2 MEANS CAN GO FROM 0.8 TO 1.2
                            shear_range=0.1,  # MAGNITUDE OF SHEAR ANGLE
                            rotation_range=10)  # DEGREES
    dataGen.fit(X_train)
    batches= dataGen.flow(X_train,y_train,batch_size=20)  # REQUESTING DATA GENRATOR TO GENERATE IMAGES  BATCH SIZE = NO. OF IMAGES CREAED EACH TIME ITS CALLED
    X_batch,y_batch = next(batches)