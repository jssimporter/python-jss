Developer Guide
===============

Installing PyOpenSSL linked with Homebrew
-----------------------------------------

Eg using 1.0.2k::

        pip install --global-option=build_ext \
            --global-option="-I/usr/local/Cellar/openssl/1.0.2k/include" \
            --global-option="-L/usr/local/Cellar/openssl/1.0.2k/lib" \
            pyopenssl


