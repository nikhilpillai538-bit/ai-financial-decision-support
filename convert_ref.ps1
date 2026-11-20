$docPath = 'C:\Users\NIKHIL.P\.gemini\antigravity\brain\5936fef4-7415-400c-a049-08bfb405b03f\.user_uploaded\media_1795096132210_e50aca06.doc'
$docxPath = 'C:\Users\NIKHIL.P\.gemini\antigravity\scratch\ai-financial-decision-support\ref_format.docx'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($docPath)
    Write-Host "Opened doc successfully, shapes count: $($doc.Shapes.Count), inline shapes: $($doc.InlineShapes.Count)"
    $doc.SaveAs2([ref]$docxPath, [ref]16)
    Write-Host "Saved as docx to $docxPath"
    $doc.Close()
} catch {
    Write-Host "Error: $_"
} finally {
    $word.Quit()
}
