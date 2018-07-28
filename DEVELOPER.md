# Developer Setup #

- Python dependencies are managed via `pipenv`.
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


## Debugging autopkg ##

### IntelliJ IDEA ###

Create a run configuration with the following details:

- *Script path*: `/usr/local/bin/autopkg`
- *Parameters*: `run -vv -k DISABLE_CODE_SIGNATURE_VERIFICATION=1 -k JSS_SUPPRESS_WARNINGS=False TextMate2.jss`
    
    Replace TextMate2.jss with a suitable test recipe.
- *Python Interpreter*: Make sure to use system python `/usr/bin/python`.
