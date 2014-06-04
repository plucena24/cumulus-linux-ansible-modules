from mock import MagicMock
import mock
from nose.tools import set_trace
from dev_modules.cl_img_install import check_url,\
    get_slot_info, main, switch_slots, install_img, \
    check_sw_version, active_sw_version
from asserts import assert_equals


def mod_args(arg):
    values = {'version': '2.0.0',
              'src': 'http://10.1.1.1/cl.bin',
              'switch_slots': 'yes'}
    return values[arg]


def slot_info():
    return {
        '1': {'version': '2.0.0'},
        '2': {'version': '2.0.2',
              'primary': True}
    }

@mock.patch('dev_modules.cl_img_install.AnsibleModule')
def test_get_slot_info(mock_module):
    """ Test getting slot information. """
    instance = mock_module.return_value
    oniefile = open('tests/u-boot-env.txt')
    slots = slot_info()
    with mock.patch('__builtin__.open') as mock_open:
        mock_open.return_value = oniefile
        assert_equals(get_slot_info(instance), slots)
        mock_open.assert_called_with('/mnt/root-rw/onie/u-boot-env.txt')

def active_sw_open(arg):
    lsb_release = open('tests/lsb-release.txt')
    proc_cmdline = open('tests/proc_cmdline.txt')
    values = {'/etc/lsb-release': lsb_release,
              '/proc/cmdline': proc_cmdline}
    return values[arg]

@mock.patch('__builtin__.open')
def test_getting_active_ver(mock_open):
    """ Test getting active version"""
    slots  = slot_info()
    assert_equals(slots['2']['version'], '2.0.2')
    active_sw_version(MagicMock(), slots)
    assert_equals(slots['2']['version'], '2.0.3')
    assert_equals(slots['2']['active'], True)


@mock.patch('dev_modules.cl_img_install.active_sw_version')
@mock.patch('dev_modules.cl_img_install.AnsibleModule')
@mock.patch('dev_modules.cl_img_install.get_slot_info')
def test_sw_version_switch_slots_no_ver_on_active_slot(mock_slot_info,
                                                       mock_module,
                                                       mock_active_sw):
    "Check if software is installed, switch slots no, version on active slot"
    ver = '2.0.0'
    mock_active_sw.return_value = ver
    instance = mock_module.return_value
    instance.params.get.return_value = 'no'
    mock_slot_info.return_value = slot_info()
    check_sw_version(instance, ver)
    _msg = 'Version %s is installed in the active slot' % (ver)
    instance.exit_json.assert_called_with(msg=_msg, changed=False)

@mock.patch('dev_modules.cl_img_install.active_sw_version')
@mock.patch('dev_modules.cl_img_install.AnsibleModule')
@mock.patch('dev_modules.cl_img_install.get_slot_info')
def test_sw_version_switch_slots_yes_ver_on_active_slot(mock_slot_info,
                                                        mock_module,
                                                        mock_active_sw):
    "Check if software is installed, switch slots yes, version on active slot"
    instance = mock_module.return_value
    instance.params.get.return_value = 'yes'
    mock_slot_info.return_value = slot_info()
    ver = '2.0.0'
    check_sw_version(instance, ver)
    _msg = 'Version %s is installed in the active slot' % (ver)
    instance.exit_json.assert_called_with(msg=_msg, changed=False)


@mock.patch('dev_modules.cl_img_install.active_sw_version')
@mock.patch('dev_modules.cl_img_install.run_cl_cmd')
@mock.patch('dev_modules.cl_img_install.AnsibleModule')
@mock.patch('dev_modules.cl_img_install.get_slot_info')
def test_sw_version_switch_slots_yes_ver_on_adj_slot_primary(mock_slot_info,
                                                             mock_module,
                                                             mock_run_cl_cmd,
                                                             mock_active_sw):
    "Check if software is installed, switch slots yes, "
    "version on adj slot, adj slot is primary"
    instance = mock_module.return_value
    instance.params.get.return_value = 'yes'
    _slot_info = {
        '1': {'version': '2.0.0',
              'active': True},
        '2': {'version': '2.0.2',
              'primary': True},
    }

    mock_slot_info.return_value = _slot_info
    ver = '2.0.2'
    check_sw_version(instance, ver)
    _msg = "Version " + ver + " is installed in the alternate slot. " + \
        "Next reboot, switch will load " + ver + "."
    instance.exit_json.assert_called_with(msg=_msg, changed=False)
    assert_equals(mock_run_cl_cmd.call_count, 0)

@mock.patch('dev_modules.cl_img_install.active_sw_version')
@mock.patch('dev_modules.cl_img_install.run_cl_cmd')
@mock.patch('dev_modules.cl_img_install.AnsibleModule')
@mock.patch('dev_modules.cl_img_install.get_slot_info')
def test_sw_version_switch_slots_yes_adj_slot_not_primary(mock_slot_info,
                                                          mock_module,
                                                          mock_run_cl_cmd,
                                                          mock_active_sw):
    """"
    Check if software is installed, switch slots yes,
    version on adj slot, adj slot is not primary
    """
    instance = mock_module.return_value
    instance.params.get.return_value = 'yes'
    _slot_info = {
        '1': {'version': '2.0.0',
              'active': True,
              'primary': True},
        '2': {'version': '2.0.2'}
    }

    mock_slot_info.return_value = _slot_info
    ver = '2.0.2'
    check_sw_version(instance, ver)
    _msg = "Version " + ver + " is installed in the alternate slot. " + \
        "cl-img-select has made the alternate slot the primary slot. " + \
        "Next reboot, switch will load " + ver + "."
    instance.exit_json.assert_called_with(msg=_msg, changed=True)
    assert_equals(mock_run_cl_cmd.call_count, 1)
    mock_run_cl_cmd.assert_called_with(instance,
                                       '/usr/cumulus/bin/cl-img-select 2')

@mock.patch('dev_modules.cl_img_install.active_sw_version')
@mock.patch('dev_modules.cl_img_install.run_cl_cmd')
@mock.patch('dev_modules.cl_img_install.AnsibleModule')
@mock.patch('dev_modules.cl_img_install.get_slot_info')
def test_sw_version_switch_slots_no_ver_not_primary(mock_slot_info,
                                                    mock_module,
                                                    mock_run_cl_cmd,
                                                    mock_active_sw):
    """
    Check if software is installed, switch slots
    no, version on adj slot, adj slot is not primary
    """
    instance = mock_module.return_value
    instance.params.get.return_value = 'no'
    _slot_info = {
        '1': {'version': '2.0.0',
              'active': True,
              'primary': True},
        '2': {'version': '2.0.2'}
    }
    mock_slot_info.return_value = _slot_info
    ver = '2.0.2'
    check_sw_version(instance, ver)
    _msg = "Version " + ver + " is installed in the alternate slot. " + \
        "Next reboot will not load " + ver + ". " + \
        "switch_slots keyword set to 'no'."

    instance.exit_json.assert_called_with(msg=_msg, changed=False)
    assert_equals(mock_run_cl_cmd.call_count, 0)


@mock.patch('dev_modules.cl_img_install.active_sw_version')
@mock.patch('dev_modules.cl_img_install.run_cl_cmd')
@mock.patch('dev_modules.cl_img_install.AnsibleModule')
@mock.patch('dev_modules.cl_img_install.get_slot_info')
def test_sw_version_switch_slots_yes_ver_not_found(mock_slot_info,
                                                   mock_module,
                                                   mock_run_cl_cmd,
                                                   mock_active_sw):
    "Check if software is installed, switch slots yes, no ver found"
    instance = mock_module.return_value
    instance.params.get.return_value = 'yes'
    _slot_info = {
        '1': {'version': '2.0.0',
              'active': True,
              'primary': True},
        '2': {'version': '2.0.2'}
    }
    mock_slot_info.return_value = _slot_info
    ver = '2.0.3'
    check_sw_version(instance, ver)
    assert_equals(instance.exit_json.call_count, 0)
    assert_equals(mock_run_cl_cmd.call_count, 0)

@mock.patch('dev_modules.cl_img_install.active_sw_version')
@mock.patch('dev_modules.cl_img_install.run_cl_cmd')
@mock.patch('dev_modules.cl_img_install.AnsibleModule')
@mock.patch('dev_modules.cl_img_install.get_slot_info')
def test_sw_version_switch_slots_no_ver_not_found(mock_slot_info,
                                                  mock_module,
                                                  mock_run_cl_cmd,
                                                  mock_active_sw):
    "Check if software is installed, switch slots no, no ver found"
    instance = mock_module.return_value
    instance.params.get.return_value = 'no'
    _slot_info = {
        '1': {'version': '2.0.0',
              'active': True,
              'primary': True},
        '2': {'version': '2.0.2'}
    }
    mock_slot_info.return_value = _slot_info
    ver = '2.0.3'
    check_sw_version(instance, ver)
    assert_equals(instance.exit_json.call_count, 0)
    assert_equals(mock_run_cl_cmd.call_count, 0)


@mock.patch('dev_modules.cl_img_install.AnsibleModule')
def test_check_url(mock_module):
    """
    Test to see that image install url is properly defined
    """
    src = 'http://10.1.1.1/image.bin'
    assert_equals(check_url(mock_module, src), True)
    assert_equals(mock_module.fail_json.call_count, 0)
    src = '/home/my/image.bin'
    assert_equals(check_url(mock_module, src),  True)
    assert_equals(mock_module.fail_json.call_count, 0)
    src = 'https://10.1.1.1/sdfdf.bin'
    assert_equals(check_url(mock_module, src),  True)
    assert_equals(mock_module.fail_json.call_count, 0)
    src = 'ftp://sdfdf.bin'
    _msg = 'Image Path URL. Wrong Format %s' % (src)
    assert_equals(check_url(mock_module, src),  False)
    mock_module.fail_json.assert_called_with(
        msg=_msg)


def mod_args_switch_slots_yes(arg):
    values = {'switch_slots': 'yes'}
    return values[arg]


def mod_args_switch_slots_no(arg):
    values = {'switch_slots': 'no'}
    return values[arg]


@mock.patch('dev_modules.cl_img_install.run_cl_cmd')
@mock.patch('dev_modules.cl_img_install.AnsibleModule')
def test_img_install(mock_module, mock_run_cl_cmd):
    """
    Test install image
    """
    instance = mock_module.return_value
    instance.params.get.side_effect = mod_args
    install_img(instance)
    cmd = '/usr/cumulus/bin/cl-img-install -f %s' % (mod_args('src'))
    mock_run_cl_cmd.assert_called_with(instance, cmd)


@mock.patch('dev_modules.cl_img_install.run_cl_cmd')
@mock.patch('dev_modules.cl_img_install.AnsibleModule')
def test_switch_slots(mock_module, mock_run_cl_cmd):
    """
    Test switching slots
    """
    instance = mock_module.return_value

    instance.params.get.side_effect = mod_args_switch_slots_no
    switch_slots(instance, 1)
    assert_equals(mock_run_cl_cmd.call_count, 0)

    instance.params.get.side_effect = mod_args_switch_slots_yes
    switch_slots(instance, '1')
    runcmd = '/usr/cumulus/bin/cl-img-select 1'
    mock_run_cl_cmd.assert_called_with(instance, runcmd)


@mock.patch('dev_modules.cl_img_install.install_img')
@mock.patch('dev_modules.cl_img_install.check_url')
@mock.patch('dev_modules.cl_img_install.check_sw_version')
@mock.patch('dev_modules.cl_img_install.AnsibleModule')
def test_funcs_called_from_main(mock_module, mock_check_sw,
                                mock_check_url, mock_install_img):
    """
    Test functions called from main
    """
    instance = mock_module.return_value
    instance.params.get.side_effect = mod_args
    main()
    assert_equals(mock_check_url.call_count, 1)
    assert_equals(mock_check_sw.call_count, 1)
    assert_equals(mock_install_img.call_count, 1)
