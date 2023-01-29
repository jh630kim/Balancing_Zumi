# 한개의 창에 두개의 그래프를 그리기
# raw 센서값과 LPF를 통과한 센서값
# LPF는 수정 필요
# https://gaussian37.github.io/autodrive-ose-low_pass_filter/

import matplotlib.pyplot as plt
import random
from matplotlib.animation import FuncAnimation
import numpy as np
from zumi.zumi import Zumi

data_len = 100
sampling_len = 10
alpha = 0.5

def LPF(acc_xf_lst, sampling_len, alpha, acc_x):
    # 이동평균필터와 1차 LPF의 혼종
    # prevX = acc_xf_lst[len(acc_xf_lst)-sampling_len:len(acc_xf_lst)-1].sum()/sampling_len
    # prevX = acc_xf_lst[len(acc_xf_lst) - sampling_len:].sum() / sampling_len # 마지막까지면... 이렇게 해야 하는데?

    # 1차 LPF: https://gaussian37.github.io/autodrive-ose-low_pass_filter/
    prevX = acc_xf_lst[-1]
    acc_xf = alpha * prevX + (1-alpha)*acc_x
    return acc_xf

zumi = Zumi()

###############
# step 0.
###############
# 초기값 선언
acc_x_lst = np.zeros(data_len)
acc_xf_lst = np.zeros(data_len)
t = np.linspace(0, 1, data_len)   # 0~1까지 100단계로 나눔

###############
# step 1.
# https://cosmosproject.tistory.com/431
###############
# fig = 그래프의 설정(plt.figure) 관련 정보
# 다수의 그래프를 그림
# fig는 전체, axes는 각각의 화면을 의미
fig, axes = plt.subplots(nrows=1, ncols=1)

# 초기 그래프 그리기
# line 객체의 첫번째... ln = plt.plot(t,lst,'r')[0]과 같은 의미임
# ln, = plt.plot(t,list,'r')과 같은 의미임
#ln0 = axes[0].plot(t, acc_x_lst, 'r')[0]
#ln1 = axes[0].plot(t, acc_xf_lst, 'b')[0]
ln0 = axes.plot(t, acc_x_lst, 'r')[0]
ln1 = axes.plot(t, acc_xf_lst, 'b')[0]

axes.grid(True)
#axes[1].grid(True)

# 그래프의 최대 최소값
# plt.xlim(0,100)   # x값은 t로 정해진다.
# subplots의 axes의 경우 ylim 대신 set_ylim을 사용
axes.set_ylim(-0.5, 0.5)
#axes[1].set_ylim(-3, 3)

# step 2.
# func = 좌표를 1개씩 update할 때 마다 그래프를 update하기 위해 사용할 함수
# i에는 t(=frames)의 값이 순차적으로 하나씩 전달되며,
# t(=frame)와 ln(위에서 선언한 그리기 객체)도 함께 전달되어
# 반복 호출된다.
def update(index):
    global acc_x_lst, acc_xf_lst  # 함수 외부에서 선언한 변수

    ##################
    # 새로운 값 읽기
    ##################
    acc = zumi.get_all_mpu_data()
    acc_x = acc[0]

    acc_x_lst = np.append(acc_x_lst, acc_x)
    acc_x_lst = np.delete(acc_x_lst, 0)

    acc_xf = LPF(acc_xf_lst, sampling_len, alpha, acc_x)
    acc_xf_lst = np.append(acc_xf_lst, acc_xf)
    acc_xf_lst = np.delete(acc_xf_lst, 0)

    # Line Update
    ln0.set_data(t, acc_x_lst)
    ln1.set_data(t, acc_xf_lst)

    # 참고로, blit가 True인 경우만 Return값이 필요하다.
    return ln0, ln1

# step 3. frame = 2번의 func 함수가 실행될 때 마다 2번의 func 함수의 argument로서 전달할 값의 list
ani = FuncAnimation(fig=fig, func=update, frames=t, blit=True)

plt.show()
