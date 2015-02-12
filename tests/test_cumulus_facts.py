import mock
from nose.tools import set_trace
import dev_modules.cumulus_facts as cl_facts
from asserts import assert_equals


@mock.patch('dev_modules.cumulus_facts.run_cl_cmd')
@mock.patch('dev_modules.cumulus_facts.AnsibleModule')
def test_running_main(mock_module, mock_cl_cmd):
    instance = mock_module.return_value
    mock_cl_cmd.return_value = ['cel,smallstone_xp']
    cl_facts.main()
    assert_equals(mock_cl_cmd.call_count, 1)
    mock_cl_cmd.assert_called_with(instance, '/usr/bin/platform-detect')
    instance.exit_json.assert_called_with(
        msg='Collected Cumulus Linux specific facts',
        ansible_facts={'productname': 'cel,smallstone_xp'})
