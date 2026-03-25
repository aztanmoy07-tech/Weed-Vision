import cv2
import numpy as np

def load_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Image not found")
    return image

def resize_image(image, size=(640, 640)):
    return cv2.resize(image, size)

def apply_gaussian_blur(image):
    return cv2.GaussianBlur(image, (5, 5), 0)

def excess_green_index(image):
    B, G, R = cv2.split(image)
    exg = 2 * G.astype(np.float32) - R.astype(np.float32) - B.astype(np.float32)
    exg = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX)
    return exg.astype(np.uint8)

def threshold_exg(exg):
    _, binary = cv2.threshold(exg, 120, 255, cv2.THRESH_BINARY)
    return binary

def morphological_operations(binary):
    kernel = np.ones((5, 5), np.uint8)
    opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel)
    return closing

def preprocess_pipeline(image_path):
    image = load_image(image_path)
    image = resize_image(image)
    blurred = apply_gaussian_blur(image)

    exg = excess_green_index(blurred)
    binary = threshold_exg(exg)
    clean = morphological_operations(binary)

    return image, exg, clean