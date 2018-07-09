#! /bin/bash

# Depends: the CLI JSON processing utility "jq"


# First, we log in with the default credentials set when we run the server
SESSION="$(curl -s -XPOST http://localhost:5555/login -d '
    {
        "username": "anton",
        "password": "anton"
    }
' | jq .session)"

# Start by creating a new script to echo "hello world!", and save the response
SCRIPT=$(curl -s -b session=$SESSION -XPUT http://localhost:5555/script -d '
    {
        "script": "echo \"hello world!\"",
        "description": "prints hello world",
        "fork": "false"
    }
')
# Pull the script ID out of the response
SCRIPT_ID=$(SCRIPT="$SCRIPT" echo $SCRIPT | jq .script_id)

# Now let's try running the script
curl -s -b session=$SESSION -XPOST http://localhost:5555/script/$SCRIPT_ID
# The response should look something like:
# {"exit_status":0,"pid":16210,"stderr":"","stdout":"hello world!\n"}

# Change the output to say something else
curl -s -b session=$SESSION -XPATCH http://localhost:5555/script/$SCRIPT_ID -d '
    {
        "script": "echo \"something else\""
    }
'

# And run it again
curl -s -b session=$SESSION -XPOST http://localhost:5555/script/$SCRIPT_ID
# Now the response should look like
# {"exit_status":0,"pid":16217,"stderr":"","stdout":"something else\n"}

# We can generate a shareable link to this script with READ and EXECUTE permissions
PUBLIC_TOKEN=$(SCRIPT="$SCRIPT" echo $SCRIPT | jq -r .public_token)

# And run as the public user
curl -s -XPOST http://localhost:5555/script/$SCRIPT_ID/$PUBLIC_TOKEN
# {"exit_status":0,"pid":19114,"stderr":"","stdout":"something else\n"}

# Delete the script to clean up
curl -s -b session=$SESSION -XDELETE http://localhost:5555/script/$SCRIPT_ID
