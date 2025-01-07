# ide_qr_bot_v0.py

from router import QueryRouter
from helpers import llm_call, extract_file_contents_with_tree, copy_folder_to_docker, check_and_delete_folder
from prompts import (
    conceptual_doubt_prompt,
    get_implementation_guidance_prompt,
    get_test_cases_qr_v0_prompt,
    get_specific_errors_qr_v0_prompt,
    get_publishing_related_query_system_prompt,
    get_ide_related_queries_system_prompt
)
# Removed Agent import if not used

class QRBot:
    def __init__(self, user_query, question_id, zip_path="", question_content="", question_test_cases=""): 
        self.user_query = user_query
        self.question_id = question_id
        self.question_content = question_content
        self.question_test_cases = question_test_cases
        self.query_category = "other"
        self.repo_state = ""
        self.query_router = QueryRouter(query=self.user_query)
        self.zip_path = zip_path
        self.container_id = "09769941a48c"  # **Update or manage dynamically as needed**
        # Removed folder_location as it's no longer needed

    def get_bot_response(self):
        self.query_category = self.query_router.classify_query().strip()
        if self.query_category == "other":
            return "<mentor_required>"
        print(f"Query Category: {self.query_category}")
        check_and_delete_folder("./workspace")
        self._generate_bot_response_based_on_category()
        print(f"Bot Response: {self.bot_response}")
        return self.bot_response
    
    def _generate_bot_response_based_on_category(self):
        if "Test case failures" in self.query_category or \
           "Unexpected output" in self.query_category or \
           "Mistakes Explanation" in self.query_category:
            
            if not self.zip_path:
                self.bot_response = "<please_attach_code_response>"
                return
            
            # Extract and prepare Docker environment
            copy_folder_to_docker(self.container_id, self.zip_path, self.question_id)
            self.repo_state = extract_file_contents_with_tree("./workspace", full_desc=True)
            
            # Prepare issue context
            test_cases = self.question_test_cases
            self.issue_context = (
                f"User Query: {self.query_router.updated_query_context}, "
                f"Repo State: {self.repo_state}, "
                f"Test Cases: {test_cases}"
            )
            self.bot_response = llm_call(get_test_cases_qr_v0_prompt(), self.issue_context)

        elif "Fix specific errors" in self.query_category:
            if not self.zip_path:
                self.bot_response = "<please_attach_code_response>"
                return
            # Extract and prepare Docker environment
            copy_folder_to_docker(self.container_id, self.zip_path, self.question_id)
            self.repo_state = extract_file_contents_with_tree("./workspace")
            self.issue_context = f"Repo State: {self.repo_state}, Issue: {self.query_router.updated_query_context}"
            self.bot_response = llm_call(get_specific_errors_qr_v0_prompt(), self.issue_context)

        elif "Code publishing issue" in self.query_category:
            self.bot_response = llm_call(get_publishing_related_query_system_prompt(),
                                         f"User Query: {self.query_router.updated_query_context}")

        elif "IDE issue" in self.query_category:
            self.bot_response = llm_call(get_ide_related_queries_system_prompt(),
                                         f"User Query: {self.query_router.updated_query_context}")

        elif "Conceptual doubts" in self.query_category:
            self.bot_response = llm_call(conceptual_doubt_prompt(),
                                         f"User Query: {self.query_router.updated_query_context}")

        elif "Problem solving approach" in self.query_category:
            self.bot_response = "<fixed_question_specific_problem_solving_approach>"

        elif "Implementation guidance" in self.query_category:
            if self.zip_path:
                copy_folder_to_docker(self.container_id, self.zip_path, self.question_id)
                self.repo_state = extract_file_contents_with_tree("./workspace", full_desc=True)
                question_context = self.question_content
                self.issue_context = (
                    f"Repo State: {self.repo_state}, "
                    f"Question Context: {question_context}, "
                    f"User Query: {self.query_router.updated_query_context}"
                )
                self.bot_response = llm_call(get_implementation_guidance_prompt(), self.issue_context)
            else:
                self.bot_response = "<please_share_current_code>"
        else:
            self.bot_response = "<mentor_required>"
