import cv2
import numpy as np
from time import time
import random
import math
import webcolors


font = cv2.FONT_HERSHEY_COMPLEX_SMALL

apple = cv2.imread("apple.png", -1)
apple_mask = apple[:, :, 3]
apple_mask_inv = cv2.bitwise_not(apple_mask)
apple = apple[:, :, 0:3]
apple = cv2.resize(apple, (40, 40), interpolation=cv2.INTER_AREA)
apple_mask = cv2.resize(apple_mask, (40, 40), interpolation=cv2.INTER_AREA)
apple_mask_inv = cv2.resize(apple_mask_inv, (40, 40), interpolation=cv2.INTER_AREA)

blank_img = np.zeros((480, 640, 3), np.uint8)

video = cv2.VideoCapture(0)
kernel_erode = np.ones((4, 4), np.uint8)
kernel_close = np.ones((15, 15), np.uint8)
color = input("Enter color: ")
rgb = webcolors.name_to_rgb(color)
red = rgb.red
blue = rgb.blue
green = rgb.green
lower_upper = []


def color_convert(r, bl, g):
    co = np.uint8([[[bl, g, r]]])
    hsv_color = cv2.cvtColor(co, cv2.COLOR_BGR2HSV)

    hue = hsv_color[0][0][0]
    lower_upper.append([hue - 10, 100, 100])
    lower_upper.append([hue + 10, 255, 255])
    return lower_upper


def detect_color(h):
    lu = color_convert(red, blue, green)
    lower = np.array(lu[0])
    upper = np.array(lu[1])
    mask = cv2.inRange(h, lower, upper)
    mask = cv2.erode(mask, kernel_erode, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)
    return mask


def orientation(p, q, r):
    val = int(((q[1] - p[1]) * (r[0] - q[0])) - ((q[0] - p[0]) * (r[1] - q[1])))
    if val == 0:
        return 0
    elif val > 0:
        return 1
    else:
        return 2


def intersect(p, q, r, s):
    o1 = orientation(p, q, r)
    o2 = orientation(p, q, s)
    o3 = orientation(r, s, p)
    o4 = orientation(r, s, q)
    if o1 != o2 and o3 != o4:
        return True

    return False


start_time = int(time())
q, snake_len, score, temp = 0, 200, 0, 1
point_x, point_y = 0, 0
last_point_x, last_point_y, dist, length = 0, 0, 0, 0
points = []
list_len = []
random_x = random.randint(10, 550)
random_y = random.randint(10, 400)
a, b, c, d = [], [], [], []


while 1:
    xr, yr, wr, hr = 0, 0, 0, 0
    ret, frame = video.read()
    frame = cv2.flip(frame, 1)
    if q == 0 and point_x != 0 and point_y != 0:
        last_point_x = point_x
        last_point_y = point_y
        q = 1

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    mask = detect_color(hsv)
    # finding contours
    _, contour, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # drawing rectangle around the accepted blob
    try:
        for i in range(0, 10):
            xr, yr, wr, hr = cv2.boundingRect(contour[i])
            if (wr*hr) > 2000:
                break
    except:
        pass

    cv2.rectangle(frame, (xr, yr), (xr + wr, yr + hr), (0, 0, 255), 2)

    point_x = int(xr+(wr/2))
    point_y = int(yr+(hr/2))

    dist = int(math.sqrt(pow((last_point_x - point_x), 2) + pow((last_point_y - point_y), 2)))
    if point_x != 0 and point_y != 0 and dist > 5:

        list_len.append(dist)
        length += dist
        last_point_x = point_x
        last_point_y = point_y
        points.append([point_x, point_y])

    if length >= snake_len:
        for i in range(len(list_len)):
            length -= list_len[0]
            list_len.pop(0)
            points.pop(0)
            if length <= snake_len:
                break

    blank_img = np.zeros((480, 640, 3), np.uint8)

    for i, j in enumerate(points):
        if i == 0:
            continue
        cv2.line(blank_img, (points[i-1][0], points[i-1][1]), (j[0], j[1]), (blue, green, red), 5)
    cv2.circle(blank_img, (last_point_x, last_point_y), 5, (10, 200, 150), -1)

    if random_x < last_point_x < (random_x + 40) and random_y < last_point_y < (random_y + 40):
        score += 1
        random_x = random.randint(10, 550)
        random_y = random.randint(10, 400)

    frame = cv2.add(frame, blank_img)

    roi = frame[random_y:random_y+40, random_x:random_x+40]
    img_bg = cv2.bitwise_and(roi, roi, mask=apple_mask_inv)
    img_fg = cv2.bitwise_and(apple, apple, mask=apple_mask)
    dst = cv2.add(img_bg, img_fg)
    frame[random_y:random_y + 40, random_x:random_x + 40] = dst
    cv2.putText(frame, str("Score - "+str(score)), (250, 450), font, 1, (0, 0, 0), 2, cv2.LINE_AA)

    if len(points) > 5:

        b = points[len(points)-2]
        a = points[len(points)-1]
        for i in range(len(points)-3):
            c = points[i]
            d = points[i+1]
            if intersect(a, b, c, d) and len(c) != 0 and len(d) != 0:
                temp = 0
                break
        if temp == 0:
            break

    cv2.imshow("frame", frame)

    if (int(time())-start_time) > 1:
        snake_len += 40
        start_time = int(time())
    key = cv2.waitKey(1)
    if key == 27:
        break


video.release()
cv2.destroyAllWindows()
cv2.putText(frame, str("Game Over!"), (100, 230), font, 3, (255, 0, 0), 3, cv2.LINE_AA)
cv2.putText(frame, str("Press any key to Exit."), (180, 260), font, 1, (255, 200, 0), 2, cv2.LINE_AA)
cv2.imshow("frame", frame)
k = cv2.waitKey(0)
cv2.destroyAllWindows()
