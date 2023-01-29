from zumi.zumi import Zumi
import time

zumi = Zumi()
# drive PID values; used in forward(),go_straight() etc
D_P = 2.9
D_I = 0.01
D_D = 0.05

# turn PID values; used in turn()
T_P = 0.6
T_I = 0.001
T_D = 0.001

max_speed = 127
# 8815: left = 20, whn right = 10
# 8815: left = 127 when right = 110
# 직진을 위해 이런 코드를 이용한다.
# def drive_at_angle(self, max_speed, base_speed, desired_angle, k_p, k_d, k_i, min_error):

zumi.control_motors(left = 127, right = 110, acceleration=0)
# zumi.drive_at_angle(max_speed=127, base_speed=50, desired_angle=0, k_p=D_P, k_d=D_D, k_i=D_I, min_error=1)
# zumi.forward(110,5)
time.sleep(1)
zumi.control_motors(left = -127, right = -110, acceleration=0)
time.sleep(1)
zumi.stop()
