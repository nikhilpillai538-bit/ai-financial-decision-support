$docxPath = 'C:\Users\NIKHIL.P\.gemini\antigravity\scratch\ai-financial-decision-support\AI_Financial_Decision_Support_SEPM_Report.docx'
$pdfPath  = 'C:\Users\NIKHIL.P\.gemini\antigravity\scratch\ai-financial-decision-support\AI_Financial_Decision_Support_SEPM_Report.pdf'

Write-Host "Converting $docxPath to PDF via Word COM..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($docxPath)
    # wdFormatPDF = 17
    $doc.SaveAs2([ref]$pdfPath, [ref]17)
    Write-Host "PDF generated successfully at $pdfPath"
    $doc.Close()
} catch {
    Write-Host "Error converting to PDF: $_"
} finally {
    $word.Quit()
}
