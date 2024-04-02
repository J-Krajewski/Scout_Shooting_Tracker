

## Running the Application

### To find out what process is running on port 5000

Find the Process:

Get-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess

Kill the Process:

Stop-Process -Id <ID>


# RBAC - Role Based Access Control 
- Giving certain user objects access to certain methods that only they can run
- Such only leader and dc, being able to run events 
- Scouts cannot run said methods as they cannot access the page but also their class posses no method to do so