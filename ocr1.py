try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract
import cv2


# If you don't have tesseract executable in your PATH, include the following:
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
# Example tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract'

# Simple image to string
custom_config = r'--oem 3 --psm 4'

#customize img
img = cv2.imread('lotto_ticket.png')
img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 

def thresholding(image):
    return cv2.threshold(img, 120, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

#cv2.imshow('thresh', thresholding(img))
#cv2.waitKey(0)
#cv2.destroyAllWindows()

print(pytesseract.image_to_string(thresholding(img), config=custom_config))

