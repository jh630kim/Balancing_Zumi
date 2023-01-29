# -*- coding: utf-8 -*-

"""
# python3 -m _00_Balancing r
# 참고: http://scipia.co.kr/cms/blog/227
# 아두이노 코드를 라즈베리파이의 python 코드로 수정
# PID는 아래 코드 이용
# https://pypi.org/project/simple-pid/

# Zumi용 코드로 수정
"""
import math
import time
import sys
import datetime

import _41_FILE_record as rec

from zumi.zumi import Zumi
from simple_pid import PID

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

zumi = Zumi()

########################################
# 설정값을 인수로 받기
########################################
# Config파일에서 PID 설정값 읽기
file = open("config.txt", 'r')
Default_SP = float(file.readline().split("=")[1])       # 로봇이 지면에서 평형을 유지하는 상태의 값
Default_Kp = float(file.readline().split("=")[1])       # P gain, 1단계 설정
Default_Ki = float(file.readline().split("=")[1])       # I gain, 3단계 설정
Default_Kd = float(file.readline().split("=")[1])       # D gain, 2단계 설정
run = int(file.readline().split("=")[1])                # 모터 구동 여부
logging = int(file.readline().split("=")[1])            # data logging 여부
file.close()

# 파일 실행 인자로 설정값 받기
try:
    if sys.argv[1] != '-' and sys.argv[1] != 'r':
        Default_SP = float(sys.argv[1])
except IndexError:
    print("Set (1)setpoint, (1)Kp, (3)Ki, (4)Kd, (5)motor_run[1], (6)logging[0] status!")
    print("('-' for not changing)")
    print("Or, Use [balancing.py r] for defalut setting")
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
except IndexError:
    pass

# Config파일에 PID 설정값 쓰기
file = open("config.txt", 'w')
file.write("# set_point                 = {}\n".format(Default_SP))
file.write("# P gain                    = {}\n".format(Default_Kp))
file.write("# I gain                    = {}\n".format(Default_Ki))
file.write("# D gain                    = {}\n".format(Default_Kd))
file.write("# motor ON(1)/OFF(0)        = {}\n".format(run))
file.write("# Data logging ON(1)/OFF(0) = {}\n".format(logging))
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
# Zumi에도 PID 제어기가 있는 것 같다
#  -> sensor 코드를 봤을 때 못믿겠다.
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

file_name = './run_setting_log.txt'
file=open(file_name, 'a')
file.write('{}/{} {}:{} {} {} {} {} {}\n'.format(
    dt.month, dt.day, dt.hour, dt.minute, Default_SP, Default_Kp, Default_Ki, Default_Kd, sample_time))
file.close()

########################################
# MOU-6050 초기화
########################################
# Sensor initialization
# Zumi에서 읽어올거기 때문에 불필요


########################################
# L298(모터) 초기화
########################################
# Zumi에서 읽어올거기 때문에 불필요

########################################
# Logging 준비
########################################
# 전송 센서 정보
if logging == 1:
    sensor_name = ["acc_xf", ",",
                   "motor_speed", ",",
                   "elapsed_time"]

    # Data 메시지 준비
    data = []
    value = ''
    for i in range(len(sensor_name)):
        value += '{} '

    # Clinet 초기화
    rec.initialize(sensor_name)

########################################
# 제어 루프 시작
########################################
print("SP = {}, Kp = {}, Ki = {}, Kd = {}, Run = {}, Log = {}"
      .format(Default_SP, Default_Kp, Default_Ki, Default_Kd, run, logging))

for i in range(3, 0, -1):
    print(i, "!")
    time.sleep(1)

print("Start!!!")

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

############################################################
#-----------------------------------
# 실시간 그래프 그리기 (센서값 and 모터속도)
############################################################

alpha = 0.3
prev_acc_xf = zumi.update_angles()[8]    # rot_y를 이용
time.sleep(0.01)

motor_speed = 0     # todo: 이건 뭐지?
count = 0           # display 주기
elapsed_time100 = 0
past = time.time()  # 루프 주기 체크용

# 초기값 선언
MAX_X = 100
lst = [np.zeros(MAX_X),
       np.zeros(MAX_X)]          # 100개의 Zero 값
t = np.linspace(0,1,MAX_X)   # 0~1까지 100단계로 나눔

# step 1.
# fig = 그래프의 설정(plt.figure) 관련 정보
# 다수의 그래프를 그림
# fig는 전체, axes는 각각의 화면을 의미
fig, axes1 = plt.subplots(nrows=1, ncols=1)
axes2 = axes1.twinx()   # 첫번째 plot의 Twin

# 초기 그래프 그리기
# line 객체의 첫번째... ln = plt.plot(t,lst,'r')[0]과 같은 의미임
# ln, = plt.plot(t,list,'r')과 같은 의미임
ln = [axes1.plot(t, lst[0], 'r')[0],
      axes2.plot(t, lst[1], 'g')[0]]

# 그리드 그리기
axes1.grid(True)
axes2.grid(True)

# 그래프의 최대 최소값
# plt.xlim(0,100)   # x값은 t로 정해진다.
# subplots의 axes의 경우 ylim 대신 set_ylim을 사용
def change_ylim(axes1, axes2, lst):
    axes1.set_ylim(min(lst[0]), max(lst[0]))
    axes2.set_ylim(min(lst[1]), max(lst[1]))

axes1.set_ylim(-5, 5)
axes2.set_ylim(-5, 5)


def update(index):
    global prev_acc_xf, count, elapsed_time100, past
    global data, value

    #################################
    # 센서 읽기 + 1차 LPF 적용
    #################################
    # raw_data = zumi.get_all_mpu_data()[0] * multi  # acc_x를 이용한 LPF 적용
    raw_data = zumi.update_angles()[8]  # rot_y를 이용
    acc_xf = alpha * prev_acc_xf + (1 - alpha) * raw_data
    prev_acc_xf = acc_xf

    # 현재 각도
    current_angle = acc_xf

    ##################
    # PID 제어
    ##################
    # current_angle = 현재 Y 각도(pitch)
    # motor_speed: 모터의 전/후진
    motor_speed = pid(current_angle)

    ###############
    # Data Logging
    ###############
    count += 1
    new = time.time()
    elapsed_time = new - past
    elapsed_time100 += elapsed_time
    past = new

    if logging == 1:
        # 메시지 생성 for logging
        data.append(value.format(acc_xf, ",",
                                 motor_speed, ",",
                                 elapsed_time))
        # 그래프를 그리기 위해 전송(또는 Logging)
        if count > 100:
            rec.msg_send(data)
            # 메시지 전송 후 초기화
            data = []

    lst[0] = np.append(lst[0], acc_xf)
    lst[0] = np.delete(lst[0], 0)
    lst[1] = np.append(lst[1], motor_speed)
    lst[1] = np.delete(lst[1], 0)

    # Line Update
    ln[0].set_data(t, lst[0])
    ln[1].set_data(t, lst[1])

    if count > 100:
        print("Elapsed time(for 100 tries) =", elapsed_time100)
        count = 0
        elapsed_time100 = 0

    change_ylim(axes1, axes2, lst)
    # 참고로, blit가 True인 경우만 Return값이 필요하다.
    return ln[0], ln[1]


# step 3. frame = 2번의 func 함수가 실행될 때 마다 2번의 func 함수의 argument로서 전달할 값의 list
ani = FuncAnimation(fig=fig, func=update, frames=t, blit=True)

plt.show()

############################################################
# 실시간 그래프 그리기 (센서값 and 모터속도)
#-----------------------------------
############################################################

'''
##################################
# 초기값 설정
##################################
alpha = 0.3
prev_acc_xf = zumi.update_angles()[8]    # rot_y를 이용
time.sleep(0.01)

motor_speed = 0     # todo: 이건 뭐지?
count = 0           # display 주기
elapsed_time100 = 0
past = time.time()  # 루프 주기 체크용


try:
    while True:
        #################################
        # 센서 읽기 + 1차 LPF 적용
        #################################
        # raw_data = zumi.get_all_mpu_data()[0] * multi  # acc_x를 이용한 LPF 적용
        raw_data = zumi.update_angles()[8]    # rot_y를 이용
        acc_xf = alpha * prev_acc_xf + (1 - alpha) * raw_data
        prev_acc_xf = acc_xf

        # 현재 각도
        current_angle = acc_xf

        ##################
        # PID 제어
        ##################
        # current_angle = 현재 Y 각도(pitch)
        # motor_speed: 모터의 전/후진
        motor_speed = pid(current_angle)

        # ----불필요???--------------------
        # 정지상태의 Setpoint 조정
        adj_value = 0.01      # 0.015
        if motor_speed < 0:
            setpoint_adj -= adj_value
        elif motor_speed > 0:
            setpoint_adj += adj_value
        # pid.setpoint = setpoint + setpoint_adj
        # ------------------------

        if run == 1:
            zumi.control_motors(left=motor_speed, right=motor_speed, acceleration=0)

        ###############
        # Data Logging
        ###############
        count += 1
        new = time.time()
        elapsed_time = new - past
        elapsed_time100 += elapsed_time
        past = new

        if logging == 1:
            # 메시지 생성 for logging
            data.append(value.format(acc_xf, ",",
                                     motor_speed, ",",
                                     elapsed_time))
            # 그래프를 그리기 위해 전송(또는 Logging)
            if count > 100:
                rec.msg_send(data)
                # 메시지 전송 후 초기화
                data = []

        if count > 100:
            print("Elapsed time(for 100 tries) =", elapsed_time100)
            count = 0
            elapsed_time100 = 0

        # time.sleep(0.01)  # PID Control을 10ms로 지정했기에 다시 기다릴 필요가 없다.

except KeyboardInterrupt:
    print('Caught Keyboard Interrupt')
    raise

finally:
    # always have a stop at the end of code with control motors
    print('Stop Zumi')
    zumi.stop()
'''

# 소켓 닫기
rec.close()


