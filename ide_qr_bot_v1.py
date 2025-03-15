from router import QueryRouter
from helpers import llm_call, download_and_extract_zip,extract_file_contents_with_tree,copy_folder_to_docker,get_question_details
from run_test_cases import run_test_case_script
from prompts import conceptual_doubt_prompt,get_edit_loacalization_task_prompt,get_publishing_related_query_system_prompt,get_ide_related_queries_system_prompt
from agent import Agent


class QRBot:
    def __init__(self,user_query,question_id,code_link = ""): 
        self.user_query = user_query
        self.question_id = question_id
        self.query_category = "other"
        self.repo_state = ""
        self.query_router = QueryRouter(query=self.user_query)
        self.code_link = code_link
 
    def get_bot_response(self):
        self.query_category = self.query_router.classify_query().strip()
        if self.query_category == "other":
            return "<mentor_required>"
        print(self.query_category)
        bot_response = self._generate_bot_response_based_on_category()
        print(bot_response)
        return bot_response
    
    def _generate_bot_response_based_on_category(self):
        
        if self.query_category == "Test case failures" or "Unexpected output":
            if self.code_link == "":
                return "<please_attach_code_response>"
            output_folder = download_and_extract_zip(self.code_link)
            self.repo_state = extract_file_contents_with_tree(output_folder)
            copy_folder_to_docker("5baf109adc77",output_folder,get_question_details(self.question_id,"question_folder_location"))
            test_case_results = run_test_case_script(self.question_id)
            if len(test_case_results['failed'])==0:
                return "<already_correct_code>" 
            print(test_case_results)
            self.issue_context = f"Repo State: {self.repo_state}, Test Case Results: {test_case_results}"

            # generate location of edits based on repo state , issue context and pool of actions and scratchpad based on thoughts sumnmary (refer paper once to see how it would look like)
            self.edit_agent = Agent(task_desc=get_edit_loacalization_task_prompt(),issue=self.query_router.updated_query_context,repo_state=self.repo_state,max_steps=10)
            self.final_edit_thought, self.edit_agent_response = self.edit_agent.execute()


            return "<mentor_required>"
        elif self.query_category.strip() == "Fix specific errors":
            if self.code_link== "":
                return "<please_attach_code_response>"
            output_folder = download_and_extract_zip(self.code_link)
            self.repo_state = extract_file_contents_with_tree(output_folder)
            self.issue_context = f"Repo State: {self.repo_state}, Issue: {self.query_router.updated_query_context}"

            self.edit_agent = Agent(task_desc=get_edit_loacalization_task_prompt(),issue=self.query_router.updated_query_context,repo_state=self.repo_state,max_steps=10)
            self.final_edit_thought, self.edit_agent_response = self.edit_agent.execute()

            self.fixer_agent = Agent(task_desc=get_fixer_prompt(f"Developers thought : {self.final_edit_thought},Developers suggestion to which file to edit : {self.edit_agent_response}"),issue=self.query_router.updated_query_context,repo_state=self.repo_state,max_steps=10)
            self.fixer_agent_response =  self.fixer_agent.execute()

            return self.fixer_agent_response
            

        elif self.query_category == "Code publishing issue":
            result = llm_call(get_publishing_related_query_system_prompt(),f"User Query: {self.query_router.updated_query_context}")
            return result
        elif self.query_category == "IDE issue":
            result = llm_call(get_ide_related_queries_system_prompt(),f"User Query: {self.query_router.updated_query_context}")
            return result
        elif self.query_category == "Conceptual doubts": 
            result = llm_call(conceptual_doubt_prompt(),f"User Query: {self.query_router.updated_query_context}")
            return result
        elif self.query_category == "Problem solving approach": 
            return "<fixed_question_specific_problem_solving_approach>"
        
        else:
            return "<mentor_required>"




