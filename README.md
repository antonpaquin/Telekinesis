# Telekinesis
Allows secure creation and execution of scripts over a REST API

## What is this?
Telekinesis is a server that provides hosting and execution of simple shell scripts over a REST API. As an added bonus, it has a user and permission model that lets you control access to the scripts you make.

## What is it for?
It's for when you want to be able to run arbitrary commands over the web, without writing and setting up the entire CGI module that would traditionally let you do that.

Fun story: one day, I wrote a script for someone to port a mailing list from one service to another. He wasn't ready for it to run immediately, and he wasn't technical enough for me to just hand off the python file and be done with it, so we had to coordinate when I would run the script to migrate the lists. 

This scenario would have been easier if I had been able to just hand him a URL, saying "push this button when you're ready". This is the use case I had in mind when I designed Telekinesis.

# Setup
## Binary
You can try the binaries [located here](https://github.com/antonpaquin/Telekinesis/releases/tag/1.1)

For usage, see
```
./telekinesis -h
```

A simple setup running on port 8080 would be
```
./telekinesis -a admin -p mypassword --port 8080
```

## From source
(Requires python3, virtualenv)

First, clone and enter the repository
```
git clone https://github.com/antonpaquin/Telekinesis
cd Telekinesis
```

Set up the python virtual environment
```
virtualenv env -p python3
source env/bin/activate
```

Install requirements
```
pip install -r requirements.txt
```

And it's ready to run!
```
cd src
python run.py -a <admin username> -p <admin password> --port <what port to listen on>
```

Warning: if you're running this on a public network, I *highly* recommend using https. Otherwise, any password or session token you send can be sniffed, and you might be exposing your computer to arbitrary remote shell access, which is a very bad thing.

To protect your machine, you can run Telekinesis as an unprivileged user, or in a chroot jail, container, or virtual machine.

### Binaries from source

To build the binaries, we can use pyinstaller and the "/build/Telekinesis.spec" file

First, setup the virtualenv and install requirements as above.

Then, use pyinstaller to build the binary
```
cd build/
pyinstaller Telekinesis.spec
```
The results will be put in "build/dist/telekinesis"

# Usage

Valid options are:
- -c, --config
  - Allows the use of a config file to replace command line arguments. See an example [here](https://github.com/antonpaquin/Telekinesis/blob/master/src/telekinesis.conf.example)
- -a, --admin, "admin" (required)
  - The username of the default API admin account
- -p, --password, "password" (required)
  - The password of the default API admin account
- --log-dir, "log_dir"
  - Where to put the "telekinesis.log" log file. Defaults to the current directory.
- --data-dir, "data_dir"
  - Where to put database files for persistent storage. Defaults to the current directory.
- --port, "port"
  - What port to serve the API on. Defaults to 80
- --ssh, "ssh"
  - SSH into this target before executing scripts (see "Security")
- "run_as_user" (config file only)
  - Change into this user before executing scripts (see "Security")
- "run_as_password" (config file only)
  - Password for the "run_as_user" field
  
If any arguments are specified in a config file and in command line arguments, the command line arguments take priority.

A simple example, without any security options and serving on port 8080, is
```
./telekinesis -a administrator -p correct_horse_battery_staple --port 8080
```
  
# API
Note: the "/" endpoint returns [this file](https://github.com/antonpaquin/Telekinesis/blob/master/src/telekinesis/swaggerfile.json) which can be pasted into [this editor](https://editor.swagger.io/) (or fetched with swagger-ui) to generate docs.

## Scripts
Let's start out by creating a script under the admin user.
First, we log in as the admin (using 127.0.0.1 and port 8080 -- set these to wherever you're hosting)
```
curl -XPOST http://127.0.0.1:8080/login -d '{"username": "myuser", "password": "mypassword"}'
> {"session":"4c3cf5f7a7ab487abd01e4b0c7965f00"}
```
This token grants full access until the next time the user logs in, so keep it secret.

We'll save it to use in future calls
```
export COOKIE="session=4c3cf5f7a7ab487abd01e4b0c7965f00"
```

Now let's create a simple script
```
curl -b $COOKIE -XPUT http://127.0.0.1:8080/script -d '{"script": "echo Hello World!", "description": "Prints a simple message", "fork": "False"}'
> {"description":"Prints a simple message","fork":false,"public_token":"d4c84e3ef1ac440b936f7b924415e065","script":"echo Hello World!","script_id":1}
```
We get back a new script with the info we sent it, a "script_id", and a "public_token".

Let's call that script with the script ID to see what it gives us
```
curl -b $COOKIE -XPOST http://127.0.0.1:8080/script/1
> {"exit_status":0,"pid":11467,"stderr":"","stdout":"Hello World!\n"}
```
We can see it printed "Hello World!" to stdout and exited successfully.

Now say I want to send that script to my friend so he can run it.
I'll send him the URL with the public token
```
http://127.0.0.1:8080/script/1/d4c84e3ef1ac440b936f7b924415e065
```
(Note: You'd need to be serving on a publicly accessible host and port for your friend to reach the server. 127.0.0.1 would not work from another machine)

And my friend can call and see the results of the script by POSTing that URL
```
curl -XPOST http://127.0.0.1:8080/script/1/d4c84e3ef1ac440b936f7b924415e065
> {"exit_status":0,"pid":11470,"stderr":"","stdout":"Hello World!\n"}
```

## Users
Let's say I trust my friend with my machine, and I want to give him the ability to write scripts on his own.

We'll create the user:
```
curl -b $COOKIE -XPUT http://127.0.0.1:8080/user -d '{"username": "myfriend", "password": "newpassword"}'
```
(Sorry, password change endpoint is not written yet. Put an issue in this repo if you would like this feature)

This default user can't do anything, so let's give him the "script.create" permission
```
curl -b $COOKIE -XPUT http://127.0.0.1:8080/permission -d '{"username": "myfriend", "permission": "script.create"}'
```
Now he can create his own scripts, and he'll have full access to anything he creates.

## Permissions

Valid permissions are:
- script.create
  - Allows creating new scripts (creating a script automatically grants read, update, execute, and destroy on that script)
- script.read.[x]
  - Allows reading the script with ID [x]
  - Note: read permission on the script will show the user the public token for the script, which by default has read and execute. These default permissions can be removed (see below).
- script.update.[x]
  - Allows changing a script, 
  - Also allows granting permissions you have on that script to other users
- script.execute.[x]
  - Allows execution of a script
- script.destroy.[x]
  - Allows deletion of a script
- scripts.read
  - Allows reading all scripts at once
  - Recommended only for administrators
- user.create
  - Allows creation of new users
- user.read
  - Allows read access of permissions on any user
  - Even without, you can always read yourself
- user.destroy
  - Allows deleting users
  - Even without, you can always delete yourself
- permission.create
  - Allows adding any permission to any user (administrator)
  - Even without, you can always grant script.(*).[x] to any user for any script where you have script.update.[x] and the granted permission
- permission.destroy
  - Allows removing any permission from any user (administrator)
  - Even without, you can always remove script.(*).[x] from the autogenerated public users for any script where you have script.update.[x]

When a script is created, the user "#script.public.[x]" is automatically created and given script.read.[x] and script.execute.[x] on that script. This user is only accessible via the public token created and stored in the script's "public_token" field (which is visible to anyone with "script.read.[x]" or "scripts.read").

If you do not want this script to be publicly accessible, you can ignore the "public_token" field, or remove these permissions with
```
curl -b $COOKIE -XDELETE http://127.0.0.1:8080/permission -d '{"username": "#script.public.[x]", "permission": "script.execute.[x]"}'
curl -b $COOKIE -XDELETE http://127.0.0.1:8080/permission -d '{"username": "#script.public.[x]", "permission": "script.read.[x]"}'
```

# Security

If you run telekinesis with the default options, user scripts will be able to run anything that the user who starts the program can. This means they can do things like delete your home directory, or add a keylogger to your bashrc.

If you keep "script.update" and "script.create" private, then you're safe. Otherwise, you should consider using one of the two available isolation methods to prevent user scripts from doing evil things.

## User Isolation

If "run_as_user" and "run_as_password" are set in a config file, telekinesis will change to that user before executing commands. You can take advantage of this to create an unprivileged user, who will not be able to damage the local machine.

To create an unprivileged user "telekinesis", run
```
sudo useradd telekinesis
sudo passwd telekinesis
```

Make sure the "other" system permissions are set to prevent access to private files
```
# Remove read permission from other users
chmod o-r my_file
# Remove write permission from other users
chmod o-w my_file
```
Which will prevent those files from being read or changed by a telekinesis script.

## SSH Isolation

You can tell telekinesis to SSH into another machine before executing any scripts. This can be used to run commands on a local container or a remote machine where malicious users can do no harm, or to a different user on the local machine. 

Any arguments you specify in the "ssh" parameter will be appended to
```ssh -T```
and run to generate a shell. You should use an identity file to enable passwordless login, and should also consider adding the host to your ssh config.

An example SSH config might contain:
```
host telekinesis_executor
  HostName 192.168.0.110
  port 22
  User telekinesis
  IdentityFile ~/.ssh/my_ssh_.key
```
And the remote host should contain the public key in its "~/.ssh/authorized_keys" file.

With this setup, specifying
```
{
  ...
  "ssh": "telekinesis_executor"
}
```
would be sufficient to trigger commands on the remote machine.
