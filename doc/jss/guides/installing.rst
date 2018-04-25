Installing
==========

.. with apologies to sheagcraig

Quick Start
-----------

The easiest method is to use pip to grab python-jss::

    $ pip install python-jss

However, if you use JSSImporter, its package installer uses easy_install since that is included on pre-10.10.5 OS X.
You may want to use easy_install instead::

    $ easy_install -U python-jss.

If you don't have pip, you should probably get it: https://pip.pypa.io/en/latest/installing.html

Alternately, download the source and copy the python-jss package wherever you normally install your packages.

Behind the scenes, python-jss requires the requests, pyasn1, and ndg-httpsclient packages.
If you install using easy-install or pip, these dependencies are handled for you.
Otherwise, you'll have to acquire them yourself::

    $ easy_install -U pyasn1 ndg-httpsclient requests



Linking to Homebrew OpenSSL
---------------------------

You can tell pip to use a previously installed OpenSSL inside your homebrew location like so:

Eg using 1.0.2k::

        pip install --global-option=build_ext \
            --global-option="-I/usr/local/Cellar/openssl/1.0.2k/include" \
            --global-option="-L/usr/local/Cellar/openssl/1.0.2k/lib" \
            pyopenssl



Linux
-----

python-jss on Linux has some extra dependencies if you need to be able to mount distribution points.

AFP distribution points require the ``fuse-afp`` package.
SMB distribution points require the ``cifs-utils`` package.
As I'm currently developing on Fedora, these requirements are specific to RedHat-based distros.
Feel free to test and comment on Debian so I can update!

