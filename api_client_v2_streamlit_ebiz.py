"""
Client for API v2
"""

import json
import requests
import streamlit as st

from config import RETURN_DATA_AS_MARKDOWN
from utils import get_console_logger

TIMEOUT = 240
API_URL = "http://localhost:8888"
# API_URL = "http://130.61.114.141:8888"
# API_URL = "https://c6fz5ip4c7ru6yndm6pqlgskmq.apigateway.eu-frankfurt-1.oci.customer-oci.com/v2"

# Define the available operations
operations = {
    "chat_with_your_data": "/v2/handle_data_request",
    "get_SQL": "/v2/get_cache_stats",
}

# examples of question on Ebiz schema
sample_questions = [
    "show all the distinct absence types that have been reported by employee",
    "show distinct absence types and the number of employees who reported them in 2017",
    "show all the employees names that have reported absence type name like 'Sick%'.",
    """show all the employee name that have reported absence type like 'Sick%' 
and the total number of hours reported. Order by number of hours descending""",
    """For every department shows the department name, the absence type name 
and total number of hour reported""",
    """show the names of all employees who registered absences started in 2017 
and the total hours for each absence type name""",
    "show all the employee located in US who have reported absences in 2017",
]

logger = get_console_logger()


def abbreviate_question(question, max_length=40):
    """
    Abbreviate the sample question for better presentation in UI
    """
    if len(question) > max_length:
        return question[:max_length] + "..."
    return question


def convert_to_json(response_content):
    """
    to convert to json if the output is not json
    """
    try:
        # Try decoding binary response if it's not already a string
        if isinstance(response_content, bytes):
            decoded_content = response_content.decode("utf-8")
        else:
            decoded_content = str(response_content)

        # Clean up escaped newlines (\\n -> \n) and other escape sequences
        cleaned_content = decoded_content.encode("utf-8").decode("unicode_escape")

        # Convert the decoded string into a JSON structure with a key
        return json.dumps({"generated_sql": cleaned_content}, indent=2)
    except Exception as e:
        st.error(f"Error converting response to JSON: {e}")
        return None


# Add the radio buttons to the sidebar with abbreviated questions
# Create abbreviated versions of the sample questions for the sidebar
abbreviated_questions = [abbreviate_question(q) for q in sample_questions]


def init_session_state():
    if "request_sent" not in st.session_state:
        st.session_state["request_sent"] = False
    if "conv_id" not in st.session_state:
        st.session_state["conv_id"] = ""
    if "user_query" not in st.session_state:
        st.session_state["user_query"] = ""


def reset_conversation():
    conv_id = st.session_state["conv_id"]
    params = {"conv_id": conv_id}
    URL = f"{API_URL}/v2/delete"

    response = requests.delete(URL, params=params, timeout=TIMEOUT)

    if response.status_code == 204:
        st.write("Conversation deleted.")


def main():
    """
    main
    """
    st.set_page_config(
        initial_sidebar_state="collapsed",
    )
    st.title("SQL Agent - Client for API v2.2")

    # to handle the sample questions
    selected_abbreviation = st.sidebar.radio(
        "Choose a question:", abbreviated_questions
    )

    # Find the full question corresponding to the selected abbreviation
    selected_question = sample_questions[
        abbreviated_questions.index(selected_abbreviation)
    ]

    if selected_question:
        st.session_state.user_query = selected_question

    # Initialize session state for request_sent if it doesn't exist
    init_session_state()

    if st.sidebar.button("Reset chat"):
        # clear the conversation
        logger.info("Reset conversation...")
        reset_conversation()

    # Select operation
    selected_operation = st.sidebar.selectbox(
        "Select an API Operation", list(operations.keys())
    )

    if selected_operation in ["chat_with_your_data"]:
        conv_id = st.text_input("Conversation ID", value="42")
        user_query = st.text_area("User Query", st.session_state.user_query)

        # Update session state if inputs change
        if (
            conv_id != st.session_state["conv_id"]
            or user_query != st.session_state["user_query"]
        ):
            st.session_state["conv_id"] = conv_id
            st.session_state["user_query"] = user_query
            st.session_state["request_sent"] = (
                False  # Allow a new request if inputs change
            )

        # remove blank at beginning and end
        user_query = user_query.strip()

        # Create a dictionary for the request body
        request_body = {"conv_id": conv_id, "user_query": user_query}

    # API call
    if st.button("Send Request") and not st.session_state["request_sent"]:
        # Make the API request to the selected operation
        endpoint = API_URL + operations[selected_operation]

        # here we call the api
        with st.spinner():
            if selected_operation == "chat_with_your_data":
                response = requests.post(endpoint, json=request_body, timeout=TIMEOUT)
            else:
                response = requests.get(endpoint, timeout=TIMEOUT)

        # Mark the request as sent to avoid multiple submissions
        st.session_state["request_sent"] = True

        # Display the response
        if response.status_code == 200:
            # If the response is not JSON (like binary/text), convert it to a JSON-like structure
            try:
                json_response = response.json()  # Try to parse JSON directly
            except Exception:
                # If response is not JSON, convert binary/text to JSON manually
                json_response = convert_to_json(response.content)

            if json_response:
                # read the status
                if json_response["status"] == "OK":
                    if json_response["type"] == "data":
                        # display a table with the data
                        if (
                            RETURN_DATA_AS_MARKDOWN
                            and selected_operation == "chat_with_your_data"
                        ):
                            st.write(json_response["content"])
                        else:
                            st.table(json_response["content"])
                    else:
                        # display a report
                        st.write(json_response["content"])
                else:
                    # KO
                    st.error("Error: " + json_response["msg"])

        # Reset the state to allow a new request to be sent
        st.session_state["request_sent"] = False


# Run the app
if __name__ == "__main__":
    main()
