import pytest
from jss.distribution_point import SMBDistributionPoint, AWS


class TestAFPDistributionPoint(object):
    pass


class TestSMBDistributionPoint(object):

    @pytest.mark.docker
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

    @pytest.mark.docker
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


class TestAWS(object):

    def test_aws(self, j, s3_bucket):
        aws_dp = AWS(
            jss=j,
            bucket=s3_bucket
        )

        aws_dp.copy_pkg("/Users/Shared/SkypeForBusinessInstaller-16.17.0.65.pkg")
