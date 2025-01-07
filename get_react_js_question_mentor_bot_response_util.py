# ruff: noqa
# pylint: skip-file
import json
import logging
from typing import List, Dict, Any

from nkb_discussions.constants.enums import BotTypeEnum
from nkb_discussions_integrations.adapters.dtos import BotConfigDTO
from mentor_bot_prompts_config import \
    QUERY_CLASSIFICATION_PROMPT, TEST_CASES_QR_V00_PROMPT, \
    SPECIFIC_ERRORS_QR_V0_PROMPT, PUBLISHING_RELATED_QUERY_SYSTEM_PROMPT, \
    IDE_RELATED_QUERIES_SYSTEM_PROMPT, CONCEPTUAL_DOUBT_PROMPT, \
    IMPLEMENTATION_GUIDANCE_PROMPT, DEFAULT_RESPONSE

logger = logging.getLogger(__name__)

class GetAIResponseForReactJsQuestionUtil:
    def __init__(self, user_query, file_url):
        self.user_query = user_query
        self.query_category = "other"
        self.repo_state = ""
        self.query_router = QueryRouter(query=self.user_query)
        self.file_url = file_url

    def get_bot_response(self, bot_config_dto: BotConfigDTO,
            prompt_vars_dto: PromptVarsDTO) -> str:
        is_user_feature_flag_enabled = \
            self._get_is_user_feature_flag_enabled(
                prompt_vars_dto, bot_config_dto)

        if not is_user_feature_flag_enabled:
            return ""
        self.query_category = self.query_router.classify_query(
            bot_config_dto, prompt_vars_dto).strip()
        if self.query_category == "other":
            return DEFAULT_RESPONSE
        self._generate_bot_response_based_on_category(
            bot_config_dto, prompt_vars_dto)
        return self.bot_response

    def _generate_bot_response_based_on_category(
            self, bot_config_dto: BotConfigDTO,
            prompt_vars_dto: PromptVarsDTO):

        if ("Test case failures" in self.query_category or
                "Unexpected output" in self.query_category or
                "Mistakes Explanation" in self.query_category):
            self.repo_state = self._get_user_code_from_zip_file(bot_config_dto)
            self.issue_context = f"User Query: {self.repo_state}"
            prompt = TEST_CASES_QR_V00_PROMPT
            self.bot_response = get_ai_response(
                prompt, self.issue_context, bot_config_dto, prompt_vars_dto)

        elif "Fix specific errors" in self.query_category.strip():
            self.repo_state = self._get_user_code_from_zip_file(bot_config_dto)
            self.issue_context = \
                (f"Repo State: {self.repo_state}, Issue: "
                 f"{self.query_router.updated_query_context}")
            prompt = SPECIFIC_ERRORS_QR_V0_PROMPT
            self.bot_response = get_ai_response(
                prompt, self.issue_context, bot_config_dto, prompt_vars_dto)

        elif "Code publishing issue" in self.query_category:
            prompt = PUBLISHING_RELATED_QUERY_SYSTEM_PROMPT
            self.bot_response = get_ai_response(
                prompt,
                f"User Query: {self.query_router.updated_query_context}",
                bot_config_dto, prompt_vars_dto)
        elif "IDE issue" in self.query_category:
            prompt = IDE_RELATED_QUERIES_SYSTEM_PROMPT
            self.bot_response = get_ai_response(
                prompt,
                f"User Query: {self.query_router.updated_query_context}",
                bot_config_dto, prompt_vars_dto)
        elif "Conceptual doubts" in self.query_category:
            prompt = CONCEPTUAL_DOUBT_PROMPT
            self.bot_response = get_ai_response(
                prompt,
                f"User Query: {self.query_router.updated_query_context}",
                bot_config_dto, prompt_vars_dto)
        elif "Implementation guidance" in self.query_category:
            question_details = bot_config_dto.content
            self.repo_state = self._get_user_code_from_zip_file(bot_config_dto)
            prompt = IMPLEMENTATION_GUIDANCE_PROMPT
            user_prompt = \
                (f"Repo State: {self.repo_state}, Question Context: "
                 f"{question_details},User Query: "
                 f"{self.query_router.updated_query_context}")
            self.bot_response = get_ai_response(
                prompt, user_prompt, bot_config_dto, prompt_vars_dto)
        else:
            self.bot_response = DEFAULT_RESPONSE

    def _get_is_user_feature_flag_enabled(
            self, prompt_vars_dto: PromptVarsDTO, bot_config_dto: BotConfigDTO
    ) -> bool:

        bot_metadata = bot_config_dto.metadata

        cloud_ide_question_config = \
            bot_metadata.get("cloud_ide_question_config", {})

        if not cloud_ide_question_config:
            return False

        should_check_user_feature_flags = \
            cloud_ide_question_config.get("should_check_user_feature_flags")

        if not should_check_user_feature_flags:
            return True


        user_id = prompt_vars_dto.user_id
        feature_flags_to_consider = \
            cloud_ide_question_config.get("feature_flags_to_consider", [])
        is_feature_flags_enabled = \
            self._is_feature_flags_enabled_for_user(
                user_id, feature_flags_to_consider)
        return is_feature_flags_enabled

    # @staticmethod
    # def _is_feature_flags_enabled_for_user(
    #         user_id: str, feature_flags_to_consider: List[str]) -> bool:
    #     from nkb_discussions_integrations.adapters.service_adapter import \
    #         get_service_adapter
    #     adapter = get_service_adapter()
    #     user_feature_flags = \
    #         adapter.auth.get_user_feature_flags(user_id)

    #     is_feature_flags_enabled = True
    #     for each in feature_flags_to_consider:
    #         if not user_feature_flags.get(each):
    #             is_feature_flags_enabled = False
    #             break

    #     return is_feature_flags_enabled

    def _get_user_code_from_zip_file(
            self, bot_config_dto: BotConfigDTO) -> str:

        import requests
        import zipfile
        from io import BytesIO

        response = requests.get(self.file_url, timeout=10)
        zip_file = zipfile.ZipFile(BytesIO(response.content)) # pylint: disable=consider-using-with

        metadata = bot_config_dto.metadata
        regex_exclude_file_paths = metadata.get("regex_exclude_file_paths", [])
        folder_structure = self._get_folder_structure_from_zip(
            zip_file, regex_exclude_file_paths)

        folder_structure_line_strs = \
            self._get_folder_structure_line_strs(folder_structure, [])

        folder_structure_str = "\n".join(folder_structure_line_strs)

        user_code = f"This is the Directory tree \n{folder_structure_str}\n"

        files_content = self._get_files_content_from_zip_file(
            zip_file, regex_exclude_file_paths)

        user_code += "\n".join(files_content)

        return user_code

    @staticmethod
    def _get_folder_structure_from_zip(  # noqa: C901
            zip_file: Any, regex_exclude_file_paths: List[str],
    ) -> Dict[str, Any]:

        folder_structure = {}
        import re
        for file_path in zip_file.namelist():
            path_parts = file_path.split('/')
            current = folder_structure

            if any(re.match(pattern, file_path) for pattern in
                   regex_exclude_file_paths):
                continue

            for part in path_parts[:-1]:
                if part not in current:
                    current[part] = {'dirs': [],
                                     'files': []}
                current = current[part]

            if file_path.endswith('/'):
                if path_parts[-1] and path_parts[-1] not in current:
                    current[path_parts[-1]] = {'dirs': [], 'files': []}
            else:
                file_name = path_parts[-1]
                if 'files' not in current:
                    current['files'] = []
                current['files'].append(file_name)

            current = folder_structure
            for part in path_parts[:-1]:
                if 'dirs' not in current:
                    current['dirs'] = []
                if part not in current['dirs']:
                    current['dirs'].append(part)
                current = current[part]

        return folder_structure

    def _get_folder_structure_line_strs(
            self, structure: Dict[str, Any], line_strs: List[str], prefix="",
    ) -> List[str]:
        dir_keys = sorted(structure["dirs"]) if "dirs" in structure else []

        file_list = sorted(structure["files"]) if "files" in structure else []

        keys = dir_keys + file_list
        total_keys = len(keys)

        for index, key in enumerate(keys):
            is_last_item = index == (total_keys - 1)

            if is_last_item:
                current_prefix = prefix + "└── "
                next_prefix = prefix + "    "
            else:
                current_prefix = prefix + "├── "
                next_prefix = prefix + "│   "

            if key in dir_keys:
                line_strs.append(f"{current_prefix}[DIR] {key}")
                next_structure = structure[key] if key in structure else {}
                self._get_folder_structure_line_strs(
                    next_structure, line_strs, next_prefix)
            elif key in file_list:
                line_strs.append(f"{current_prefix}[FILE] {key}")

        return line_strs

    @staticmethod
    def _get_files_content_from_zip_file(
            zip_file: Any, regex_exclude_file_paths: List[str]) -> List[str]:

        file_contents = ["\n\nFile contents: "]
        import re
        for file_path in zip_file.namelist():
            if file_path.endswith('/'):
                continue

            if any(re.match(pattern, file_path) for pattern in
                   regex_exclude_file_paths):
                continue

            with zip_file.open(file_path) as file:
                try:
                    content = file.read().decode('utf-8')
                except UnicodeDecodeError:
                    content = str(file.read())

            file_contents.append(f"\n\n{file_path}\n```\n{content}\n```")

        return file_contents


class QueryRouter:
    def __init__(self, query):
        self.query = query
        self.query_text = ""
        self.updated_query_context = ""

    def classify_query(self, bot_config_dto, prompt_vars_dto):
        self.query_text = "Processed text from query: " + self.query
        prompt = QUERY_CLASSIFICATION_PROMPT
        result = get_ai_response(
            prompt, self.query_text, bot_config_dto, prompt_vars_dto)

        res_json = json.loads(
            result.replace("```json", "").replace("```", ""))
        if "error_description" in res_json and \
                res_json['error_description'] != "":
            self.updated_query_context = \
                (f"Query Summary: {res_json['user_query_summary']}, "
                 f"Error Description: {res_json['error_description']}")
        else:
            self.updated_query_context = \
                f"Query Summary: {res_json['user_query_summary']}"
        return res_json['query_category']


def get_ai_response(
        system_prompt: str, user_prompt: str,
        bot_config_dto: BotConfigDTO, prompt_vars_dto: PromptVarsDTO):

    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}]

    timeout_in_secs = 240
    retry_attempts_count = 0
    bot_type = BotTypeEnum.mentor_bot.value

    service_enum = bot_config_dto.service_enum
    if not service_enum:
        service_enum = MENTOR_BOT_DEFAULT_SERVICE_ENUM
    _, model_name = service_enum.split("/")

    discussion_id = prompt_vars_dto.discussion_id \
        if prompt_vars_dto else None

    entity_id = prompt_vars_dto.entity_id \
        if prompt_vars_dto else None

    interactor = AiServiceBaseImplementation()
    service_util = \
        interactor.get_ai_service_util_based_on_service_enum(service_enum)
    response = \
        service_util.get_ai_response(
            messages, model_name, timeout_in_secs, bot_type,
            retry_attempts_count, discussion_id, entity_id)
    choices = response.get("choices", [])
    response = choices[0].get('message', {}).get('content') \
        if choices else ""

    return response
