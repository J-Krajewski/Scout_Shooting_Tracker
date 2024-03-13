

## Running the Application

### To find out what process is running on port 5000

Find the Process:

Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess

Kill the Process:

Stop-Process -Id <ID>

