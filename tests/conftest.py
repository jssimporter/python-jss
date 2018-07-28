import pytest
import plistlib
import os
from jss import JSSPrefs, JSS
from xml.etree import ElementTree
from subprocess import call
import boto
from boto.s3.connection import S3Connection
from boto.s3.bucket import Bucket


JSS_PREFS = {
    'jss_url': 'https://localhost:8444',
    'jss_user': 'admin',
    'jss_password': 'P@ssw0rd',
    'verify': False,
    'suppress_warnings': False,
    'repos': [],
}

JAMFCLOUD_PREFS = {
    'jss_url': os.environ.get('JAMFCLOUD_URL'),
    'jss_user': os.environ.get('JAMFCLOUD_USER'),
    'jss_password': os.environ.get('JAMFCLOUD_PASSWORD'),
    'verify': False,
    'suppress_warnings': False,
    'repos': [],
}


@pytest.fixture
def jss_prefs_dict():  # type: () -> dict
    return JSS_PREFS


@pytest.fixture
def cloud_jss_prefs_dict():  # type: () -> dict
    return JAMFCLOUD_PREFS


@pytest.fixture
def jss_prefs_file(tmpdir):  # type: () -> str
    prefs_path = tmpdir.join('com.github.sheagcraig.python-jss.plist')
    plistlib.writePlist(JSS_PREFS, prefs_path)
    return prefs_path


@pytest.fixture
def jss_prefs(jss_prefs_file):  # type: (str) -> JSSPrefs
    prefs = JSSPrefs(preferences_file=jss_prefs_file)
    return prefs


@pytest.fixture
def j(jss_prefs_dict):  # type: (dict) -> JSS
    o = JSS(
        url=jss_prefs_dict['jss_url'],
        user=jss_prefs_dict['jss_user'],
        password=jss_prefs_dict['jss_password'],
        ssl_verify=jss_prefs_dict['verify'],
    )
    return o


@pytest.fixture
def cloud_j(cloud_jss_prefs_dict):  # type: (dict) -> JSS
    o = JSS(
        url=cloud_jss_prefs_dict['jss_url'],
        user=cloud_jss_prefs_dict['jss_user'],
        password=cloud_jss_prefs_dict['jss_password'],
        ssl_verify=cloud_jss_prefs_dict['verify'],
    )
    return o


@pytest.fixture
def etree_building():  # type: () -> ElementTree.Element
    building = ElementTree.Element('building')
    name = ElementTree.SubElement(building, 'name')
    name.text = 'Fixture Building'
    # id = ElementTree.SubElement(building, 'id')
    # id.text = '0'
    
    return building


@pytest.fixture
def package():  # type: () -> JSS.Package
    pass

# def is_afp_responsive(afpurl):
#     """Check if something responds to ``url``."""
#     pass


def is_smb_responsive(smburl):
    """Check if something responds to ``url``."""
    status = call(['/usr/bin/smbutil', 'view', smburl])
    return status == 0


@pytest.fixture
def dp_smb_ip_port(docker_ip, docker_services):
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.1,
        check=lambda: is_smb_responsive("//jss:jss@%s:%s" % (docker_ip, docker_services.port_for('samba', 139)))
    )
    return docker_ip, docker_services.port_for('samba', 139)


# @pytest.fixture
# def dp_afp_url(docker_ip, docker_services):
#     afp_url = 'afp://%s:%s/distribution_point' % (
#         docker_ip,
#         docker_services.port_for('afp', 549),
#     )
#     docker_services.wait_until_responsive(
#         timeout=30.0, pause=0.1,
#         check=lambda: is_afp_responsive(afp_url)
#     )
#     return afp_url

@pytest.fixture
def uapi_token(jss_prefs_dict, j):
    response = j.post('uapi/auth/tokens', data={})
    json_data = response.json()


@pytest.fixture
def pkg_path():
    return os.path.abspath("testdata/Microsoft_Outlook_2016_16.15.18070902_Installer.pkg")


@pytest.fixture
def s3_connection():
    # calling_format is passed because i use a bucket with periods which normally raises a CertificateError
    # see: https://github.com/boto/boto/issues/2836
    return boto.s3.connect_to_region('ap-southeast-2', calling_format=boto.s3.connection.OrdinaryCallingFormat())
    #return S3Connection(calling_format=boto.s3.connection.OrdinaryCallingFormat())


@pytest.fixture
def s3_bucket(s3_connection):  # type: (S3Connection) -> Bucket
    return s3_connection.get_bucket('python-jss-pytest')
