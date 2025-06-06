$SearchBase = "OU=VISN18,DC=v18,DC=med,DC=va,DC=gov"
$Filter = "Name -like 'PRE-*'"
$ComputerNames = (Get-ADComputer -Filter $Filter -SearchBase $SearchBase | Where-Object { $_.Enabled -eq $true }).Name
$ComputerNames