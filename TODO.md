*Not really sure whether I need a raw_get and a get.
	*I guess raw_get could be useful if you wanted to hand write a get url, or
	for interactive testing.
	*python_gitlab only has a Connection exception for rawget

*All of my methods utilizing requests are in a while loop to avoid the errors I
	get when hitting the server really fast.  
	*Can this code (and exception testing) be factored out?  
	*Alternately, it could be added where it is expected to be needed, which
	for the wrapper is nowhere. This has just been a problem with me doing my
	policies_for_group search, which pulls every full policy down afap.

*Remove try/except and while loop from rawget.