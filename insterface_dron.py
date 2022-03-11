import cv2
import gc
import multiprocessing as mp
from multiprocessing import Event, Process, Manager
from psychopy import visual, event, core
from PIL import Image
import numpy as np
import time
import airsim
import keyboard


client = airsim.MultirotorClient("192.168.18.8")  # connect to the AirSim simulator
client.confirmConnection()
client.enableApiControl(True)       # 获取控制权
client.armDisarm(True)              # 解锁
  


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
        


def control_dron() -> None:
    client.takeoffAsync().join()        # 第一阶段：起飞
    client.moveToZAsync(-2, 5).join()   # 第二阶段：上升到2米高度

    direction_control()

    client.landAsync().join()           # 第五阶段：降落
    client.armDisarm(False)             # 上锁
    client.enableApiControl(False)      # 释放控制权

# 向共享缓冲栈中写入数据:
def write(stack, cam, top: int) -> None:
    """
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
        # while True:
        stack.append(img)
            # # 每到一定容量清空一次缓冲栈
            # # 利用gc库，手动清理内存垃圾，防止内存溢出
            # if len(stack) >= top:
            #     del stack[:-1]
            #     gc.collect()

def sin_wave(A, f, fs, phi, t):
                '''
                :params A:    振幅
                :params f:    信号频率
                :params fs:   采样频率
                :params phi:  相位
                :params t:    时间长度
                '''
                # 若时间序列长度为 t=1s,
                # 采样频率 fs=1000 Hz, 则采样时间间隔 Ts=1/fs=0.001s
                # 对于时间序列采样点个数为 n=t/Ts=1/0.001=1000, 即有1000个点,每个点间隔为 Ts
                Ts = 1 / fs
                n = t / Ts
                n = np.arange(n)
                y = A * np.sin(2 * np.pi * f * n * Ts + phi * (np.pi / 180))
                return y

# 在缓冲栈中读取数据:
def read(stack,stackudp) -> None:
    # print('Process to read: %s' % os.getpid())
    w = 640
    h = 480
    DISPSIZE = (w, h)
    Win = visual.Window(size=DISPSIZE, units='pix', fullscr=False )
    refresh_rate = Win.getActualFrameRate(nIdentical=20, nWarmUpFrames=20)
    # print(refresh_rate)
    flash_time = 0.1
    flash_frames = int(flash_time * refresh_rate)
    t = 0.1
    # fs = refresh_rate

    parameter = np.array([[1, 9, refresh_rate, 0, t],
                         [1, 9, refresh_rate, 30, t],
                         [1, 9, refresh_rate, 60, t],
                         [1, 9, refresh_rate, 90, t]])  # 创建矩阵
    #
    stim_colors = np.array([(sin_wave(parameter[0, 0], parameter[0, 1], parameter[0, 2], parameter[0, 3],
                            parameter[0, 4]) + 1) / 2 * 255,
                  (sin_wave(parameter[1, 0], parameter[1, 1], parameter[1, 2], parameter[1, 3],
                            parameter[1, 4]) + 1) / 2 * 255,
                  (sin_wave(parameter[2, 0], parameter[2, 1], parameter[2, 2], parameter[2, 3],
                            parameter[0, 4]) + 1) / 2 * 255,
                  (sin_wave(parameter[3, 0], parameter[3, 1], parameter[3, 2], parameter[3, 3],
                            parameter[3, 4]) + 1) / 2 * 255])
    text1 = visual.TextStim(Win, text='Up', color='blue', units='pix', pos=(0, 120))
    text2 = visual.TextStim(Win, text='Down', color='blue', units='pix', pos=(0, -120))
    text3 = visual.TextStim(Win, text='Left', color='blue', units='pix', pos=(-160, 0))
    text4 = visual.TextStim(Win, text='Right', color='blue', units='pix', pos=(160, 0))
    temp = 120
    
    while True:
        if len(stack) != 0:
            value = stack.pop()
            pic = visual.ImageStim(Win, value)
            if len(stackudp) != 0:
                udpvalue = stackudp.pop()
                udp = udpvalue.decode('utf-8')
                temp = udp
            else:
                udp = temp
            t = time.perf_counter()
            for i in range(flash_frames):
                tic = time.time() 
                pic.draw()
                visual.ImageStim(Win, Image.fromarray(np.full((80, 80), stim_colors[0, i])), units='pix',
                                 pos=(0, udp),colorSpace='rgb255').draw()
                visual.ImageStim(Win, Image.fromarray(np.full((80, 80), stim_colors[1, i])), units='pix',
                                 pos=(0, -120),colorSpace='rgb255').draw()
                visual.ImageStim(Win, Image.fromarray(np.full((80, 80), stim_colors[2, i])), units='pix',
                                 pos=(-160, 0),colorSpace='rgb255').draw()
                visual.ImageStim(Win, Image.fromarray(np.full((80, 80), stim_colors[3, i])), units='pix',
                                 pos=(160, 0),colorSpace='rgb255').draw()
                text1.draw()
                text2.draw()
                text3.draw()
                text4.draw()
                Win.flip()
                toc = time.time()
                print(toc-tic)





if __name__ == '__main__':
    q = Manager().list()
    m = Manager().list()
    d = Manager().list()
    pw = Process(target=write,args=(q,"0",20))
    pr = Process(target=read, args=(q, d))
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