# Developer Setup #

- Create a virtualenv based on System Python.
- Activate the virtualenv.
- Install dependencies into the virtualenv by running `pip install -r requirements.txt`.
- Live tests are carried out by running a jss inside a `docker-jss` container.

## Symlinking the git repository into a live autopkg ##

Some care must be taken to symlink python-jss and JSSImporter into a live autopkg setup.

1. **JSSImporter** by default, will install into `/Library/AutoPkg/autopkglib`, so we must link a dev version into that
    directory. 
    
    If symlinking you will find that python will follow the link and break imports inside `JSSImporter.py`. For the moment
    I just append another PYTHONPATH to my checked-out JSSImporter git repo, like so:
    
        sys.path.insert(0, '/Library/Application Support/JSSImporter')
        sys.path.insert(0, '/path/to/python-jss')

2. If symlinking `python-jss` into `/Library/Application Support/JSSImporter` it must be a subdirectory named `jss`.
3. If you need to test against newer and/or different python-jss dependencies, you must run autopkg and tests from within
	a virtualenv.

## Running pytest ##

- Make sure your virtualenv is activated.
- Run `pytest` from within the python-jss directory, usually not everyone has the JCDS or CDP so you may also run:

		$ pytest --verbose -m "not docker and not jamfcloud and not s3"
		
to skip all the docker, jamfcloud and s3 tests.

You can see a list of available markers to skip by running:

		$ pytest --markers


*NOTE:* if you do run the docker tests, the first time you encounter a test that requires a new container, it will pull
down a new copy of that container, therefore the initial run time will be much longer.

To run specific groups of tests:

		$ pytest -m docker
		$ pytest -m jamfcloud
		$ pytest -m s3


### Testing with boto ###

Assuming you will create credentials for a test account, you should populate the file `~/.boto` with your access key
and secret key. See the [boto documentation](http://boto.cloudhackers.com/en/latest/boto_config_tut.html) for more 
information about how to supply credentials for use with S3.


### Testing with the NSURLSession Adapter ###

If your test JSS does not contain a valid certificate, the certificate trust will be automatically evaluated based on
your keychain, therefore you may have to trust the root CA of the test JSS prior to running tests that use NSURLSession.

## Debugging autopkg ##

### IntelliJ IDEA ###

Create a run configuration with the following details:

- *Script path*: `/usr/local/bin/autopkg`
- *Parameters*: `run -vv -k DISABLE_CODE_SIGNATURE_VERIFICATION=1 -k JSS_SUPPRESS_WARNINGS=False TextMate2.jss`
    
    Replace TextMate2.jss with a suitable test recipe.
- *Python Interpreter*: Make sure to use system python `/usr/bin/python`.
