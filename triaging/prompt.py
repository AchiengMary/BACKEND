from langchain.prompts import ChatPromptTemplate

def get_triaging_prompt_template():
    return ChatPromptTemplate.from_messages(
        [
            ("system", "You are a specialized assistant for solar water heating system selection. Your goal is to help qualify customer needs through targeted questions that gather critical information for the sales process."),
            (
                "human",
                """
                Analyze the following user query and generate 5 highly relevant questions to qualify their needs for a solar water heating solution:
                
                User Query: "{user_query}"
                
                TASK:
                Generate 5 specific questions that will help better understand this customer's requirements and constraints. These questions should be carefully tailored to the specific context of their query.
                
                INSTRUCTIONS:
                1. Each question must be unique and directly relevant to what is already mentioned or implied in the user query
                2. Questions should address information gaps in the user query - what hasn't been mentioned but is crucial to know
                3. Focus on technical specifications, implementation requirements, and customer expectations
                4. Format precisely as "Q1: [Question]", "Q2: [Question]", etc.
                5. Each question should be concise (10-15 words) and direct
                
                ESSENTIAL AREAS TO COVER (prioritize based on relevance to the query):
                • System capacity: Daily hot water volume needed, number of users, peak demand periods
                • Installation specifics: Available space, roof type, sun exposure, existing infrastructure
                • Budget parameters: Purchase limits, financing preferences, ROI expectations
                • Technical requirements: Temperature needs, pressure requirements, integration with existing systems
                • Implementation timeline: Installation deadlines, phasing requirements
                • Special considerations: Warranty expectations, maintenance concerns, certification requirements
                
                QUESTION TYPES TO INCLUDE:
                • At least one question about capacity/sizing
                • At least one question about budget
                • At least one question about installation timeline or constraints
                • Remaining questions should address specific technical requirements or integration needs
                
                EXAMPLES OF DIFFERENTIATED QUESTIONS FOR VARIOUS QUERIES:
                
                For general inquiry about options:
                - Focus on determining the scale of need and specific application environment
                - Ask about key decision factors and constraints
                
                For specific capacity requirements:
                - Focus on installation specifics and integration requirements
                - Ask about budget constraints and timeline expectations
                
                For commercial applications:
                - Focus on compliance requirements and maintenance expectations
                - Ask about capacity requirements more precisely (peak loads, usage patterns)
                
                RESPONSE FORMAT:
                Return ONLY the 5 numbered questions, formatted exactly as follows:
                Q1: [First question relevant to user query]
                Q2: [Second question relevant to user query]
                Q3: [Third question relevant to user query]
                Q4: [Fourth question relevant to user query]
                Q5: [Fifth question relevant to user query]
                """
            ),
        ]
    )

# from langchain.prompts import ChatPromptTemplate

# def get_triaging_prompt_template():
#     return ChatPromptTemplate.from_messages(
#         [
#             ("system", "You are a helpful assistant for solar water heating system selection. You assist users by asking relevant questions based on their query to gather details about their needs."),
#             (
#                 "human",
#                 """
#                 Based on the user's inquiry, generate a list of 5 **well-structured** and **relevant** questions to help determine their solar water heating system needs. The questions should be **formatted consistently** as follows:
#                 - Each question should start with "Q1: ", "Q2: ", etc.
#                 - Each question should be short, clear, and directly related to the user's query.
#                 - The questions should cover essential details such as:
#                   - Daily hot water demand
#                   - Available roof space for installation
#                   - Budget for the system
#                   - Preferences for features or technologies
#                   - Timeline for installation

#                 Ensure the following:
#                 - Each question is **numbered sequentially** (Q1, Q2, Q3, Q4, Q5).
#                 - The questions should be **relevant** to the specific needs mentioned in the user's query.
#                 - Do not include additional information or excessive details in the questions; keep them clear and concise.

#                 **Example 1**: User asks, "I'm interested in solar water heating solutions for my residential building. What options do you offer?"
#                 The assistant would generate questions like:
#                 - Q1: What is the approximate daily hot water requirement in liters for your household?
#                 - Q2: Are there any structural constraints regarding the roof space for the installation of the solar heating system?
#                 - Q3: What is your budget range for the solar water heating system and installation?
#                 - Q4: Do you have any specific preferences for brands or technologies in solar heating?
#                 - Q5: What is your timeline for implementing this solar water heating solution?

#                 **Example 2**: User asks, "I need a solar water heating system that can provide enough hot water for 50 people in a residential setting."
#                 The assistant would generate questions like:
#                 - Q1: What is the maximum daily hot water demand in liters per person you expect?
#                 - Q2: Are there any specific constraints on budget or preferred brands?
#                 - Q3: What is the timeline for installation and when do you need the system operational?
#                 - Q4: Do you need any additional features such as remote monitoring or integration with existing systems?
#                 - Q5: What criteria will you use to define the success of this installation?

#                 **Example 3**: User asks, "What options do you have for solar water heating systems that can heat 150 liters per day?"
#                 The assistant would generate questions like:
#                 - Q1: What is your budget for the solar water heating system?
#                 - Q2: Do you have any specific requirements for the installation process?
#                 - Q3: What is your timeline for implementing this solar water heating solution?
#                 - Q4: Are there any existing systems that this new solution must be compatible with?
#                 - Q5: What criteria will determine the success of this installation for you?

#                 **Example 4**: User asks, "Can you provide a quotation for the supply and installation of heat pumps for our project?"
#                 The assistant would generate questions like:
#                 - Q1: What is the required heating capacity for your application?
#                 - Q2: What is your budget for this purchase?
#                 - Q3: What is the timeline for installation?
#                 - Q4: Are there any specific brands or models you prefer?
#                 - Q5: Is there a need for remote monitoring or control features?

#                 Based on the user's input, please generate **5 structured questions** that are relevant to what was asked but try to follow the approach used in the example depending on the type of queston. This need to help the user during the triaging process. Ensure the questions are **relevant** to the user's specific query and follow the **exact format** outlined here: each question should start with "Q1: ", "Q2: ", etc., and the questions should be clear, concise, and directly related to the user’s needs. Strickly only return the question and do not include any additional information or User asks.
#                 """
#             ),
#             ("assistant", "You will now generate the questions based on the user's query."),
#         ]
#     )
