# Collaudo di campagna-ordini.xlsx con Excel per Windows.
#   .\verifica-excel.ps1
# Apre il foglio in sola lettura, confronta ogni lead con casi-attesi.csv, cambia dati e regole in memoria
# e controlla che cosa si sposta. Chiude senza salvare.
$ErrorActionPreference = 'Stop'
$qui = Split-Path -Parent $MyInvocation.MyCommand.Path
$attesi = Import-Csv (Join-Path $qui 'casi-attesi.csv') -Delimiter ';' -Encoding UTF8
$script:ok = 0; $script:errori = @()
function Controlla($nome, $ottenuto, $atteso) {
  if ("$ottenuto" -eq "$atteso") { $script:ok++ } else { $script:errori += "$nome : atteso '$atteso', ottenuto '$ottenuto'" }
}
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false; $xl.DisplayAlerts = $false
try {
  $wb = $xl.Workbooks.Open((Join-Path $qui 'campagna-ordini.xlsx'), 0, $true)
  $fLead = $wb.Worksheets.Item('Lead'); $fCrm = $wb.Worksheets.Item('CRM'); $fOrd = $wb.Worksheets.Item('Ordini')
  $fRie = $wb.Worksheets.Item('Riepilogo'); $fDec = $wb.Worksheets.Item('Da decidere'); $fCom = $wb.Worksheets.Item('Per i commerciali'); $fReg = $wb.Worksheets.Item('Regole')
  $n = $attesi.Count; $fine = 5 + $n
  function Ricalcola { $xl.CalculateFull() }
  function Lead($id) { for ($r = 6; $r -le 305; $r++) { if ($fLead.Cells.Item($r, 1).Value2 -eq $id) { return $r } } }
  function Esito($id) { $fLead.Cells.Item((Lead $id), 10).Value2 }
  function Attr($id) { [math]::Round([double]$fLead.Cells.Item((Lead $id), 13).Value2, 2) }
  function Righe($foglio) { $k = 0; for ($r = 6; $r -le 155; $r++) { if ("$($foglio.Cells.Item($r, 1).Value2)" -ne '') { $k++ } }; $k }
  function InLista($foglio, $id) { for ($r = 6; $r -le 155; $r++) { if ("$($foglio.Cells.Item($r, 1).Value2)" -eq $id) { return $true } }; $false }
  function Errori { $k = 0; foreach ($f in @($fLead, $fCrm, $fOrd, $fRie, $fDec, $fCom)) { foreach ($v in $f.UsedRange.Value2) { if ($v -is [int] -and $v -lt -2146826000) { $k++ } } }; $k }
  Ricalcola

  # 1. ogni caso: esito, importo attribuibile, permesso, e un perche' scritto
  foreach ($a in $attesi) {
    $r = Lead $a.ID
    Controlla "$($a.ID) esito ($($a.Caso))" $fLead.Cells.Item($r, 10).Value2 $a.Esito
    Controlla "$($a.ID) attribuibili ($($a.Caso))" ([math]::Round([double]$fLead.Cells.Item($r, 13).Value2, 2)) ([math]::Round([double]::Parse($a.Attribuibili, [Globalization.CultureInfo]::InvariantCulture), 2))
    Controlla "$($a.ID) permesso ($($a.Caso))" $fLead.Cells.Item($r, 15).Value2 $a.'Si può contattare'
    Controlla "$($a.ID) ha un perche'" ("$($fLead.Cells.Item($r, 11).Value2)".Length -gt 5) $true
  }
  # 2. il riepilogo quadra, nessun lead si perde, nessuna formula in errore
  for ($r = 10; $r -le 16; $r++) { if ("$($fRie.Cells.Item($r, 1).Value2)" -ne '') { Controlla "Riepilogo riga $r quadra" $fRie.Cells.Item($r, 11).Value2 'sì' } }
  Controlla 'totale lead' $fRie.Cells.Item(16, 2).Value2 $n
  foreach ($k in @(@(3, 'Da correggere'), @(4, 'Escluso'), @(5, 'Doppione'), @(6, 'Da decidere'), @(7, 'Già cliente'), @(8, 'Già in trattativa'), @(9, 'Tornato'), @(10, 'Nuovo'))) {
    Controlla "totale $($k[1])" $fRie.Cells.Item(16, $k[0]).Value2 (@($attesi | Where-Object { $_.Esito -eq $k[1] }).Count)
  }
  $somma = 0; foreach ($a in $attesi) { $somma += [double]::Parse($a.Attribuibili, [Globalization.CultureInfo]::InvariantCulture) }
  Controlla 'totale attribuibili' ([math]::Round([double]$fRie.Cells.Item(16, 13).Value2, 2)) ([math]::Round($somma, 2))
  foreach ($k in @(@(17, 53767.5, 'tutti gli ordini dopo, una volta sola'), @(14, 4000, 'di chi e'' tornato'), @(15, 21000, 'di clienti e trattative'), @(16, 6000, 'da decidere'))) { Controlla "totale $($k[2])" ([math]::Round([double]$fRie.Cells.Item(16, $k[0]).Value2, 2)) $k[1] }
  Controlla 'gli euro quadrano' $fRie.Cells.Item(16, 18).Value2 'sì'
  Controlla 'formule in errore' (Errori) 0
  # 3. le due liste
  Controlla 'righe Da decidere' (Righe $fDec) (@($attesi | Where-Object { $_.Esito -in 'Da decidere', 'Da correggere' }).Count)
  Controlla 'righe Per i commerciali' (Righe $fCom) (@($attesi | Where-Object { $_.'Si può contattare' -eq 'sì' -and $_.Esito -in 'Nuovo', 'Tornato', 'Già cliente', 'Già in trattativa' }).Count)
  foreach ($a in $attesi) { if ($a.'Si può contattare' -ne 'sì') { Controlla "$($a.ID) senza permesso non va ai commerciali" (InLista $fCom $a.ID) $false } }
  foreach ($a in $attesi) { if ($a.Esito -in 'Da decidere', 'Da correggere', 'Doppione', 'Escluso') { Controlla "$($a.ID) $($a.Esito) non va ai commerciali" (InLista $fCom $a.ID) $false } }

  for ($r = 6; $r -le 155; $r++) { if ($fCom.Cells.Item($r, 1).Value2 -eq 'L14') { Controlla 'L14 email tronca: segnalata' $fCom.Cells.Item($r, 5).Value2 'email da correggere' } }
  # 4. cambio un dato: si sposta solo quello che deve
  $r = Lead 'L02'; $fLead.Cells.Item($r, 9).Value2 = 'revocato'; Ricalcola
  Controlla 'revoca: L02 esce dalla lista' (InLista $fCom 'L02') $false; Controlla 'revoca: resta nei numeri' (Esito 'L02') 'Nuovo'
  $fLead.Cells.Item($r, 9).Value2 = 'sì'
  $primaOrdine = 6 + 0; for ($k = 6; $k -le 1005; $k++) { if ("$($fOrd.Cells.Item($k, 1).Value2)" -eq '') { $libera = $k; break } }
  $fOrd.Cells.Item($libera, 1).Value2 = 9001; $fOrd.Cells.Item($libera, 2).Value2 = [double]([datetime]'2026-04-01').ToOADate(); $fOrd.Cells.Item($libera, 3).Value2 = 'Corsi Tech'; $fOrd.Cells.Item($libera, 5).Value2 = 'aldo@corsitech.example'; $fOrd.Cells.Item($libera, 6).Value2 = 'Ordine'; $fOrd.Cells.Item($libera, 7).Value2 = 100; Ricalcola
  Controlla 'un ordine precedente: L02 diventa gia'' cliente' (Esito 'L02') 'Già cliente'
  $fOrd.Cells.Item($libera, 2).Value2 = [double]([datetime]'2026-06-20').ToOADate(); Ricalcola
  Controlla 'lo stesso ordine dopo: L02 nuovo' (Esito 'L02') 'Nuovo'; Controlla 'e attribuibile' (Attr 'L02') 100
  $fOrd.Cells.Item($libera, 6).Value2 = 'Annullato'; Ricalcola; Controlla 'annullato: attribuibile zero' (Attr 'L02') 0
  $fOrd.Range("A${libera}:H${libera}").ClearContents() | Out-Null
  $r = Lead 'L01'; for ($k = 6; $k -le 505; $k++) { if ("$($fCrm.Cells.Item($k, 1).Value2)" -eq '') { $lib = $k; break } }
  $fCrm.Cells.Item($lib, 1).Value2 = 'C900'; $fCrm.Cells.Item($lib, 2).Value2 = 'Bruni Macchine'; $fCrm.Cells.Item($lib, 4).Value2 = 'capo@brunimacchine.example'; $fCrm.Cells.Item($lib, 5).Value2 = 'Segnalazione'; $fCrm.Cells.Item($lib, 6).Value2 = 'Conti'; $fCrm.Cells.Item($lib, 7).Value2 = 'Trattativa aperta'; $fCrm.Cells.Item($lib, 8).Value2 = [double]([datetime]'2026-02-01').ToOADate(); Ricalcola
  Controlla 'trattativa aperta prima: L01' (Esito 'L01') 'Già in trattativa'; Controlla 'ordine non piu'' attribuibile' (Attr 'L01') 0
  Controlla 'chi lo segue resta' $fLead.Cells.Item($r, 14).Value2 'Conti'; Controlla 'la fonte originale resta' ("$($fLead.Cells.Item($r, 11).Value2)".Contains('Segnalazione')) $true
  $fCrm.Range("A${lib}:I${lib}").ClearContents() | Out-Null

  # 5. cambio una regola
  $fReg.Range('B4').Value2 = 210; Ricalcola; Controlla 'finestra 210: L36 ordine a 204 giorni' ([math]::Round([double]($attesi | Where-Object { $_.Caso -like 'Ordine dopo 204*' } | ForEach-Object { Attr $_.ID }), 2)) 5200
  $fReg.Range('B4').Value2 = 180; $fReg.Range('B5').Value2 = 100; Ricalcola; Controlla 'fermo da 100 giorni: il caso dei 180 giorni diventa Tornato' (Esito (($attesi | Where-Object { $_.Caso -like 'Ultimo ordine esattamente*' }).ID)) 'Tornato'
  $fReg.Range('B5').Value2 = 180
  $celle = $fReg.Range('C9:C28'); $vuota = $fReg.Range('C10'); $vuota.Value2 = 'corsitech.example'; Ricalcola; Controlla 'dominio interno aggiunto: L02 escluso' (Esito 'L02') 'Escluso'; $vuota.ClearContents() | Out-Null
  $fReg.Range('A9').Value2 = 'Altro nome'; Ricalcola; Controlla 'campagna tolta dall''elenco: i lead non si perdono' $fRie.Cells.Item(16, 2).Value2 $n; Controlla 'e il totale quadra' $fRie.Cells.Item(16, 11).Value2 'sì'; $fReg.Range('A9').Value2 = 'Fiera Bologna'; Ricalcola

  # 6. stessi dati in un altro ordine: stessi risultati
  $zona = $fLead.Range("A6:I$fine"); $copia = $zona.Value2
  for ($i = 1; $i -le $n; $i++) { for ($j = 1; $j -le 9; $j++) { $v = $copia[($n + 1 - $i), $j]; $cella = $fLead.Cells.Item(5 + $i, $j); if ($null -eq $v) { $cella.ClearContents() | Out-Null } elseif ($v -is [string]) { $cella.NumberFormat = '@'; $cella.Value2 = [string]$v } else { $cella.Value2 = [double]$v } } }
  Ricalcola
  foreach ($a in $attesi) { Controlla "$($a.ID) righe al contrario" (Esito $a.ID) $a.Esito }
  Controlla 'euro con le righe al contrario' $fRie.Cells.Item(16, 18).Value2 'sì'
  Controlla 'attribuibili con le righe al contrario' ([math]::Round([double]$fRie.Cells.Item(16, 13).Value2, 2)) ([math]::Round($somma, 2))
  # 7. manca un export intero
  $fOrd.Range('A6:H1005').ClearContents() | Out-Null; Ricalcola
  Controlla 'senza ordini: nessun importo' ([double]$fRie.Cells.Item(16, 17).Value2) 0; Controlla 'senza ordini: quadra' $fRie.Cells.Item(16, 11).Value2 'sì'; Controlla 'senza ordini: formule in errore' (Errori) 0
  $fCrm.Range('A6:I505').ClearContents() | Out-Null; $fLead.Range('A6:I305').ClearContents() | Out-Null; Ricalcola
  Controlla 'tutto vuoto: zero lead' $fRie.Cells.Item(16, 2).Value2 0; Controlla 'tutto vuoto: formule in errore' (Errori) 0
} finally {
  if ($wb) { $wb.Close($false) }
  $xl.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($xl)
}
$script:errori | ForEach-Object { Write-Output "DIVERSO  $_" }
Write-Output "$($script:ok) controlli superati, $($script:errori.Count) falliti"
