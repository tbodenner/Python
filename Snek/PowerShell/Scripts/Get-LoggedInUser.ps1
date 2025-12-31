<#
try {
    # change our default settings for our remote session used by invoke-command
    $PssOptions = New-PSSessionOption -MaxConnectionRetryCount 0 -OpenTimeout 10000 -OperationTimeout 30000

    # command to run on remote computer
    $ScriptBlock = { (Get-CimInstance -ClassName Win32_ComputerSystem).Username }

    # invoke-command parameters
    $Parameters = @{
        ComputerName      = "PYTHON_COMPUTERNAME"
        ScriptBlock       = $ScriptBlock
        ErrorAction       = "SilentlyContinue"
        WarningAction     = "SilentlyContinue"
        SessionOption     = $PssOptions
    }

    # run the command and save the result
    $User = Invoke-Command @Parameters
}
catch {
    $User = 'Error'
}

# change any disconnects to errors
if (($User | Out-String) -like "*WARNING*") {
    $User = 'Error'
}

# return the result
$User
#>

# try to get our logged in user
try {
    # use quser to get the logged in user
    $QResult = quser.exe /SERVER:"PYTHON_COMPUTERNAME"

    # check if we received a result
    if (($null -eq $QResult) -or ($QResult -eq "")) {
        # return an empty string if we had no result
        ''
    }
    else {
        # otherwise, check if our result has two or more lines
        if ($QResult.Length -ge 2) {
            # get our user from our second line
            $User = $QResult[1].Substring(1,12)
            # return our user
            $User
        }
        else {
            # if we didn't receive enough lines, return an empty string
            ''
        }
    }
}
catch {
    # on any errors, return an error
    'Error'
}
