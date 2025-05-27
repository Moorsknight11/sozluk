from flask import Flask, render_template, request, send_file, url_for
import fitz  # PyMuPDF
from PIL import Image
import io
import cv2
import pytesseract
from PIL import Image
import random
import os


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

PDF_PATH = "./uploads/sozluk.pdf"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        word = request.form["word"].strip().lower()
        page_number = find_word_in_pdf(PDF_PATH, word)

        if page_number is not None and page_number != -1:
            image_url = render_pdf_page_as_image(PDF_PATH, page_number, word)
            return render_template("index.html", image_path=image_url, word=word)
        else:
            return render_template("index.html", error="Word not found.")

    return render_template("index.html")



import re

def find_word_in_pdf(pdf_path, word, start_page=17):
    word = word.lower()
    doc = fitz.open(pdf_path)
    for page_num in range(start_page, len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text().lower()

        # Split text into words using regex to handle punctuation properly
        words = re.findall(r'\b\w+\b', text)

        if word in words:
            return page_num  # word found as a separate word
    return -1  # word not found



def render_pdf_page_as_image(pdf_path, page_number, target_word):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number)

    pix = page.get_pixmap(dpi=150)

    code = random.randint(100000, 999999)
    original_path = os.path.join(STATIC_DIR, f"page_{code}.png")
    pix.save(original_path)

    image = cv2.imread(original_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    data = pytesseract.image_to_data(gray, lang='tur', output_type=pytesseract.Output.DICT)

    found = False
    for i in range(len(data['text'])):
        word = data['text'][i]
        try:
            conf = int(data['conf'][i])
        except ValueError:
            conf = -1

        if word.strip().lower() == target_word.lower():
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image, word, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            found = True

    highlighted_path = os.path.join(STATIC_DIR, f"page_{code}_highlighted.png")
    cv2.imwrite(highlighted_path, image)
    doc.close()

    # Return the URL path for the template
    return url_for('static', filename=f"page_{code}_highlighted.png")


if __name__ == "__main__":
    app.run(debug=True)
