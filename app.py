from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF
from PIL import Image
import io
import cv2
import pytesseract
from PIL import Image
import random


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)

PDF_PATH = "./uploads/sozluk.pdf"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        word = request.form["word"].strip().lower()
        page_number = find_word_in_pdf(PDF_PATH, word)

        if page_number is not None:
            image_path = render_pdf_page_as_image(PDF_PATH, page_number,word)
            return render_template("index.html", image_path=image_path, word=word)
        else:
            return render_template("index.html", error="Word not found.")

    return render_template("index.html")


def find_word_in_pdf(pdf_path, word):
    doc = fitz.open(pdf_path)
    for i, page in enumerate(doc):
        text = page.get_text().lower()
        if word in text:
            return i  # Return the first matched page number
    return None


def render_pdf_page_as_image(pdf_path, page_number, target_word):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number)

    pix = page.get_pixmap(dpi=150)

    # Save original image first
    code = random.randint(100000, 999999)
    original_path = f"./static/page_{code}.png"
    pix.save(original_path)

    # Load image with OpenCV
    image = cv2.imread(original_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # OCR to find word bounding boxes
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

    found = False
    for i in range(len(data['text'])):
        word = data['text'][i]
        word = data['text'][i]
        try:
            conf = int(data['conf'][i])
        except ValueError:
            conf = -1  # or 0, to treat invalid as low confidence

       
        if word.strip().lower() == target_word.lower():
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            # Draw rectangle and label
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image, word, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            found = True

    if found:
        print(f"'{target_word}' found and highlighted.")
    else:
        print(f"'{target_word}' not found.")

    # Save the highlighted image
    highlighted_path = f"./static/page_{code}_highlighted.png"
    cv2.imwrite(highlighted_path, image)

    # Close the PDF doc
    doc.close()

    # Return the highlighted image path (to display in web)
    return highlighted_path

if __name__ == "__main__":
    app.run(debug=True)
