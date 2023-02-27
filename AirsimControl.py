import airsim
from threading import Thread
import numpy as np
import keyboard
import time
import socket
import cv2
import plotly.express as px


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
        plot ={'x':[],'y':[],'z':[]}
        plot['x'] = df[:,0]
        plot['y'] = df[:,1]
        plot['z'] = df[:,2]
        fig = px.line_3d(plot, x="x", y="y", z="z")
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
            self.draw_figure(self.FlyPath)
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




class BrainControlCenter:
    def __init__(self,port, IP='127.0.0.1'):
        self.airsim_client = None
        self.IP = IP
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((IP,port))
        self.SpeedVectors = np.array([0,0,0,0])  # for_back、left_righ、down_uo、yaw
        self.DronSpeed = np.array([0,0,0,0])
        self.isfly = False
        self.send_rc_control = False


    def connect_airsim(self):
        '''
        建立与Airsim客户端的连接
        :return:
        '''
        self.airsim_client = airsim.MultirotorClient(self.IP)
        self.airsim_client.confirmConnection()


    def SpeedUpdata(self, command):
        '''
        速度滤波:
        ["Right", "CW", "TakeOff", "Forward", "Up", "CCW", "Left", "Down", "Back", "Land" ]
        [  0        1      2           3        4     5      6       7       8       9    ]
        :return:
        '''
        '''起飞或降落'''
        if command == str(b'2'):
            self.airsim_client.enableApiControl(True)       # 获取控制权
            self.airsim_client.armDisarm(True)
            self.airsim_client.takeoffAsync().join()
            self.isfly = True
            self.send_rc_control = True
            print('You are controling now!')

        # 降落按键
        if command == str(b'9'):
            self.airsim_client.landAsync().join()
            self.isfly = False
            self.send_rc_control = False
            self.airsim_client.armDisarm(False)   # 上锁
            self.airsim_client.enableApiControl(False)
            print('I am landing')

        '''方向控制'''
        # 速度单位为 cm/s
        # 前后控制
        if command == str(b'3'):
            self.SpeedVectorUpdata(0)
            self.DronSpeed = self.SpeedVectors*250

        elif command == str(b'8'):
            self.SpeedVectorUpdata(0)
            self.DronSpeed = self.SpeedVectors*(-250)

        # 左右控制
        elif command == str(b'0'):
            self.SpeedVectorUpdata(1)
            self.DronSpeed = self.SpeedVectors*250

        elif command == str(b'6'):
            self.SpeedVectorUpdata(1)
            self.DronSpeed = self.SpeedVectors*(-250)

        # 上下控制
        elif command == str(b'7'):
            self.SpeedVectorUpdata(2)
            self.DronSpeed = self.SpeedVectors*250

        elif command == str(b'4'):
            self.SpeedVectorUpdata(2)
            self.DronSpeed = self.SpeedVectors*(-250)

        # 旋转控制
        elif command == str(b'1'):
            self.SpeedVectorUpdata(3)
            self.DronSpeed = self.SpeedVectors*250

        elif command == str(b'5'):
            self.SpeedVectorUpdata(3)
            self.DronSpeed = self.SpeedVectors*(-250)

        elif command == str(b'10'):
            self.DronSpeed = self.DronSpeed


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


    def updata(self):
        '''
        向Airsim发送速度控制向量
        :return:
        '''
        if self.send_rc_control:
            recvData, Add = self.socket.recvfrom(1024)
            self.SpeedUpdata(str(recvData))

            self.airsim_client.moveByVelocityBodyFrameAsync(self.DronSpeed[0]/100, self.DronSpeed[1]/100, self.DronSpeed[2]/100, duration = 0.5,
                                                            yaw_mode = airsim.YawMode(is_rate = True, yaw_or_rate = (self.DronSpeed[3]/100)*20))

            # 记录无人机的飞行轨迹
            state = self.airsim_client.getMultirotorState().kinematics_estimated
            x_position = np.round(-state.position.x_val, 3)
            y_position = np.round(-state.position.y_val, 3)
            z_position = np.round(-state.position.z_val, 3)
            
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
    mode = 'keyboard'
    IP = "127.0.0.1"

    GetAirsimVideo = AirsimVideo(IP)
    GetAirsimVideo.setDaemon(True)
    GetAirsimVideo.start()


    if mode == 'keyboard':
        keyboard_control_dron = AirsimControlKeyBoard(IP)
        keyboard_control_dron.connect_airsim()
        keyboard.hook(keyboard_control_dron.keydownFunc)
        keyboard.wait()
    else:
        brain_control_dron = BrainControlCenter(7820,IP)
        brain_control_dron.connect_airsim()
        while True:
            brain_control_dron.updata()







