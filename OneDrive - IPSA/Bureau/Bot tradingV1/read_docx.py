# -*- coding: utf-8 -*-
import zipfile
import xml.etree.ElementTree as ET

def read_docx(file_path):
    try:
        with zipfile.ZipFile(file_path) as z:
            xml_content = z.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            # Namespace map usually required for docx
            # But we can just search for all 't' tags which contain text
            
            text_content = []
            for elem in tree.iter():
                if elem.tag.endswith('}t'):
                    if elem.text:
                        text_content.append(elem.text)
                elif elem.tag.endswith('}p'):
                    text_content.append('\n') 
            
            return ''.join(text_content)
    except Exception as e:
        return str(e)

import glob

if __name__ == "__main__":
    files = glob.glob("*.docx")
    for f in files:
        if "liorations" in f:
            content = read_docx(f)
            with open("improvements_content.txt", "w") as out:
                out.write(content.encode('utf-8'))
            print("Content written to improvements_content.txt")
            break
