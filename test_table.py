import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

doc = docx.Document()
table = doc.add_table(rows=1, cols=1)
cell = table.cell(0, 0)
cell.width = Inches(6.0)

shd_xml = f'<w:shd {nsdecls("w")} w:fill="F8FAFC"/>'
cell._tc.get_or_add_tcPr().append(parse_xml(shd_xml))

border_xml = f'''<w:tcBorders {nsdecls("w")}>
    <w:top w:val="single" w:sz="8" w:space="0" w:color="94A3B8"/>
    <w:left w:val="single" w:sz="8" w:space="0" w:color="94A3B8"/>
    <w:bottom w:val="single" w:sz="8" w:space="0" w:color="94A3B8"/>
    <w:right w:val="single" w:sz="8" w:space="0" w:color="94A3B8"/>
</w:tcBorders>'''
cell._tc.get_or_add_tcPr().append(parse_xml(border_xml))

p = cell.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(36)
p.paragraph_format.space_after = Pt(6)
run = p.add_run("INSERT PROJECT SCREENSHOT HERE")
run.font.bold = True
run.font.size = Pt(11)
run.font.color.rgb = RGBColor(30, 41, 59)

p2 = cell.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
p2.paragraph_format.space_after = Pt(36)
run2 = p2.add_run("[Main Financial Dashboard displaying Portfolio Value, Cash Flow, and Emergency Fund]")
run2.font.italic = True
run2.font.size = Pt(9.5)
run2.font.color.rgb = RGBColor(100, 116, 139)

doc.save("test_table.docx")
print("Table styled successfully and saved to test_table.docx")
