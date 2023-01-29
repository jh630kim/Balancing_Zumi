# 세개의 창에 세개의 그래프를 그리기
import matplotlib.pyplot as plt
import random
from matplotlib.animation import FuncAnimation
import numpy as np
from zumi.zumi import Zumi

MAX_X = 10

zumi = Zumi()

###############
# step 0.
###############
# 초기값 선언
lst = [np.zeros(MAX_X),np.zeros(MAX_X),np.zeros(MAX_X)]          # 100개의 Zero 값
t = np.linspace(0,1,MAX_X)   # 0~1까지 100단계로 나눔

###############
# step 1.
# https://cosmosproject.tistory.com/431
###############
# fig = 그래프의 설정(plt.figure) 관련 정보
# 다수의 그래프를 그림
# fig는 전체, axes는 각각의 화면을 의미
fig, axes = plt.subplots(nrows=3, ncols=1)

# 초기 그래프 그리기
# line 객체의 첫번째... ln = plt.plot(t,lst,'r')[0]과 같은 의미임
# ln, = plt.plot(t,list,'r')과 같은 의미임
ln = [axes[0].plot(t, lst[0], 'r')[0],
      axes[1].plot(t, lst[1], 'r')[0],
      axes[2].plot(t, lst[2], 'r')[0]]

# 그래프의 최대 최소값
# plt.xlim(0,100)   # x값은 t로 정해진다.
# subplots의 axes의 경우 ylim 대신 set_ylim을 사용
axes[0].set_ylim(-180, 180)
axes[1].set_ylim(-180, 180)
axes[2].set_ylim(-180, 180)

# step 2.
# func = 좌표를 1개씩 update할 때 마다 그래프를 update하기 위해 사용할 함수
# i에는 t(=frames)의 값이 순차적으로 하나씩 전달되며,
# t(=frame)와 ln(위에서 선언한 그리기 객체)도 함께 전달되어
# 반복 호출된다.
def update(index):
    global lst  # 함수 외부에서 선언한 변수

    ##################
    # 새로운 값 읽기
    ##################
    # acc = zumi.get_gyro()
    acc = zumi.update_angles()
    new_val = [acc[5], acc[6], acc[5]]

    for i in range(0,3):
        # List에 값 추가
        lst[i] = np.append(lst[i], new_val[i])
        lst[i] = np.delete(lst[i], 0)

        # Line Update
        ln[i].set_data(t, lst[i])

    # 참고로, blit가 True인 경우만 Return값이 필요하다.
    return ln[0], ln[1], ln[2]

# step 3. frame = 2번의 func 함수가 실행될 때 마다 2번의 func 함수의 argument로서 전달할 값의 list
ani = FuncAnimation(fig=fig, func=update, frames=t, blit=True)

plt.show()
