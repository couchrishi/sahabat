# -*- coding: utf-8 -*-
# Copyright 2024 Google LLC
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
"""
Configuration settings for the Sahabat agent tier.
"""

# --- Model Names ---

# The primary model for the orchestrator agent.
ORCHESTRATOR_MODEL = "gemini-2.5-pro"

# Models for the specialist text agent.
TEXT_FLASH_MODEL = "gemini-2.5-flash"
TEXT_PRO_MODEL = "gemini-2.5-pro"

# Model for the specialist image agent.
IMAGE_MODEL = "gemini-2.5-flash-image-preview"

# Model for the specialist video agent.
VIDEO_MODEL = "veo-3.1-fast-generate-preview"
