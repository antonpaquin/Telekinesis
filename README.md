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
You can try the binaries [located here](https://github.com/antonpaquin/Telekinesis/releases/tag/1.0)

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

To protect your machine, you can run Telekinesis as an unprivileged user, 

# Usage

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
