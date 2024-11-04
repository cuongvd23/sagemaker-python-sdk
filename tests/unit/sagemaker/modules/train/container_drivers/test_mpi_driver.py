# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
"""MPI Driver Unit Tests."""
from __future__ import absolute_import

import os
import sys

from unittest.mock import patch, MagicMock

sys.modules["utils"] = MagicMock()
sys.modules["mpi_utils"] = MagicMock()

from sagemaker.modules.train.container_drivers import mpi_driver  # noqa: E402


DUMMY_MPI_COMMAND = [
    "mpirun",
    "--host",
    "algo-1,algo-2",
    "-np",
    "2",
    "python",
    "-m",
    "mpi4py",
    "-m",
    "script.py",
]

DUMMY_SOURCE_CODE_CONFIG = {
    "entry_script": "script.py",
    "distribution": {
        "process_count_per_node": 2,
        "sm_distributed_settings": {
            "enable_dataparallel": True,
        },
        "mpi_additional_options": [
            "-x",
            "AWS_REGION",
        ],
    },
}


@patch.dict(
    os.environ,
    {
        "SM_CURRENT_HOST": "algo-2",
        "SM_HOSTS": '["algo-1", "algo-2"]',
        "SM_MASTER_ADDR": "algo-1",
        "SM_HOST_COUNT": "2",
    },
)
@patch("sagemaker.modules.train.container_drivers.mpi_driver.read_source_code_config_json")
@patch("sagemaker.modules.train.container_drivers.mpi_driver.write_env_vars_to_file")
@patch("sagemaker.modules.train.container_drivers.mpi_driver.start_sshd_daemon")
@patch("sagemaker.modules.train.container_drivers.mpi_driver.bootstrap_master_node")
@patch("sagemaker.modules.train.container_drivers.mpi_driver.bootstrap_worker_node")
@patch("sagemaker.modules.train.container_drivers.mpi_driver.get_mpirun_command")
@patch("sagemaker.modules.train.container_drivers.mpi_driver.execute_commands")
def test_mpi_driver_worker(
    mock_execute_commands,
    mock_get_mpirun_command,
    mock_bootstrap_worker_node,
    mock_bootstrap_master_node,
    mock_start_sshd_daemon,
    mock_write_env_vars_to_file,
    mock_read_source_code_config_json,
):
    mock_read_source_code_config_json.return_value = DUMMY_SOURCE_CODE_CONFIG

    mpi_driver.main()

    mock_write_env_vars_to_file.assert_called_once()
    mock_start_sshd_daemon.assert_called_once()
    mock_bootstrap_worker_node.assert_called_once()

    mock_bootstrap_master_node.assert_not_called()
    mock_get_mpirun_command.assert_not_called()
    mock_execute_commands.assert_not_called()


@patch.dict(
    os.environ,
    {
        "SM_CURRENT_HOST": "algo-1",
        "SM_HOSTS": '["algo-1", "algo-2"]',
        "SM_MASTER_ADDR": "algo-1",
        "SM_HOST_COUNT": "2",
    },
)
@patch("sagemaker.modules.train.container_drivers.mpi_driver.read_source_code_config_json")
@patch("sagemaker.modules.train.container_drivers.mpi_driver.write_env_vars_to_file")
@patch("sagemaker.modules.train.container_drivers.mpi_driver.start_sshd_daemon")
@patch("sagemaker.modules.train.container_drivers.mpi_driver.bootstrap_master_node")
@patch("sagemaker.modules.train.container_drivers.mpi_driver.bootstrap_worker_node")
@patch("sagemaker.modules.train.container_drivers.mpi_driver.get_process_count")
@patch("sagemaker.modules.train.container_drivers.mpi_driver.get_mpirun_command")
@patch("sagemaker.modules.train.container_drivers.mpi_driver.execute_commands")
@patch("sagemaker.modules.train.container_drivers.mpi_driver.write_status_file_to_workers")
def test_mpi_driver_master(
    mock_write_status_file_to_workers,
    mock_execute_commands,
    mock_get_mpirun_command,
    mock_get_process_count,
    mock_bootstrap_worker_node,
    mock_bootstrap_master_node,
    mock_start_sshd_daemon,
    mock_write_env_vars_to_file,
    mock_read_source_code_config_json,
):
    mock_read_source_code_config_json.return_value = DUMMY_SOURCE_CODE_CONFIG
    mock_get_mpirun_command.return_value = DUMMY_MPI_COMMAND
    mock_get_process_count.return_value = 2
    mock_execute_commands.return_value = (0, "")

    mpi_driver.main()

    mock_write_env_vars_to_file.assert_called_once()
    mock_start_sshd_daemon.assert_called_once()
    mock_bootstrap_master_node.assert_called_once()
    mock_get_mpirun_command.assert_called_once()
    mock_execute_commands.assert_called_once_with(DUMMY_MPI_COMMAND)
    mock_write_status_file_to_workers.assert_called_once()

    mock_bootstrap_worker_node.assert_not_called()
