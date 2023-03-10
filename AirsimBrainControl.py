import airsim
from threading import Thread
import numpy as np
import socket
import cv2
# import plotly.express as px
# import pandas as pd
import keyboard
import os


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


class AsyBrainControlCenter:
    def __init__(self,port,IP="127.0.0.1"):
        self.airsim_client = None
        self.right_left_v = 0
        self.for_back_v = 0
        self.up_down_v = 0
        self.yaw_v = 0
        self.isfly = False
        self.send_rc_control = False
        self.speed_add = 10
        self.AirsimIP = IP
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((IP,port))
        self.FlyPath = []
        self.SpeedVectors = np.array([0,0,0,0])  # for_back、left_righ、down_uo、yaw
        self.DronSpeed = np.array([0,0,0,0])

    def SpeedVectorUpdata(self, index):
        '''
        更新无人机的速度向量
        :param index:
        :return:
        '''
        for i in range(4):
            if i == index:
                if self.SpeedVectors[index] == 4:
                    self.SpeedVectors[index] = 4
                else:
                    self.SpeedVectors[index] += 1

            else:
                if self.SpeedVectors[i] == 0:
                    self.SpeedVectors[i] = 0
                else:
                    self.SpeedVectors[i] -= 1


    def connect_airsim(self):
        '''
        建立与Airsim客户端的连接
        :return:
        '''
        self.airsim_client = airsim.MultirotorClient(self.AirsimIP)
        self.airsim_client.confirmConnection()


    def SpeedUpdata(self, command):
        '''
        速度控制:
        ["Right", "CW", "TakeOff", "Forward", "Up", "CCW", "Left", "Down", "Back", "Land" ]
        [  0        1      2           3        4     5      6       7       8       9    ]
        :return:
        '''
        # 前后移动
        if command == str(b'3'):
            self.SpeedVectorUpdata(0)
            self.DronSpeed = self.SpeedVectors*self.speed_add
            self.set_speed(self.DronSpeed)

        elif command == str(b'8'):
            self.SpeedVectorUpdata(0)
            self.DronSpeed = self.SpeedVectors*(-self.speed_add)
            self.set_speed(self.DronSpeed)

        # 左右旋转移动
        elif command == str(b'0'):
            self.SpeedVectorUpdata(3)
            self.DronSpeed = self.SpeedVectors*self.speed_add
            self.set_speed(self.DronSpeed)

        elif command == str(b'6'):
            self.SpeedVectorUpdata(3)
            self.DronSpeed = self.SpeedVectors*(-self.speed_add)
            self.set_speed(self.DronSpeed)

        # 上下移动
        elif command == str(b'4'):
            self.SpeedVectorUpdata(2)
            self.DronSpeed = self.SpeedVectors*(-self.speed_add)
            self.set_speed(self.DronSpeed)

        elif command == str(b'7'):
            self.SpeedVectorUpdata(2)
            self.DronSpeed = self.SpeedVectors*(self.speed_add)
            self.set_speed(self.DronSpeed)

        # 左右移动
        elif command == str(b'1'):
            self.SpeedVectorUpdata(1)
            self.DronSpeed = self.SpeedVectors*self.speed_add
            self.set_speed(self.DronSpeed)

        elif command == str(b'5'):
            self.SpeedVectorUpdata(1)
            self.DronSpeed = self.SpeedVectors*(-self.speed_add)
            self.set_speed(self.DronSpeed)

        elif command == str(b'10'):
            if self.SpeedVectors[0] == 4 or self.SpeedVectors[1] == 4 or self.SpeedVectors[2] == 4 or self.SpeedVectors[3] == 4:
                self.set_speed(self.DronSpeed)
                self.send_feedback(self.DronSpeed)  # 如果保持原速，就出现反馈
            else:
                self.airsim_client.hoverAsync()


    def send_feedback(self, DronSpeed):
        if DronSpeed[0] == 4*self.speed_add:
            command = '3'
        elif DronSpeed[0] == -4*self.speed_add:
            command = '8'
        
        elif DronSpeed[1] == 4*self.speed_add:
            command = '1'
        elif DronSpeed[1] == -4*self.speed_add:
            command = '5'
        
        elif DronSpeed[2] == 4*self.speed_add:
            command = '7'
        elif DronSpeed[2] == 4*self.speed_add:
            command = '4'

        elif DronSpeed[3] == 4*self.speed_add:
            command = '0'
        elif DronSpeed[3] == 4*self.speed_add:
            command = '6'
        
        self.client_socket.sendto(bytes(command, "utf8"),(self.AirsimIP, 7830))
        
            

    def set_speed(self,DronSpeed):
        self.for_back_v = DronSpeed[0]/100
        self.right_left_v = DronSpeed[1]/100
        self.up_down_v = DronSpeed[2]/100
        self.yaw_v = (DronSpeed[3]/100)*10
        self.airsim_client.moveByVelocityBodyFrameAsync(self.for_back_v, self.right_left_v, self.up_down_v, duration = 0.5, yaw_mode = airsim.YawMode(is_rate = True, yaw_or_rate = self.yaw_v))


    def updata(self):
        '''
        向Airsim发送速度控制向量
        :return:
        '''
        recvData, Add = self.socket.recvfrom(1024)
        command = str(recvData)
        # 起飞按键
        if command == str(b'2'):
            if self.isfly == False:
                self.airsim_client.enableApiControl(True)       # 获取控制权
                self.airsim_client.armDisarm(True)              # 解锁
                self.airsim_client.takeoffAsync().join()
                self.airsim_client.moveToZAsync(-3.3, 1).join()
                self.isfly = True
                self.send_rc_control = True
                print('You are controling now!')
        # 降落按键
        elif command == str(b'9'):
            self.airsim_client.hoverAsync()

        if self.send_rc_control:
            self.SpeedUpdata(command)
            state = self.airsim_client.getMultirotorState().kinematics_estimated
            x_position = np.round(-state.position.x_val, 3)
            y_position = np.round(-state.position.y_val, 3)
            z_position = np.round(-state.position.z_val, 3)
            self.FlyPath.append([x_position,y_position,z_position])
            print('x:{}, y:{}, z:{}'.format(x_position, y_position, z_position))




class SynBrainControlCenter:
    def __init__(self,port,IP="127.0.0.1"):
        self.airsim_client = None
        self.right_left_v = 0
        self.for_back_v = 0
        self.up_down_v = 0
        self.yaw_v = 0
        self.isfly = False
        self.send_rc_control = False
        self.speed_add = 10
        self.AirsimIP = IP
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((IP,port))
        self.FlyPath = []
        self.SpeedVectors = np.array([0,0,0,0])  # for_back、left_righ、down_uo、yaw
        self.DronSpeed = np.array([0,0,0,0])

    def SpeedVectorUpdata(self, index):
        '''
        更新无人机的速度向量
        :param index:
        :return:
        '''
        for i in range(4):
            if i == index:
                if self.SpeedVectors[index] == 4:
                    self.SpeedVectors[index] = 4
                else:
                    self.SpeedVectors[index] += 1

            else:
                if self.SpeedVectors[i] == 0:
                    self.SpeedVectors[i] = 0
                else:
                    self.SpeedVectors[i] -= 1


    def connect_airsim(self):
        '''
        建立与Airsim客户端的连接
        :return:
        '''
        self.airsim_client = airsim.MultirotorClient(self.AirsimIP)
        self.airsim_client.confirmConnection()


    def SpeedUpdata(self, command):
        '''
        速度控制:
        ["Right", "CW", "TakeOff", "Forward", "Up", "CCW", "Left", "Down", "Back", "Land" ]
        [  0        1      2           3        4     5      6       7       8       9    ]
        :return:
        '''
        # 前后移动
        if command == str(b'3'):
            self.SpeedVectorUpdata(0)
            self.DronSpeed = self.SpeedVectors*self.speed_add
            self.set_speed(self.DronSpeed)

        elif command == str(b'8'):
            self.SpeedVectorUpdata(0)
            self.DronSpeed = self.SpeedVectors*(-self.speed_add)
            self.set_speed(self.DronSpeed)

        # 左右旋转移动
        elif command == str(b'0'):
            self.SpeedVectorUpdata(3)
            self.DronSpeed = self.SpeedVectors*self.speed_add
            self.set_speed(self.DronSpeed)

        elif command == str(b'6'):
            self.SpeedVectorUpdata(3)
            self.DronSpeed = self.SpeedVectors*(-self.speed_add)
            self.set_speed(self.DronSpeed)

        # 上下移动
        elif command == str(b'4'):
            self.SpeedVectorUpdata(2)
            self.DronSpeed = self.SpeedVectors*(-self.speed_add)
            self.set_speed(self.DronSpeed)

        elif command == str(b'7'):
            self.SpeedVectorUpdata(2)
            self.DronSpeed = self.SpeedVectors*(self.speed_add)
            self.set_speed(self.DronSpeed)

        # 左右移动
        elif command == str(b'1'):
            self.SpeedVectorUpdata(1)
            self.DronSpeed = self.SpeedVectors*self.speed_add
            self.set_speed(self.DronSpeed)

        elif command == str(b'5'):
            self.SpeedVectorUpdata(1)
            self.DronSpeed = self.SpeedVectors*(-self.speed_add)
            self.set_speed(self.DronSpeed)


    def set_speed(self,DronSpeed):
        self.for_back_v = DronSpeed[0]/100
        self.right_left_v = DronSpeed[1]/100
        self.up_down_v = DronSpeed[2]/100
        self.yaw_v = (DronSpeed[3]/100)*10
        self.airsim_client.moveByVelocityBodyFrameAsync(self.for_back_v, self.right_left_v, self.up_down_v, duration = 0.5, yaw_mode = airsim.YawMode(is_rate = True, yaw_or_rate = self.yaw_v))


    def updata(self):
        '''
        向Airsim发送速度控制向量
        :return:
        '''
        recvData, Add = self.socket.recvfrom(1024)
        command = str(recvData)
        # 起飞按键
        if command == str(b'2'):
            if self.isfly == False:
                self.airsim_client.enableApiControl(True)       # 获取控制权
                self.airsim_client.armDisarm(True)              # 解锁
                self.airsim_client.takeoffAsync().join()
                self.airsim_client.moveToZAsync(-3.43, 1).join()
                self.isfly = True
                self.send_rc_control = True
                print('You are controling now!')
        # 降落按键
        elif command == str(b'9'):
            self.airsim_client.hoverAsync()

        if self.send_rc_control:
            self.SpeedUpdata(command)
            state = self.airsim_client.getMultirotorState().kinematics_estimated
            x_position = np.round(-state.position.x_val, 3)
            y_position = np.round(-state.position.y_val, 3)
            z_position = np.round(-state.position.z_val, 3)
            self.FlyPath.append([x_position,y_position,z_position])
            print('x:{}, y:{}, z:{}'.format(x_position, y_position, z_position))


if __name__ == '__main__':
    subject = 'wyl'
    runloop = 'Asy_01'

    filename = subject+ '_' + runloop
    if os.path.exists('./data/' + filename) == False:
        os.makedirs('./data/' + filename)

    IP = "192.168.56.3"
    GetAirsimVideo = AirsimVideo(IP)
    GetAirsimVideo.setDaemon(True)
    GetAirsimVideo.start()

    brain_control_dron = AsyBrainControlCenter(7820, IP)
    brain_control_dron.connect_airsim()
    while True:
        brain_control_dron.updata()
        if keyboard.is_pressed('esc'):
            np.save('./data/' + filename+'/PathData.npy', brain_control_dron.FlyPath)
            break







