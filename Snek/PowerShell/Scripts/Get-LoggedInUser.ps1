# change our default settings for our remote session used by invoke-command
$PssOptions = New-PSSessionOption -MaxConnectionRetryCount 0 -OpenTimeout 10000 -OperationTimeout 30000

# command to run on remote computer
$ScriptBlock = { (Get-CimInstance -ClassName Win32_ComputerSystem).Username }

# invoke-command parameters
$Parameters = @{
    ComputerName	= PYTHON_COMPUTERNAME
    ScriptBlock		= $ScriptBlock
    ErrorAction		= "SilentlyContinue"
    WarningAction   = "SilentlyContinue"
    SessionOption	= $PssOptions
}

try {
    # run the command and save the result
    $User = Invoke-Command @Parameters
}
catch {
    $User = 'PS Error'
}
finally {
    # return the result
    $User
}
