import airsim
import cv2
import numpy as np
import keyboard
import multiprocessing 

client = airsim.MultirotorClient("192.168.18.8")  # connect to the AirSim simulator
client.confirmConnection()
client.enableApiControl(True)       # 获取控制权
client.armDisarm(True)              # 解锁


def direction_control():
    if keyboard.read_key() == 'up':
         client.moveByVelocityZAsync(2, 0, -2, 0.4).join()     # 第三阶段：以1m/s速度向前飞0.4秒钟
    elif keyboard.read_key() == 'down':
        client.moveByVelocityZAsync(-2, 0, -2, 0.4).join()    # 第三阶段：以1m/s速度向后飞0.4秒钟
    if keyboard.read_key() == 'right':
        client.moveByVelocityZAsync(0, 2, -2, 0.4).join()     # 第三阶段：以1m/s速度向右飞0.4秒钟
    elif keyboard.read_key() == 'left':
        client.moveByVelocityZAsync(0, -2, -2, 0.4).join()    # 第三阶段：以1m/s速度向左飞0.4秒钟]

def get_image() -> None:
    while True:
        png_image = client.simGetImages([airsim.ImageRequest("0",airsim.ImageType.Scene,pixels_as_float = False,compress = False)])
        image = png_image[0]
        imgld = np.frombuffer(image.image_data_uint8,dtype=np.uint8)
        img_rgb = imgld.reshape(image.height,image.width,3)
        cv2.imshow('img_rgb',img_rgb)


def control_dron() -> None:
    client.takeoffAsync().join()        # 第一阶段：起飞
    client.moveToZAsync(-2, 5).join()   # 第二阶段：上升到2米高度

    while True:
        direction_control()
        if keyboard.read_key() == 'space':
            break
 
    client.landAsync().join()           # 第五阶段：降落
    client.armDisarm(False)             # 上锁
    client.enableApiControl(False)      # 释放控制权


if __name__ == '__main__':
    pi = multiprocessing.Process(target=get_image)
    pc = multiprocessing.Process(target=control_dron)

    pi.start()
    pc.start()

    pi.join()
    pc.join()
    