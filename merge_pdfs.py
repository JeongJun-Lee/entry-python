import os
import re
from pypdf import PdfWriter, PdfReader

def merge_pdfs():
    pdf_dir = os.path.abspath("pub/pdf")
    output_filename = "merged_all.pdf"
    output_path = os.path.join(pdf_dir, output_filename)

    # Get all PDF files excluding previous merged files
    files = [
        f for f in os.listdir(pdf_dir)
        if f.endswith(".pdf") and not f.startswith("merged")
    ]

    # Extract multi-part numerical prefix for numeric sorting (0.0, 0.1, 1, 2, 3.0, 3.1, ... 4.1, 4.3)
    def extract_prefix(filename):
        match = re.match(r"^(\d+(?:\.\d+)*)", filename)
        if match:
            numbers = tuple(int(x) for x in match.group(1).split("."))
            return (0, numbers, filename)
        return (1, (), filename)

    files_sorted = sorted(files, key=extract_prefix)

    writer = PdfWriter()
    total_pages = 0

    print("Merging PDF files in numerical prefix order:")
    for f in files_sorted:
        file_path = os.path.join(pdf_dir, f)
        reader = PdfReader(file_path)
        num_pages = len(reader.pages)
        total_pages += num_pages
        bookmark_title = os.path.splitext(f)[0]
        writer.append(file_path, outline_item=bookmark_title)
        print(f" - Added {f} ({num_pages} pages)")

    with open(output_path, "wb") as f_out:
        writer.write(f_out)

    writer.close()
    
    print(f"\nSuccessfully created merged PDF file:")
    print(f"- {output_path} ({total_pages} pages)")

if __name__ == "__main__":
    merge_pdfs()
