# About
This is a simple keyword matching script.
It opens a never ending loop in a terminal where one can search for questions that one has written the answer to, through the use of keywords.

The api_server and Dockerfile are not functional. They were just written as an starter point of its possible use.

# Relase
Release versions in GitHub have the latest code as well as a downabable zip with the data_qa folder with all the required content

# Commands
## q
q: Write q followed by keywords that are searched

q -n=[n]: insert in [n] the amount of results that should be printed. Default is set to 4

q -t: Limit a search to only a given a topic

q -a: Search for a keyword not only in the questions but also in the answers

### Examples
Search for questions with 'new'
    q new

Give the top 6 results of searching for 'new'
    q -n=6 new

Search for questions with 'new' but only for the topic 'git'
    q -t git -q new

Search for answers that includes 'rake'
    q -a rake

### Notes
Giving a feedback to a keyword searched with -a will add the keyword to the weight of the question even if that keyword is not present in the question.
This will make a query that was not findable as 'q rake' be make so that it will now be.

A mixed search with both -q and -a might not work as intended

## f
Provide feedback.
    f -[n] +/-

Define with the [n] which of the results from the query the feedback will apply to.

This action is only possible on the last query explicetly written with q ...

Only the weights of those words that have been put on the q search will be updated.

Putting + will increase each weight by 0.2
Putting - will decrease each weight by 0.2

# License
This project is licensed under the MIT License.

Read the full license here: [MIT License](LICENSE)