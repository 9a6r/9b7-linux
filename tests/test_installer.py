from dataclasses import replace
from pathlib import Path
import unittest
from unittest.mock import patch
from nineb7.installer import InstallConfig, disks, install


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.config = InstallConfig('/dev/vda', 'student', 'New-testing-password', confirmation='ERASE /dev/vda')

    def test_explicit_identity_disk_and_confirmation(self):
        self.assertIs(self.config.validate(), self.config)
        for change in ({'disk':'/dev/../sda'}, {'username':'root'}, {'username':'9b7'}, {'username':'bad;name'},
                       {'password':'9b7'}, {'password':'a\nbcdefghi'}, {'confirmation':'ERASE /dev/sda'},
                       {'hostname':'pc;command'}, {'timezone':'../../etc/passwd'}, {'session':'shell;command'},
                       {'keyboard':'us"\ncommand'}):
            with self.subTest(change={k:v for k,v in change.items() if k!='password'}):
                with self.assertRaises(ValueError): replace(self.config, **change).validate()
        self.assertNotIn(self.config.password, repr(self.config))

    def test_bad_configuration_cannot_execute_disk_command(self):
        with patch('nineb7.installer.run') as run, patch('nineb7.installer.validate_target') as validate:
            with self.assertRaises(ValueError): install(replace(self.config, confirmation=''))
            run.assert_not_called(); validate.assert_not_called()

    def test_mounted_child_and_read_only_devices_are_identified(self):
        raw = '{"blockdevices":[{"name":"/dev/vda","type":"disk","size":85899345920,"ro":false,"mountpoints":[null],"children":[{"name":"/dev/vda1","mountpoints":["/run/archiso/bootmnt"]}]},{"name":"/dev/vdb","type":"disk","size":85899345920,"ro":false,"mountpoints":[null]},{"name":"/dev/loop0","type":"loop","mountpoints":[null]}]}'
        with patch('subprocess.check_output', return_value=raw):
            result = disks()
        self.assertEqual(len(result), 2); self.assertTrue(result[0]['mounted']); self.assertFalse(result[1]['mounted'])


if __name__ == '__main__': unittest.main()
