import numpy as np
import cv2

cap = cv2.VideoCapture(0)

while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()

    # 이미지 상하반전
    frame = cv2.flip(frame, 0)

    # 이미지 사이즈 축소
    rsz = cv2.resize(frame, dsize=(320, 240))

    # 잡음제거를 위한 이미지 블러링 처리
    # blur = cv2.GaussianBlur(rsz, (11, 11), 0)

    # 이미지를 흑백으로 전환
    gray = cv2.cvtColor(rsz, cv2.COLOR_BGR2GRAY)

    # 라플라시안 및 소벨 영상
    laplacian = cv2.Laplacian(gray,cv2.CV_64F)
    sobelx = cv2.Sobel(gray,cv2.CV_64F,1,0,ksize=5)
    sobely = cv2.Sobel(gray,cv2.CV_64F,0,1,ksize=5)

    # 이미지 연결
    res = np.concatenate((laplacian, sobelx, sobely), axis=1)

    # Display the resulting frame
    # cv2.imshow('frame',frame)
    cv2.imshow('res', res)

    # waitKey(in ms)
    if cv2.waitKey(200) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()