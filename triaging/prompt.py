from langchain.prompts import ChatPromptTemplate

def get_triaging_prompt_template():
    return ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant for solar water heating system selection. You assist users by asking relevant questions based on their query to gather details about their needs."),
            (
                "human",
                """
                Based on the user's inquiry, generate a list of 5 **well-structured** and **relevant** questions to help determine their solar water heating system needs. The questions should be **formatted consistently** as follows:
                - Each question should start with "Q1: ", "Q2: ", etc.
                - Each question should be short, clear, and directly related to the user's query.
                - The questions should cover essential details such as:
                  - Daily hot water demand
                  - Available roof space for installation
                  - Budget for the system
                  - Preferences for features or technologies
                  - Timeline for installation

                Ensure the following:
                - Each question is **numbered sequentially** (Q1, Q2, Q3, Q4, Q5).
                - The questions should be **relevant** to the specific needs mentioned in the user's query.
                - Do not include additional information or excessive details in the questions; keep them clear and concise.

                **Example 1**: User asks, "I'm interested in solar water heating solutions for my residential building. What options do you offer?"
                The assistant would generate questions like:
                - Q1: What is the approximate daily hot water requirement in liters for your household?
                - Q2: Are there any structural constraints regarding the roof space for the installation of the solar heating system?
                - Q3: What is your budget range for the solar water heating system and installation?
                - Q4: Do you have any specific preferences for brands or technologies in solar heating?
                - Q5: What is your timeline for implementing this solar water heating solution?

                **Example 2**: User asks, "I need a solar water heating system that can provide enough hot water for 50 people in a residential setting."
                The assistant would generate questions like:
                - Q1: What is the maximum daily hot water demand in liters per person you expect?
                - Q2: Are there any specific constraints on budget or preferred brands?
                - Q3: What is the timeline for installation and when do you need the system operational?
                - Q4: Do you need any additional features such as remote monitoring or integration with existing systems?
                - Q5: What criteria will you use to define the success of this installation?

                **Example 3**: User asks, "What options do you have for solar water heating systems that can heat 150 liters per day?"
                The assistant would generate questions like:
                - Q1: What is your budget for the solar water heating system?
                - Q2: Do you have any specific requirements for the installation process?
                - Q3: What is your timeline for implementing this solar water heating solution?
                - Q4: Are there any existing systems that this new solution must be compatible with?
                - Q5: What criteria will determine the success of this installation for you?

                **Example 4**: User asks, "Can you provide a quotation for the supply and installation of heat pumps for our project?"
                The assistant would generate questions like:
                - Q1: What is the required heating capacity for your application?
                - Q2: What is your budget for this purchase?
                - Q3: What is the timeline for installation?
                - Q4: Are there any specific brands or models you prefer?
                - Q5: Is there a need for remote monitoring or control features?

                Based on the user's input, please generate **5 structured questions** that are relevant to what was asked but try to follow the approach used in the example depending on the type of queston. This need to help the user during the triaging process. Ensure the questions are **relevant** to the user's specific query and follow the **exact format** outlined here: each question should start with "Q1: ", "Q2: ", etc., and the questions should be clear, concise, and directly related to the user’s needs. Strickly only return the question and do not include any additional information or User asks.
                """
            ),
            ("assistant", "You will now generate the questions based on the user's query."),
        ]
    )
