*Should I make class Policy, etc, into private?
*__dict__ is a special class property which allows you to see all instance
variables as a dictionary of k=variable name, v=value. I don't see keeping
anything else there, but the python-gitlab code does, so I want to remember it
as an option if I get stuck and can't figure out how I'm jacking stuff up.
*Add sorting options for listing operations in jss_helper