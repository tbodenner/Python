$RequiredModuleName = 'LDAP-ADTools'
if($null -eq (Get-Module -Name $RequiredModuleName -ListAvailable)) {
    exit
}
Import-Module $RequiredModuleName -Scope Local
$Filter = 'PRE-*'
$ADComputersHashtable = Get-LDAPComputer -RootOU $Global:MyRootOU -Computers $Filter -Properties 'useraccountcontrol'
$EnabledComputersHashtable = @{}
foreach ($Key in $ADComputersHashtable.Keys) {
    if ($ADComputersHashtable[$Key]['useraccountcontrol'] -eq 4096) { 
        $EnabledComputersHashtable[$ADComputersHashtable[$Key]['name']] = ''
    }
}
$EnabledComputersHashtable.Keys