from psychopy import visual
from psychopy.contrib.lazy_import import ImportReplacer
from psychopy.hardware.crs.bits import event
from psychopy.logging import data
from psychopy.tools.mathtools import length
from psychopy.visual import image, rect, text, window
from psychopy import event
import json
import math
import time
import numpy as np
from pygame.constants import FULLSCREEN
import airsim
import multiprocessing
import cv2
from PIL import Image
import gc
from multiprocessing import Process, Manager
import keyboard


'''加载数据'''
presettingfile = open('interface\PreSettings_Single_tenclass.json')
settings = json.load(presettingfile)
stimulationLength = settings[u'stimulationLength'][0]
stimuliLoop = settings[u'frequence'] 
phase = settings[u'phase']
size = settings[u'squaresize'][0]
keepsize = settings[u'keepsize'][0]       
cuelen = settings[u'cuelen'][0] 
textList = settings[u'controlCommand']
textposition = settings[u'textposition']
position = settings[u'position']        
#framerate = settings[u'framerate'][0]     
framerate = 60.0                        
cueseries =settings[u'cueSeries']   
#Set the  window size
windowSquareSize = (1900,1060)
windowSquarePos = (0,0)
#Set the video window size
videoSquareSize = [1,1]           
videoSquarePos = [0,0] 

#自定义的全局变量
w = 960
h = 540
is_full_screen = False
win_w = 1920
win_h = 1080
hc = h/win_h
wc = w/win_w
choice =  1
dt = 1/framerate

# Rect_video = rect.Rect(win,pos=(0,0),size=(850*wc,450*hc),units = 'pix',fillColor=(125,125,125),colorSpace = 'rgb255')
stim_texts = []
stim_Rects = []
res_time= []
test_Rects = [] 
position_stim = [(int(0*wc),int(325*hc)),(int(-100*wc),int(-325*hc)),(int(325*wc),int(325*hc)),(int(300*wc),int(-325*hc)),(int(-525*wc),int(100*hc)),(int(525*wc),int(100*hc)),(int(525*wc),int(-100*hc)),(int(-525*wc),int(-100*hc)),(int(-325*wc),int(325*hc)),(int(0*wc),int(-125*hc)),(int(-300*wc),int(-325*hc)),(int(100*wc),int(-325*hc))]
c = {}
video_image = []

# 先和 Airsim建立连接
client = airsim.MultirotorClient("192.168.18.8")  # connect to the AirSim simulator
client.confirmConnection()


def write(stack, cam, top: int) -> None:
    """
    读取视频流
    :param cam: 摄像头参数
    :param stack: Manager.list对象
    :param top: 缓冲栈容量
    :return: None
    """
    while True:
        png_image = client.simGetImages([airsim.ImageRequest(cam,airsim.ImageType.Scene,pixels_as_float = False,compress = False)],vehicle_name='SimpleFlight')
        im = png_image[0]
        imgld = np.fromstring(im.image_data_uint8,dtype=np.uint8)
        img_rgb = imgld.reshape(im.height,im.width,3)
        # print(im.height,im.width)
        #
        img_rgb = Image.fromarray(cv2.cvtColor(img_rgb, cv2.COLOR_BGR2RGB))
        
        stack.append(img_rgb)
            # # 每到一定容量清空一次缓冲栈
            # # 利用gc库，手动清理内存垃圾，防止内存溢出
        if len(stack) >= top:
            del stack[:-1]
            gc.collect()

def direction_control():
    dron_info = airsim.KinematicsState()
    while True:
        print(dron_info.position)

        if keyboard.read_key() == 'up':
            client.moveByVelocityZAsync(2, 0, -2, 0.4).join()     # 第三阶段：以1m/s速度向前飞0.4秒钟
        elif keyboard.read_key() == 'down':
            client.moveByVelocityZAsync(-2, 0, -2, 0.4).join()    # 第三阶段：以1m/s速度向后飞0.4秒钟
        elif keyboard.read_key() == 'right':
            client.moveByVelocityZAsync(0, 2, -2, 0.4).join()     # 第三阶段：以1m/s速度向右飞0.4秒钟
        elif keyboard.read_key() == 'left':
            client.moveByVelocityZAsync(0, -2, -2, 0.4).join()    # 第三阶段：以1m/s速度向左飞0.4秒钟]
        elif keyboard.read_key() == "a":
            client.rotateByYawRateAsync(-10,0.4).join()
        elif keyboard.read_key() == 'd':
            client.rotateByYawRateAsync(10,0.4).join()
        elif keyboard.read_key() == 'w':
            client.moveByAngleZAsync(-2,0,-2,0,0.4).join()
        elif keyboard.read_key() == "s":
            client.moveByAngleZAsync(2,0,-2,0,0.4).join()
        elif keyboard.read_key() == 'space':
            break
        

def takeoff():
    """第一阶段起飞"""
    client.enableApiControl(True)       # 获取控制权
    client.armDisarm(True)              # 解锁
    client.takeoffAsync().join()        # 第一阶段：起飞
    client.moveToZAsync(-2, 5).join()   # 第二阶段：上升到2米高度


def control_dron() -> None:
    """无人机的飞行控制"""
    takeoff()
    direction_control()

    client.landAsync().join()           # 第五阶段：降落
    client.armDisarm(False)             # 上锁
    client.enableApiControl(False)      # 释放控制权


def stimu_sqeuence(t):
    ''' 刺激序列 '''
    for i in range(len(stimuliLoop)):
            cor= (math.sin(2*math.pi*stimuliLoop[i]*dt*t+phase[i])+1)/2
            c[i] = ([int(cor*255),int(cor*255),int(cor*255)])
    return c     
    
    
def read(stack) -> None:
    ''' 闪烁刺激界面 '''
    win = visual.Window(pos=(0,0),color=(0,0,0),fullscr=is_full_screen,colorSpace = 'rgb255',size = (w,h))

    ''' 刺激界面非闪烁下的整体效果 '''
    for i in range(len(position)):
        Rect_test = rect.Rect(win,pos=(position[str(i)][0]*wc,position[str(i)][1]*hc),size=(150*wc,150*wc),units = 'pix',fillColor=(255,255,255),colorSpace = 'rgb255')
        test_Rects.append(Rect_test)

    ''' 刺激界面的提示字符 '''
    for i in range(12):
        Texts_Stim = visual.TextStim(win,text=textList[str(i)],font='Times New Roman',
                                    pos=(textposition[str(i)][0]*wc,textposition[str(i)][1]*hc),units='pix',color=(0,0,0),
                                    colorSpace='rgb255',height=35*wc)
        stim_texts.append(Texts_Stim)  
    
    ''' 刺激块 '''
    for t in range(int(stimulationLength*framerate)):
        color_stim = stimu_sqeuence(t)
        color_stim = list(color_stim.values())
        Rects_Stim = visual.ElementArrayStim(win,fieldShape='sqr',nElements = 12,xys=position_stim,
                                            sizes=(150*wc,150*wc),units = 'pix',colors=color_stim,colorSpace = 'rgb255',
                                            elementTex=np.ones([150,150]),elementMask = np.ones([150,150]))
        stim_Rects.append(Rects_Stim)

    """ 刺激界面显示"""
    for loop in cueseries:   
        for i in loop:
            win.flip()
            # 提示
            for t in range(int(cuelen*framerate)):
                if len(stack) != 0:
                   value = stack[-1]
                   pic = visual.ImageStim(win, value,units='pix',size=(850*wc,450*hc))
                   pic.draw()
                [test_Rect.draw() for test_Rect in test_Rects]
                Rect_cue = rect.Rect(win,pos=(position[str(i)][0]*wc,position[str(i)][1]*hc),size=(150*wc,150*wc),units = 'pix',fillColor=(255,0,0),colorSpace = 'rgb255')
                Rect_cue.draw()
                [text_stim.draw() for text_stim in stim_texts]
                win.flip()
            
           # triggerWrite(i)                  # 打标签
            for rect_stim in stim_Rects:     # 刺激
                tic = time.time() 
                # 显示视频流
                if len(stack) != 0:
                   value = stack[-1]
                   pic = visual.ImageStim(win, value,units='pix',size=(850*wc,450*hc))
                   pic.draw()
                # 画出刺激块
                rect_stim.draw()
                # 显示提示字符
                [text_stim.draw() for text_stim in stim_texts]
                win.flip()
                toc = time.time()
                T = toc-tic
                res_time.append(T)
  
    print(np.average(res_time))
    win.flip()  
    while 'space' not in event.getKeys():
        pass
    win.close()


if __name__ == "__main__":
    q = Manager().list()
    pw = Process(target=write,args=(q,"1",20))
    pr = Process(target=read, args=(q,))
    pc = Process(target=control_dron)
    # Pr = Process()
    # 启动子进程Pw，写入
    pw.start()
    pr.start()
    pc.start()
    # pd.start()
    pr.join()
    pc.join()
    # pw进程里是死循环，无法等待其结束，只能强行终止:
    pw.terminate()




