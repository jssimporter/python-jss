import pytest
from jss.distribution_point import SMBDistributionPoint


class TestAFPDistributionPoint(object):
    pass


class TestSMBDistributionPoint(object):

    @pytest.mark.dockertest
    def test_mount(self, dp_smb_ip_port, tmpdir, j):
        smb_ip, smb_port = dp_smb_ip_port
        
        dp = SMBDistributionPoint(
            url=smb_ip,
            port=str(smb_port),
            mount_point=tmpdir.strpath,
            username='jss',
            password='jss',
            share_name='distribution_point',
            domain='WORKGROUP',
            jss=j,
        )
        dp.mount()
        assert dp.is_mounted()

        dp.umount()

    @pytest.mark.dockertest
    def test_copy_pkg(self, dp_smb_ip_port, tmpdir, j):
        smb_ip, smb_port = dp_smb_ip_port

        dp = SMBDistributionPoint(
            url=smb_ip,
            port=str(smb_port),
            mount_point=tmpdir.strpath,
            username='jss',
            password='jss',
            share_name='distribution_point',
            domain='WORKGROUP',
            jss=j,
        )
        #dp.copy_pkg()


class TestLocalRepository(object):
    pass


class TestCDP(object):
    pass


