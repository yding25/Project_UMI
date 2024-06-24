import cv2

# 读取图像
img = cv2.imread('image.png')

# 回调函数用于获取鼠标点击事件的坐标
def get_points(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"Point: ({x}, {y})")

points = []
cv2.namedWindow("image")
cv2.setMouseCallback("image", get_points)

while True:
    cv2.imshow("image", img)
    if cv2.waitKey(20) & 0xFF == 27:  # 按下ESC键退出
        break

cv2.destroyAllWindows()
