# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import create_artifact_with_sdk_sample

from google.cloud.aiplatform.compat.types import artifact as gca_artifact

import test_constants as constants


def test_create_artifact_with_sdk_sample(mock_artifact, mock_create_artifact):
    artifact = create_artifact_with_sdk_sample.create_artifact_sample(
        project=constants.PROJECT,
        location=constants.LOCATION,
        uri=constants.MODEL_ARTIFACT_URI,
        artifact_id=constants.RESOURCE_ID,
        display_name=constants.DISPLAY_NAME,
        schema_version=constants.SCHEMA_VERSION,
        description=constants.DESCRIPTION,
        metadata=constants.METADATA,
    )

    mock_create_artifact.assert_called_with(
        resource_id=constants.RESOURCE_ID,
        schema_title="system.Artifact",
        uri=constants.MODEL_ARTIFACT_URI,
        display_name=constants.DISPLAY_NAME,
        schema_version=constants.SCHEMA_VERSION,
        description=constants.DESCRIPTION,
        metadata=constants.METADATA,
        state=gca_artifact.Artifact.State.LIVE,
        metadata_store_id="default",
        project=constants.PROJECT,
        location=constants.LOCATION,
        credentials=None,
    )

    assert artifact is mock_artifact
