import os
import io
import csv
from read_data import convert_pdf_to_txt
from PIL import Image
import pytesseract
from wand.image import Image as wi
import hashlib
import pandas as pd
import numpy as np
import pprint as pp

def conv_pdf(pdf):
    with open('./pdfs/' + pdf, 'rb') as f:
        # text from pdf
        bfr = io.BufferedReader(f)
        pdf_text = convert_pdf_to_txt(bfr)

        # recognized text (OCR) from pdf
        if len(pdf_text.strip()) <= 50:
            with wi(filename=pdf, resolution=200) as pdf_file:
                pdfImage = pdf_file.convert('jpeg')
                imageBlobs = []
                for img in pdfImage.sequence:
                    with wi(image = img) as imgPage:
                        imageBlobs.append(imgPage.make_blob('jpeg'))

            recognized_text = []

            for imgBlob in imageBlobs:
                im = Image.open(io.BytesIO(imgBlob))
                text = pytesseract.image_to_string(im, lang = 'eng')
                recognized_text.append(text)

            recognized_text = '\n\n\n'.join(recognized_text)

        pdf_text = pdf_text if len(pdf_text.strip()) > 50 else recognized_text
        
        return pdf_text