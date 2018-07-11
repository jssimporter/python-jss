Distribution Points
===================

.. automodule:: jss.distribution_point

.. inheritance-diagram:: jss.distribution_point
    :top-classes: jss.distribution_point.Repository


Architecture
------------

- **FileRepository** is the base class for all types of Distribution Point that require mounting.
- **DistributionServer** is the base class for all legacy Distribution Point types that used the dbfileupload API to upload
    and check for the existence of package(s).
- **CloudDistributionServer** is the base class for all newer Distribution Point types that upload directly to their cloud
    API counterparts.

Constructors
------------

Each class takes a **kwargs** object that describes the parameters needed for connection to the respective Distribution
Point. This varies greatly by the class that is being instantiated.

Classes
-------

.. toctree::
    :maxdepth: 2

    distribution_points.rst
    file_repository.rst
    mounted_repository.rst
    afp_dp.rst
    smb_dp.rst
    distribution_server.rst
    cdp.rst
    jds.rst
    jcds


