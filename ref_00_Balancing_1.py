# -*- coding: utf-8 -*-

"""
# python3 -m _00_Balancing r
# 참고: http://scipia.co.kr/cms/blog/227
# 아두이노 코드를 라즈베리파이의 python 코드로 수정
# PID는 아래 코드 이용
# https://pypi.org/project/simple-pid/

# Zumi용 코드로 수정
"""

import _10_L298_RPi as L298
from _21_MPU_Thread import Angle_MPU6050
# Sensor_Visualizer_v2를 이용해 Display하고 싶으면 이걸 이용
# import _41_LAN_Comm as rec
# 단순히 파일로 기록하고 싶으면 이걸 이용
import _41_FILE_record as rec

import math
import time
import sys
import datetime

from zumi.zumi import Zumi
from simple_pid import PID

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

# zumi = Zumi()

########################################
# 설정값을 인수로 받기
########################################
# Config파일에서 PID 설정값 읽기
file = open("_01_config.py", 'r')
Default_SP = float(file.readline().split("=")[1])       # 로봇이 지면에서 평형을 유지하는 상태의 값
Default_Kp = float(file.readline().split("=")[1])             # P gain, 1단계 설정
Default_Ki = float(file.readline().split("=")[1])            # I gain, 3단계 설정
Default_Kd = float(file.readline().split("=")[1])            # D gain, 2단계 설정
run = int(file.readline().split("=")[1])            # 모터 구동 여부
logging = int(file.readline().split("=")[1])        # data logging 여부
bluetooth = int(file.readline().split("=")[1])
file.close()

# 파일 실행 인자로 설정값 받기
try:
    # if str(type(sys.argv[1])) != "<class 'str'>":
    if sys.argv[1] != '-' and sys.argv[1] != 'r':
        Default_SP = float(sys.argv[1])
except IndexError:
    print("Set (1)setpoint, (1)Kp, (3)Ki, (4)Kd, (5)motor_run[1], (6)logging[0] status!")
    print("('-' for not changing)")
    print("Or, Use [_00_Balancing.py r] for defalut setting")
    exit()

# 인자로 - 를 받으면 default값 이용
try:
    if sys.argv[2] != '-':
        Default_Kp = float(sys.argv[2])
    if sys.argv[3] != '-':
        Default_Ki = float(sys.argv[3])
    if sys.argv[4] != '-':
        Default_Kd = float(sys.argv[4])
    if sys.argv[5] != '-':
        run = int(sys.argv[5])
    if sys.argv[6] != '-':
        logging = int(sys.argv[6])
    if sys.argv[6] != '-':
        bluetooth = int(sys.argv[7])
except IndexError:
    pass

# Config파일에 PID 설정값 쓰기
file = open("_01_config.py", 'w')
file.write("# set_point                 = {}\n".format(Default_SP))
file.write("# P gain                    = {}\n".format(Default_Kp))
file.write("# I gain                    = {}\n".format(Default_Ki))
file.write("# D gain                    = {}\n".format(Default_Kd))
file.write("# motor ON(1)/OFF(0)        = {}\n".format(run))
file.write("# Data logging ON(1)/OFF(0) = {}\n".format(logging))
file.write("# BT connection ON(1)/OFF(0)= {}\n".format(bluetooth))
file.close()

########################################
# PID 초기화
########################################
# 기타 설정값
setpoint_adj = 0
# todo: Sampling Time 조절, zippy 코드를 보니 5ms 이내로 하라고 한다.
#       가장 마지막의 time.sleep()도 조정 필요
sample_time = 0.01  # 주기: 0.05 sec
output_limits = (-99, 99)   # 출력 제한: -100 ~ 100
auto_mode = True    # PID control ON(True), Off(False)
p_ON_M = False      # 뭐지?

# PID 제어기 선언
# todo: Zumi에도 PID 제어기가 있는 것 같다.
pid = PID(Kp=Default_Kp, Ki=Default_Ki, Kd=Default_Kd,
          setpoint=Default_SP,
          sample_time=sample_time,
          output_limits=output_limits,
          auto_mode=auto_mode,
          proportional_on_measurement=p_ON_M)
# 참고: 설정값 변경 예
# pid.setpoint = 10
# pid.tunings = (1.0, 0,2, 0.4) = (Kp, Ki, Kd) or pid.Kp = 1.0

# PID 설정값 Logging
dt = datetime.datetime.now()
dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.microsecond

file_name = './_01_run_setting_log.txt'
file=open(file_name, 'a')
file.write('{}/{} {}:{} {} {} {} {} {}\n'.format(
    dt.month, dt.day, dt.hour, dt.minute, Default_SP, Default_Kp, Default_Ki, Default_Kd, sample_time))
file.close()

########################################
# MOU-6050 초기화
########################################
# Sensor initialization
# todo: Zumi용으로 수정 필요
mpu6050 = Angle_MPU6050()
mpu6050.start_measure_thread()


########################################
# L298(모터) 초기화
########################################
# todo: Zumi용으로 수정 필요
# L298.GPIO_init()

########################################
# Logging 준비
########################################
# 전송 센서 정보
if logging == 1:
    # 파일 저장시에는 sensor name만 사용된다.
    # channel, sensor_min, sensor max는 실시간 LAN 통신때만 사용한다.
    # sensor_name = ["Kalman_Y", "SetPoint", "MOTOR", "ACCEL_Y",
    #               "Gyro_yaw", "DMP_Y", "ADJ"]
    sensor_name = ["zumi_y_acc", ",",
                   "zumi_y_gyro", ",",
                   "zumi_y_angle", ",",
                   "accel_pitch", ",",
                   "gyro_pitch", ",",
                   "zumi_y_angle"]
    channel = len(sensor_name)

    # Data 메시지 준비
    msg = 'value'
    data = []
    value = ''
    sensor_min = []
    sensor_max = []

    for i in range(channel):
        value += '{} '
        sensor_min.append(-180)
        sensor_max.append(180)
    sensor_min[0] = -30
    sensor_max[0] = 30
    sensor_min[1] = -5
    sensor_max[1] = 0
    sensor_min[3] = -100
    sensor_max[3] = 100

    # Clinet 초기화
    rec.initialize(channel, sensor_name, sensor_min, sensor_max)

########################################
# 제어 루프 시작
########################################
print("SP = {}, Kp = {}, Ki = {}, Kd = {}, Run = {}, Log = {}"
      .format(Default_SP, Default_Kp, Default_Ki, Default_Kd, run, logging))

for i in range(3, 0, -1):
    print(i, "!")
    time.sleep(1)

print("Start!!!")

# 초기값 설정
count = 0           # display 주기
past = time.time()  # 현재 시간(Loop time 확인용)

##################################
# 정지상태의 Gyro 센서 보정
##################################
# todo: 크게 중요하지 않아 보인다.
#       나중에 밸런싱이 잘 맞으면 그때 생각하자.
#       지금은 약 -0.006, 0.02 deg로 보이는데... 짧은 시간에는 영향 없다.
'''
gyro_pitch_sum = 0
gyro_yaw_sum = 0
for i in range(500):
    gyro_pitch_sum += mpu6050.get_gyro_pitch()
    gyro_yaw_sum += mpu6050.get_gyro_yaw()
    time.sleep(0.005)

gyro_pitch_cal = gyro_pitch_sum/500
gyro_yaw_cal = gyro_yaw_sum/500
'''

# 현재 PID 계수 및 setpoint
motor_speed = 0

MAX_X = 100

###############
# step 0.
###############
# 초기값 선언
lst = [np.zeros(MAX_X),
       np.zeros(MAX_X),
       np.zeros(MAX_X)]          # 100개의 Zero 값
t = np.linspace(0,1,MAX_X)   # 0~1까지 100단계로 나눔

###############
# step 1.
# https://cosmosproject.tistory.com/431
###############
# fig = 그래프의 설정(plt.figure) 관련 정보
# 다수의 그래프를 그림
# fig는 전체, axes는 각각의 화면을 의미
fig, axes1 = plt.subplots(nrows=1, ncols=1)
axes2 = axes1.twinx()   # 첫번째 plot의 Twin
axes3 = axes1.twinx()   # 첫번째 plot의 Twin

# 초기 그래프 그리기
# line 객체의 첫번째... ln = plt.plot(t,lst,'r')[0]과 같은 의미임
# ln, = plt.plot(t,list,'r')과 같은 의미임
ln = [axes1.plot(t, lst[0], 'r')[0],
      axes2.plot(t, lst[1], 'g')[0],
      axes3.plot(t, lst[2], 'b')[0]]

# 그래프의 최대 최소값
# plt.xlim(0,100)   # x값은 t로 정해진다.
# subplots의 axes의 경우 ylim 대신 set_ylim을 사용
axes1.grid(True)
axes2.grid(True)
axes3.grid(True)

def change_ylim(axes1, axes2, axes3, lst):
    axes1.set_ylim(min(lst[0]), max(lst[0]))
    axes2.set_ylim(min(lst[1]), max(lst[1]))
    axes3.set_ylim(min(lst[2]), max(lst[2]))


axes1.set_ylim(0, 5)
axes2.set_ylim(0, 5)
axes3.set_ylim(100, 1200)

# step 2.
# func = 좌표를 1개씩 update할 때 마다 그래프를 update하기 위해 사용할 함수
# i에는 t(=frames)의 값이 순차적으로 하나씩 전달되며,
# t(=frame)와 ln(위에서 선언한 그리기 객체)도 함께 전달되어
# 반복 호출된다.
alpha = 0.3
def update(index):
    global lst  # 함수 외부에서 선언한 변수

    ##################
    # 새로운 값 읽기
    ##################
    kalman_pitch = mpu6050.get_kalman_pitch()
    accel_pitch = mpu6050.get_accel_pitch()
    raw_data = mpu6050.get_raw_data()
    prevX = lst[2][-1]
    acc_xf = alpha * prevX + (1-alpha)*raw_data[0]

    new_val = [kalman_pitch, accel_pitch, acc_xf]

    for i in range(0,3):
        # List에 값 추가
        lst[i] = np.append(lst[i], new_val[i])
        lst[i] = np.delete(lst[i], 0)

        # Line Update
        ln[i].set_data(t, lst[i])

    # change_ylim(axes1, axes2, axes3, lst)
    # 참고로, blit가 True인 경우만 Return값이 필요하다.
    return ln[0], ln[1], ln[2]

# step 3. frame = 2번의 func 함수가 실행될 때 마다 2번의 func 함수의 argument로서 전달할 값의 list
ani = FuncAnimation(fig=fig, func=update, frames=t, blit=True)

plt.show()


'''
while True:
    #################################
    # 센서 읽기
    #################################
    kalman_pitch = mpu6050.get_kalman_pitch()
    Comp_pitch = mpu6050.get_complementary_pitch()
    accel_pitch = mpu6050.get_accel_pitch()
    gyro_pitch = mpu6050.get_gyro_pitch()
    
    raw_data = mpu6050.get_raw_data()

    count += 1

    if logging == 1:
        # 메시지 생성 for logging
        data.append(value.format(zumi_x_acc, ",",
                                 zumi_x_gyro, ",",
                                 zumi_x_angle, ",",
                                 accel_pitch, ",",
                                 gyro_pitch, ",",
                                 zumi_y_angle))

        # 그래프를 그리기 위해 전송(또는 Logging)
        if count > 100:
            rec.msg_send(msg, data)
            # 메시지 전송 후 초기화
            data = []

    if count > 100:
        new = time.time()
        print("Elapsed time(for 100 tries) =", new - past)
        past = new
        count = 0

    # todo: PID에서 Sampling Rate에 따라 기다리는지 확인
    #       현재 Sampling Rate는 0.01임

    time.sleep(0.01)

# GPIO 종료
GPIO.cleanup()

# 소켓 닫기
rec.close()
'''


