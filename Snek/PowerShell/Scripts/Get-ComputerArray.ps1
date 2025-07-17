$Domains = @('va.gov', 'v18.med.va.gov')
$Filter = "Name -like 'PRE-*'"
$ComputerNames = @()
foreach ($Domain in $Domains) {
    $Server = Get-ADDomainController -Discover -DomainName $Domain
    $ComputerNames += (Get-ADComputer -Filter $Filter -Server $Server | Where-Object { $_.Enabled -eq $true }).Name
}
$ComputerNames