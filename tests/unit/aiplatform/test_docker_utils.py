# -*- coding: utf-8 -*-

# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import pytest
from unittest import mock

from google.cloud.aiplatform.constants import prediction
from google.cloud.aiplatform.docker_utils import run


_TEST_CONTAINER_LOGS = b"line1\nline2\nline3\n"
_TEST_CONTAINER_LOGS_LEN = 3


@pytest.fixture
def docker_client_mock():
    with mock.patch("docker.from_env") as from_env_mock:
        client = from_env_mock.return_value
        client().containers.run.return_value = None
        yield client


@pytest.fixture
def docker_container_mock():
    container = mock.MagicMock()
    container.logs.return_value = _TEST_CONTAINER_LOGS
    return container


class TestRun:
    IMAGE_URI = "test_image:latest"

    def test_run_prediction_container(self, docker_client_mock):
        run.run_prediction_container(self.IMAGE_URI)

        docker_client_mock.containers.run.assert_called_once_with(
            self.IMAGE_URI,
            command=None,
            ports={prediction.DEFAULT_AIP_HTTP_PORT: None},
            environment={
                prediction.AIP_HTTP_PORT: prediction.DEFAULT_AIP_HTTP_PORT,
                prediction.AIP_HEALTH_ROUTE: None,
                prediction.AIP_PREDICT_ROUTE: None,
                prediction.AIP_STORAGE_URI: None,
                run._ADC_ENVIRONMENT_VARIABLE: run._DEFAULT_CONTAINER_CRED_KEY_PATH,
            },
            volumes=[],
            detach=True,
        )

    def test_run_prediction_container_with_all_parameters(
        self, tmp_path, docker_client_mock
    ):
        artifact_uri = "gs://myproject/mymodel"
        serving_container_predict_route = "/custom_predict"
        serving_container_health_route = "/custom_health"
        serving_container_command = ["echo", "hello"]
        serving_container_args = [">", "tmp.log"]
        serving_container_environment_variables = {"custom_key": "custom_value"}
        serving_container_ports = [5555]
        credential_path = tmp_path / "key.json"
        credential_path.write_text("")
        host_port = 6666
        environment = {k: v for k, v in serving_container_environment_variables.items()}
        environment[prediction.AIP_HTTP_PORT] = serving_container_ports[0]
        environment[prediction.AIP_HEALTH_ROUTE] = serving_container_health_route
        environment[prediction.AIP_PREDICT_ROUTE] = serving_container_predict_route
        environment[prediction.AIP_STORAGE_URI] = artifact_uri
        environment[
            run._ADC_ENVIRONMENT_VARIABLE
        ] = run._DEFAULT_CONTAINER_CRED_KEY_PATH
        volumes = [f"{credential_path}:{run._DEFAULT_CONTAINER_CRED_KEY_PATH}"]

        run.run_prediction_container(
            self.IMAGE_URI,
            artifact_uri=artifact_uri,
            serving_container_predict_route=serving_container_predict_route,
            serving_container_health_route=serving_container_health_route,
            serving_container_command=serving_container_command,
            serving_container_args=serving_container_args,
            serving_container_environment_variables=serving_container_environment_variables,
            serving_container_ports=serving_container_ports,
            credential_path=credential_path,
            host_port=host_port,
        )

        docker_client_mock.containers.run.assert_called_once_with(
            self.IMAGE_URI,
            command=serving_container_command + serving_container_args,
            ports={serving_container_ports[0]: host_port},
            environment=environment,
            volumes=volumes,
            detach=True,
        )

    def test_run_prediction_container_artifact_uri_is_not_gcs(self, docker_client_mock):
        artifact_uri = "./models"
        expected_message = (
            f'artifact_uri must be a GCS path but it is "{artifact_uri}".'
        )

        with pytest.raises(ValueError) as exception:
            run.run_prediction_container(self.IMAGE_URI, artifact_uri=artifact_uri)

        assert str(exception.value) == expected_message

    def test_run_prediction_container_credential_path_not_exists(
        self, docker_client_mock
    ):
        credential_path = "key.json"
        expected_message = f'credential_path does not exist: "{credential_path}".'

        with pytest.raises(ValueError) as exception:
            run.run_prediction_container(
                self.IMAGE_URI, credential_path=credential_path
            )

        assert str(exception.value) == expected_message

    @mock.patch.dict(os.environ, {run._ADC_ENVIRONMENT_VARIABLE: "key.json"})
    def test_run_prediction_container_adc_value_not_exists(self, docker_client_mock):
        expected_message = (
            f"The file from the environment variable {run._ADC_ENVIRONMENT_VARIABLE} does "
            f'not exist: "key.json".'
        )

        with pytest.raises(ValueError) as exception:
            run.run_prediction_container(self.IMAGE_URI)

        assert str(exception.value) == expected_message

    def test_print_container_logs(self, docker_container_mock):
        with mock.patch(
            "google.cloud.aiplatform.docker_utils.run._logger"
        ) as logger_mock:
            logs_len = run.print_container_logs(docker_container_mock)

        assert logs_len == _TEST_CONTAINER_LOGS_LEN
        assert docker_container_mock.logs.called
        assert logger_mock.info.call_count == _TEST_CONTAINER_LOGS_LEN

    def test_print_container_logs_with_start_index(self, docker_container_mock):
        start_index = 1
        with mock.patch(
            "google.cloud.aiplatform.docker_utils.run._logger"
        ) as logger_mock:
            logs_len = run.print_container_logs(
                docker_container_mock, start_index=start_index
            )

        assert logs_len == _TEST_CONTAINER_LOGS_LEN
        assert docker_container_mock.logs.called
        assert logger_mock.info.call_count == (_TEST_CONTAINER_LOGS_LEN - start_index)
