import airsim
from threading import Thread
import numpy as np
import keyboard
import time
import socket
import cv2
import plotly.express as px
import pandas as pd


class AirsimControlKeyBoard():
    def __init__(self,IP="127.0.0.1"):
        self.airsim_client = None
        self.right_left_v = 0
        self.for_back_v = 0
        self.up_down_v = 0
        self.yaw_v = 0
        self.isfly = False
        self.maxVelocity = 1
        self.send_rc_control = False
        self.speed_add = 0.25
        self.AirsimIP = IP
        self.FlyPath = []

    def draw_figure(self, df):
        df = np.array(df)
        plot ={'x':[],'y':[],'z':[],'path':'dron'}
        plot_UE4 = {'x':[0, 0, 0, 0, 0, 0, 16, 17.29, 17.29, 17.29],
                    'y':[0, 17.1, 17.1, 34.195, 34.195, 59.09, 59.09, 59.09, 59.09, 31.725],
                    'z':[2.5, 2.5, 4.5, 4.5, 2.5, 2.5, 2.5, 2.5, 5.5, 5.5],'path':'Origin'}
        plot['x'] = df[:,0]
        plot['y'] = df[:,1]
        plot['z'] = df[:,2]

        df1 = pd.DataFrame(plot_UE4)
        df2 = pd.DataFrame(plot)
        DataFrame = pd.concat ([df1,df2],axis=0,ignore_index=True)
        fig = px.line_3d(DataFrame, x="x", y="y", z="z",color='path')
        fig.show()
 

    def connect_airsim(self):
        '''
        建立与Airsim客户端的连接
        :return:
        '''
        self.airsim_client = airsim.MultirotorClient(self.AirsimIP)
        self.airsim_client.confirmConnection()


    def keydownFunc(self,x):
        '''
        按键控制无人机飞行
        :return:
        '''
        w = keyboard.KeyboardEvent('down', 28, 'w')             # 前进
        s = keyboard.KeyboardEvent('down', 28, 's')             # 后退
        a = keyboard.KeyboardEvent('down', 28, 'a')             # 左移
        d = keyboard.KeyboardEvent('down', 28, 'd')             # 右移
        up = keyboard.KeyboardEvent('down', 28, 'up')           # 上升
        down = keyboard.KeyboardEvent('down', 28, 'down')       # 下降
        left = keyboard.KeyboardEvent('down', 28, 'left')       # 左转
        right = keyboard.KeyboardEvent('down', 28, 'right')     # 右转
        t = keyboard.KeyboardEvent('down', 28, 't')             # 起飞获取控制
        l = keyboard.KeyboardEvent('down', 28, 'l')             # 降落释放控制
        r= keyboard.KeyboardEvent('down', 28, 'r')              # 保持坐标数据

        if x.event_type == 'down' and x.name == r.name:
            np.save('path',self.FlyPath)


        # 起飞按键
        if x.event_type == 'down' and x.name == t.name and self.isfly == False:
            self.airsim_client.enableApiControl(True)       # 获取控制权
            self.airsim_client.armDisarm(True)              # 解锁
            self.airsim_client.takeoffAsync().join()
            self.airsim_client.moveToZAsync(-3.42, 1).join()
            self.isfly = True
            self.send_rc_control = True
            print('You are controling now!')
        # 降落按键
        elif x.event_type == 'down' and x.name == l.name and self.isfly == True:
            self.airsim_client.landAsync().join()
            self.isfly = False
            self.send_rc_control = False
            self.airsim_client.armDisarm(False)   # 上锁
            self.airsim_client.enableApiControl(False)
            # self.draw_figure(self.FlyPath)
            print('I am landing')

        # 前后移动
        elif x.event_type == 'down' and x.name == w.name :
            self.for_back_v = self.for_back_v + self.speed_add
            if self.for_back_v > self.maxVelocity:
                self.for_back_v = self.maxVelocity

        elif x.event_type == 'down' and x.name == s.name :
            self.for_back_v = self.for_back_v - self.speed_add
            if self.for_back_v < -self.maxVelocity:
                self.for_back_v = -self.maxVelocity

        # 左右移动
        elif x.event_type == 'down' and x.name == right.name :
            # self.yaw_v = self.right_left_v + self.speed_add
            # if self.yaw_v > self.maxVelocity:
            #     self.yaw_v = self.maxVelocity
            self.yaw_v = 15

        elif x.event_type == 'down' and x.name == left.name :
            # self.yaw_v = self.yaw_v - self.speed_add
            # if self.yaw_v < -self.maxVelocity:
            #     self.yaw_v = -self.maxVelocity
            self.yaw_v = -15

        # 上下移动
        elif x.event_type == 'down' and x.name == up.name:
            self.up_down_v = self.up_down_v - self.speed_add
            if self.up_down_v < -self.maxVelocity:
                self.up_down_v = -self.maxVelocity

        elif x.event_type == 'down' and x.name == down.name:
            self.up_down_v = self.up_down_v + self.speed_add
            if self.up_down_v > self.maxVelocity:
                self.up_down_v = self.maxVelocity

        # 左右旋转移动
        elif x.event_type == 'down' and x.name == d.name :
            self.right_left_v = self.right_left_v + self.speed_add
            if self.right_left_v > self.maxVelocity:
                self.right_left_v = self.maxVelocity
          

        elif x.event_type == 'down' and x.name == a.name :
            self.right_left_v = self.right_left_v - self.speed_add
            if self.right_left_v < -self.maxVelocity:
                self.right_left_v = -self.maxVelocity
           

        else:
            self.right_left_v = 0
            self.for_back_v = 0
            self.up_down_v = 0
            self.yaw_v = 0
        self.updata()


    def updata(self):
        '''
        向Airsim发送速度控制向量
        :return:
        '''
        if self.send_rc_control:
            self.airsim_client.moveByVelocityBodyFrameAsync(self.for_back_v, self.right_left_v, self.up_down_v, duration = 0.5, yaw_mode = airsim.YawMode(is_rate = True, yaw_or_rate = self.yaw_v))
            state = self.airsim_client.getMultirotorState().kinematics_estimated
            x_position = np.round(-state.position.x_val, 3)
            y_position = np.round(-state.position.y_val, 3)
            z_position = np.round(-state.position.z_val, 3)
            self.FlyPath.append([x_position,y_position,z_position])
            print('x:{}, y:{}, z:{}'.format(x_position, y_position, z_position))



class AirsimVideo(Thread):
    def __init__(self,IP):
        Thread.__init__(self)
        self.AirsimClient = airsim.MultirotorClient(IP)
        self.AirsimClient.confirmConnection()
        self.AirsimClient.enableApiControl(True)       # 获取控制权
        self.AirsimClient.armDisarm(True)              # 解锁

    def run(self):
        while True:
            try:
                png_image = self.AirsimClient.simGetImages([airsim.ImageRequest("front_center",airsim.ImageType.Scene,False,False)])
                image = png_image[0]
                imgld = np.frombuffer(image.image_data_uint8,dtype=np.uint8) #get numpy array
                img_rgb = imgld.reshape(image.height, image.width, 3)        #reshape array to 3 channel image array H X W X 3
                cv2.imshow('img_rgb',img_rgb)
                if cv2.waitKey(10) & 0xFF == ord('q'):
                    break
            except:
                continue



if __name__ == '__main__':
    IP = "192.168.56.3"
    GetAirsimVideo = AirsimVideo(IP)
    GetAirsimVideo.setDaemon(True)
    GetAirsimVideo.start()

    keyboard_control_dron = AirsimControlKeyBoard(IP)
    keyboard_control_dron.connect_airsim()
    keyboard.hook(keyboard_control_dron.keydownFunc)
    keyboard.wait()








