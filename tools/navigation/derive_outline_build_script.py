"""Keep the existing V9/V10 builder intact; emit an outline-specific contract."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
text=(ROOT/'tools/navigation/build_foundation_package.ps1').read_text()
start=text.index("if($receipt.status -ne 'FOUNDATION_STAGED_WITH_STALE_BOOTSTRAP_NAVIGATION')")
end=text.index('$sourceItems=@(')
replacement='''if($receipt.status -ne 'OUTLINE_STAGED_FOR_DATA_SERVER_WITH_STALE_NAVIGATION') { throw 'Verified outline stage required' }
if($receipt.precision_contract -ne 'native-outline-frozen' -or $receipt.exact_native_persistence -ne $true) { throw 'Wrong precision contract' }
$expectedAsc=$receipt.asc_sha256
if((Get-FileHash -LiteralPath $receipt.asc -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedAsc) {throw 'ASC changed'}
if((Get-FileHash -LiteralPath $receipt.offline_proof -Algorithm SHA256).Hash.ToLowerInvariant() -ne $receipt.offline_proof_sha256) {throw 'Offline proof changed'}
$offline=Get-Content -LiteralPath $receipt.offline_proof -Raw | ConvertFrom-Json
if($offline.status -ne 'PASS_OFFLINE_OUTLINE_GEOMETRY' -or $offline.candidate_sha256 -ne $expectedAsc -or @($offline.checks.PSObject.Properties | Where-Object {$_.Value -ne $true}).Count) {throw 'Offline proof scope mismatch'}
$expectedWater='f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3'
$expectedNm='eb0f131e5fc0f80d81c60b1f332d8ecfa6396cab9e09ffd36cd1c8504885c496'
if(@($receipt.native_exports).Count -ne 2){throw 'Two complete native gates required'}
foreach($gate in $receipt.native_exports) {
    if($gate.status -ne 'PASS_NATIVE_ROAD_TERRAIN_CONTENT' -or $gate.asc_sha256 -ne $expectedAsc -or @($gate.checks.PSObject.Properties | Where-Object {$_.Value -ne $true}).Count) {throw 'Native proof scope mismatch'}
    if((Get-FileHash -LiteralPath $gate.wrp -Algorithm SHA256).Hash.ToLowerInvariant() -ne $gate.wrp_sha256) {throw 'Native export changed'}
}
'''
text=text[:start]+replacement+text[end:]
target=ROOT/'tools/navigation/build_outline_package.ps1';assert not target.exists();target.write_text(text);print(target)
