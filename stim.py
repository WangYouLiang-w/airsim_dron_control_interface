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
choice =  1
dt = 1/framerate
win = visual.Window(pos=(0,0),color=(0,0,0),fullscr=False,colorSpace = 'rgb255',size = windowSquareSize)
Rect_video = rect.Rect(win,pos=(0,0),size=(850,450),units = 'pix',fillColor=(125,125,125),colorSpace = 'rgb255')
stim_texts = []
stim_Rects = []
res_time= []
test_Rects = [] 
position_stim = [(0,325),(-100,-325),(325,325),(300,-325),(-525,100),(525,100),(525,-100),(-525,-100),(-325,325),(0,-125),(-300,-325),(100,-325)]
c = {}
video_image = []

client = airsim.MultirotorClient("192.168.18.8")  # connect to the AirSim simulator
client.confirmConnection()



def draw_rect():
    ''' 刺激界面非闪烁下的整体效果 '''
    Rect_video.draw()
    for i in range(len(position)):
        Rect_test = rect.Rect(win,pos=position[str(i)],size=(150,150),units = 'pix',fillColor=(255,255,255),colorSpace = 'rgb255')
        test_Rects.append(Rect_test)


def stimu_sqeuence(t):
    ''' 刺激序列 '''
    for i in range(len(stimuliLoop)):
            cor= (math.sin(2*math.pi*stimuliLoop[i]*dt*t+phase[i])+1)/2
            c[i] = ([int(cor*255),int(cor*255),int(cor*255)])
    return c     
    
        
def Stim_text():
    ''' 刺激界面的提示字符 '''
    for i in range(12):
        Texts_Stim = visual.TextStim(win,text=textList[str(i)],font='Times New Roman',
                                    pos=textposition[str(i)],units='pix',color=(0,0,0),
                                    colorSpace='rgb255',height=35)
        stim_texts.append(Texts_Stim)
    
       
def draw_RectStims():
        ''' 刺激界面方块 '''
        for t in range(int(stimulationLength*framerate)):
            color_stim = stimu_sqeuence(t)
            color_stim = list(color_stim.values())
            Rects_Stim = visual.ElementArrayStim(win,fieldShape='sqr',nElements = 12,xys=position_stim,
                                                sizes=(150,150),units = 'pix',colors=color_stim,colorSpace = 'rgb255',
                                                elementTex=np.ones([150,150]),elementMask = np.ones([150,150]))
            stim_Rects.append(Rects_Stim)
            
      
def cue_stimu(cue_num,cue):
    ''' 刺激提示 '''
    for t in range(int(cue*framerate)):
        Rect_video.draw()
        [test_Rect.draw() for test_Rect in test_Rects]
        Rect_cue = rect.Rect(win,pos=position[str(cue_num)],size=(150,150),units = 'pix',fillColor=(255,0,0),colorSpace = 'rgb255')
        Rect_cue.draw()
        [text_stim.draw() for text_stim in stim_texts]
        win.flip()




def write(stack, cam, top: int) ->None:
    """
    获取视频流
    :param cam: 摄像头参数
    :param stack: Manager.list对象
    :param top: 缓冲栈容量
    :return: None
    """
    while True:
        png_image = client.simGetImages([airsim.ImageRequest(cam,airsim.ImageType.Scene,pixels_as_float = False,compress = False)])
        im = png_image[0]
        imgld = np.frombuffer(im.image_data_uint8,dtype=np.uint8)
        img_rgb = imgld.reshape(im.height,im.width,3)
        img = Image.fromarray(cv2.cvtColor(img_rgb, cv2.COLOR_BGR2RGB))
        stack.append(img)
    # while True:
    #         stack.append(img)
    #         # 每到一定容量清空一次缓冲栈
    #         # 利用gc库，手动清理内存垃圾，防止内存溢出
    #         if len(stack) >= top:
    #             del stack[:-1]
    #             gc.collect()

    
def read(stack) -> None:
    ''' 闪烁刺激界面 '''
    draw_rect()
    Stim_text()
    draw_RectStims()
  
    for loop in cueseries:   
        for i in loop:
            win.flip()
            cue_stimu(i,cuelen)  # 提示
           # triggerWrite(i)                  # 打标签
            for rect_stim in stim_Rects:     # 刺激
                tic = time.time() 
                if len(stack) != 0:
                   value = stack.pop()
                   pic = visual.ImageStim(win, value,units='pix')
                   pic.draw()
                rect_stim.draw()
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


def direction_control():
    while True:
        if keyboard.read_key() == 'up':
            client.moveByVelocityZAsync(2, 0, -2, 0.4).join()     # 第三阶段：以1m/s速度向前飞0.4秒钟
        elif keyboard.read_key() == 'down':
            client.moveByVelocityZAsync(-2, 0, -2, 0.4).join()    # 第三阶段：以1m/s速度向后飞0.4秒钟
        elif keyboard.read_key() == 'right':
            client.moveByVelocityZAsync(0, 2, -2, 0.4).join()     # 第三阶段：以1m/s速度向右飞0.4秒钟
        elif keyboard.read_key() == 'left':
            client.moveByVelocityZAsync(0, -2, -2, 0.4).join()    # 第三阶段：以1m/s速度向左飞0.4秒钟]
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


if __name__ == "__main__":
    q = Manager().list()
    pw = multiprocessing.Process(target=write,args=(q,"0",20))
    pr = multiprocessing.Process(target=read,args=(q,))
    pc = Process(target=control_dron)
    pw.start()
    pr.start()
    pc.start()

    pr.join()
    pc.join()
    # pw进程里是死循环，无法等待其结束，只能强行终止:
    pw.terminate()


