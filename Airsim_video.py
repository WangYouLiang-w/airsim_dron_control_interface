import airsim
import cv2
import numpy as np

#client = airsim.MultirotorClient("172.18.140.175")  # connect to the AirSim simulator
client = airsim.MultirotorClient("127.0.0.1")  # connect to the AirSim simulator
client.confirmConnection()
client.enableApiControl(True)       # 获取控制权
client.armDisarm(True)              # 解锁


if __name__ == '__main__':
    while True:
        try:
            png_image = client.simGetImages([airsim.ImageRequest("front_center",airsim.ImageType.Scene,False,False)])
            image = png_image[0]
            imgld = np.frombuffer(image.image_data_uint8,dtype=np.uint8)#get numpy array
            img_rgb = imgld.reshape(image.height, image.width, 3)#reshape array to 3 channel image array H X W X 3
            cv2.imshow('img_rgb',img_rgb)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
        except:
            continue
