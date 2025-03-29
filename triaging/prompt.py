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

