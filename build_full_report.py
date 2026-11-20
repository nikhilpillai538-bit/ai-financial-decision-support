"""
Master Document Builder for Bhilai Institute of Technology, Durg (C.G.)
SEPM Project Report:
AI-POWERED PERSONAL FINANCIAL PORTFOLIO MANAGEMENT AND DECISION SUPPORT SYSTEM

Assembles all preliminary pages, 6 technical chapters, 11 high-res diagrams,
24 screenshot placeholders, tables, formulas, and academic references.
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Import modular chapter generators
import doc_preliminary
import doc_chapter1
import doc_chapter2
import doc_chapter3
import doc_chapter4
import doc_chapter5
import doc_chapter6_and_refs

def set_page_margins(section, left=1.25, right=1.0, top=1.0, bottom=1.0):
    section.page_width = Inches(8.27)   # A4 Width
    section.page_height = Inches(11.69) # A4 Height
    section.left_margin = Inches(left)
    section.right_margin = Inches(right)
    section.top_margin = Inches(top)
    section.bottom_margin = Inches(bottom)

def add_header_footer(doc, project_title="AI-Powered Personal Financial Portfolio Management & Decision Support System"):
    # Apply subtle academic header across sections
    for s_idx, section in enumerate(doc.sections):
        if s_idx == 0:
            # Cover page - no header/footer
            section.different_first_page_header_footer = True
            continue
            
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run(project_title + " | B.Tech IT SEPM Project")
        hrun.font.name = "Times New Roman"
        hrun.font.size = Pt(8.5)
        hrun.font.italic = True
        hrun.font.color.rgb = RGBColor(100, 116, 139)
        
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Bhilai Institute of Technology, Durg (C.G.)")
        frun.font.name = "Times New Roman"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(148, 163, 184)

def build_report():
    print("Initializing Microsoft Word Document...")
    doc = docx.Document()
    
    # Configure base styles
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Times New Roman'
    style_normal.font.size = Pt(12)
    style_normal.font.color.rgb = RGBColor(30, 41, 59)
    style_normal.paragraph_format.line_spacing = 1.25
    style_normal.paragraph_format.space_after = Pt(6)
    
    # Configure section margins
    set_page_margins(doc.sections[0])
    
    logo_path = os.path.abspath('bit_durg_logo.png')
    if not os.path.exists(logo_path):
        print(f"Warning: Logo not found at {logo_path}")
        
    print("1. Generating Preliminary Pages (Cover, Declaration, Certificates, Abstract, TOC)...")
    doc_preliminary.add_cover_page(doc, logo_path)
    doc_preliminary.add_declaration_page(doc)
    doc_preliminary.add_supervisor_certificate(doc)
    doc_preliminary.add_examiners_certificate(doc)
    doc_preliminary.add_acknowledgement(doc)
    doc_preliminary.add_abstract(doc)
    doc_preliminary.add_list_of_symbols(doc)
    doc_preliminary.add_list_of_abbreviations(doc)
    doc_preliminary.add_list_of_tables(doc)
    doc_preliminary.add_list_of_figures(doc)
    doc_preliminary.add_table_of_contents(doc)
    
    print("2. Generating Chapter 1: Introduction...")
    doc_chapter1.add_chapter_1(doc)
    
    print("3. Generating Chapter 2: Literature Review...")
    doc_chapter2.add_chapter_2(doc)
    
    print("4. Generating Chapter 3: Problem Identification and SRS (with 7 DFDs)...")
    doc_chapter3.add_chapter_3(doc)
    
    print("5. Generating Chapter 4: Methodology and System Design (with 4 Architecture Diagrams & Math Models)...")
    doc_chapter4.add_chapter_4(doc)
    
    print("6. Generating Chapter 5: Implementation, Results and Discussion (with 24 Screenshot Placeholders & Test Matrices)...")
    doc_chapter5.add_chapter_5(doc)
    
    print("7. Generating Chapter 6: Conclusion and Future Scope + References...")
    doc_chapter6_and_refs.add_chapter_6(doc)
    doc_chapter6_and_refs.add_references(doc)
    
    print("Applying Academic Headers and Footers...")
    add_header_footer(doc)
    
    out_docx = "AI_Financial_Decision_Support_SEPM_Report.docx"
    doc.save(out_docx)
    file_size_kb = os.path.getsize(out_docx) / 1024
    print(f"SUCCESS: Report saved as '{out_docx}' ({file_size_kb:.1f} KB)")
    return out_docx

if __name__ == '__main__':
    build_report()
